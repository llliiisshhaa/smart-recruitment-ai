from io import BytesIO
from pathlib import Path
from typing import List, Optional
from uuid import uuid4
import zipfile

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.ai.services.resume_parser import ResumeParserError, parse_resume
from app.config import settings
from app.core.dependencies import require_roles
from app.database import get_db
from app.models.audit import AuditLog
from app.models.job import Application
from app.models.resume import Resume, ResumeSkill, Skill
from app.models.user import CandidateProfile, User
from app.schemas.resume import (
    ExtractedSkillItem,
    ParsedResumeResponse,
    ResumeListItem,
    ResumeResponse,
)


router = APIRouter(prefix="/resumes", tags=["Resumes"])

MAX_RESUMES_PER_CANDIDATE = 5
CHUNK_SIZE = 1024 * 1024

ALLOWED_CONTENT_TYPES = {
    ".pdf": {
        "application/pdf",
        "application/octet-stream",
    },
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    },
}


def get_owned_resume(
    db: Session,
    resume_id: int,
    candidate_id: int,
) -> Resume:
    """Return a resume only if it belongs to the current candidate."""

    resume = (
        db.query(Resume)
        .filter(
            Resume.id == resume_id,
            Resume.candidate_id == candidate_id,
        )
        .first()
    )

    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    return resume


def validate_resume_content(
    content: bytes,
    extension: str,
) -> None:
    """Validate the actual file signature and, for DOCX, ZIP structure."""

    if extension == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is not a valid PDF.",
            )

    elif extension == ".docx":
        if not content.startswith(b"PK"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is not a valid DOCX.",
            )

        try:
            with zipfile.ZipFile(BytesIO(content)) as archive:
                if "word/document.xml" not in archive.namelist():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="The DOCX file does not contain a Word document.",
                    )

                if archive.testzip() is not None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="The DOCX file is corrupted.",
                    )

        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded DOCX file is corrupted or invalid.",
            )


@router.post(
    "",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("candidate")),
):
    """Upload a PDF or DOCX resume after consent has been given."""

    # 1. Verify candidate consent.
    profile = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )

    if profile is None or profile.consent_given_at is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please provide consent before uploading a resume.",
        )

    # 2. Validate the filename and extension.
    if not file.filename or not file.filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A filename is required.",
        )

    # Handle both Windows and Unix-style path separators.
    original_filename = file.filename.replace("\\", "/").split("/")[-1]

    if not original_filename or original_filename in {".", ".."}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename.",
        )

    original_filename = original_filename[:255]
    extension = Path(original_filename).suffix.lower()

    if extension not in {".pdf", ".docx"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are allowed.",
        )

    # 3. Check the declared content type.
    content_type = (file.content_type or "").lower()

    if content_type not in ALLOWED_CONTENT_TYPES[extension]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The file content type does not match the permitted format.",
        )

    # 4. Enforce the maximum file size while reading.
    max_size = settings.MAX_UPLOAD_MB * 1024 * 1024
    chunks = []
    total_size = 0

    try:
        while True:
            chunk = await file.read(CHUNK_SIZE)

            if not chunk:
                break

            total_size += len(chunk)

            if total_size > max_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds the {settings.MAX_UPLOAD_MB} MB limit.",
                )

            chunks.append(chunk)

    finally:
        await file.close()

    if total_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    content = b"".join(chunks)

    # 5. Validate the actual file contents.
    validate_resume_content(content, extension)

    # 6. Enforce the candidate's resume limit.
    resume_count = (
        db.query(Resume)
        .filter(Resume.candidate_id == current_user.id)
        .count()
    )

    if resume_count >= MAX_RESUMES_PER_CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can upload a maximum of 5 resumes.",
        )

    # 7. Generate a server-controlled storage path.
    upload_root = Path(settings.UPLOAD_DIR).expanduser()
    candidate_directory = upload_root / str(current_user.id)
    stored_filename = f"{uuid4().hex}{extension}"
    stored_path = candidate_directory / stored_filename

    try:
        candidate_directory.mkdir(parents=True, exist_ok=True)
        stored_path.write_bytes(content)

    except OSError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not store the uploaded file.",
        )

    # 8. Create the database record and audit event.
    resume = Resume(
        candidate_id=current_user.id,
        file_path=str(stored_path),
        original_filename=original_filename,
        parse_status="pending",
    )

    try:
        db.add(resume)
        db.flush()

        audit_log = AuditLog(
            user_id=current_user.id,
            action="RESUME_UPLOADED",
            entity_type="Resume",
            entity_id=resume.id,
            details={
                "original_filename": original_filename,
                "parse_status": "pending",
            },
        )

        db.add(audit_log)
        db.commit()
        db.refresh(resume)

    except Exception:
        db.rollback()

        try:
            stored_path.unlink(missing_ok=True)
        except OSError:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the resume record.",
        )

    return resume


@router.get("", response_model=list[ResumeListItem])
def list_my_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("candidate")),
):
    """List only the current candidate's resumes."""

    return (
        db.query(Resume)
        .filter(Resume.candidate_id == current_user.id)
        .order_by(Resume.created_at.desc())
        .all()
    )


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_my_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("candidate")),
):
    """Get details of a resume owned by the current candidate."""

    return get_owned_resume(db, resume_id, current_user.id)


@router.get("/{resume_id}/download")
def download_my_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("candidate")),
):
    """Download a resume only if it belongs to the current candidate."""

    resume = get_owned_resume(db, resume_id, current_user.id)
    stored_path = Path(resume.file_path)

    if not stored_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The stored resume file could not be found.",
        )

    if stored_path.suffix.lower() == ".pdf":
        media_type = "application/pdf"
    else:
        media_type = (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )

    return FileResponse(
        path=stored_path,
        media_type=media_type,
        filename=resume.original_filename,
    )


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("candidate")),
):
    """Delete an owned resume, its database record, and its stored file."""

    resume = get_owned_resume(db, resume_id, current_user.id)
    stored_path = Path(resume.file_path)

    # Check whether the resume is associated with any job application
    has_applications = (
        db.query(Application.id)
        .filter(Application.resume_id == resume.id)
        .first()
        is not None
    )
    if has_applications:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This resume is attached to an application and cannot be deleted.",
        )

    audit_log = AuditLog(
        user_id=current_user.id,
        action="RESUME_DELETED",
        entity_type="Resume",
        entity_id=resume.id,
        details={
            "original_filename": resume.original_filename,
        },
    )

    try:
        db.add(audit_log)
        db.delete(resume)
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete the resume record.",
        )

    # Delete the physical file after the database transaction succeeds.
    # Missing files are acceptable.
    try:
        stored_path.unlink(missing_ok=True)
    except OSError:
        pass

    return None


@router.post(
    "/{resume_id}/parse",
    response_model=ParsedResumeResponse,
    status_code=status.HTTP_200_OK,
)
def parse_my_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("candidate")),
):
    """
    Parse an owned resume document into structured data and extract skills.
    Idempotent: replaces previous ResumeSkill associations and updates parse status.
    """
    resume = get_owned_resume(db, resume_id, current_user.id)
    stored_path = Path(resume.file_path)

    # Validate file existence before parsing
    if not stored_path.is_file():
        # Persist failure status safely
        error_msg = "The stored resume file could not be found."
        resume.parse_status = "failed"
        resume.parsed_json = {"meta": {"error": error_msg}}
        audit_fail = AuditLog(
            user_id=current_user.id,
            action="RESUME_PARSE_FAILED",
            entity_type="Resume",
            entity_id=resume.id,
            details={"error": error_msg},
        )
        try:
            db.add(resume)
            db.add(audit_fail)
            db.commit()
        except Exception:
            db.rollback()

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg,
        )

    # Load canonical skills from database taxonomy
    canonical_skills = [s[0] for s in db.query(Skill.name).all()]

    try:
        parsed_data = parse_resume(stored_path, canonical_skills=canonical_skills)
        raw_text = parsed_data.pop("_raw_text", "")
    except (ResumeParserError, Exception) as exc:
        db.rollback()

        # Sanitize error message to avoid exposing server file paths or tracebacks
        error_msg = str(exc)
        if resume.file_path in error_msg:
            error_msg = error_msg.replace(resume.file_path, resume.original_filename)
        # Ensure standard wording for no-text errors is preserved
        if "no extractable text" not in error_msg.lower() and not any(
            w in error_msg.lower() for w in ["limit", "corrupt", "unsupported", "exceeds"]
        ):
            error_msg = "The resume file could not be parsed: corrupted or invalid."

        resume.parse_status = "failed"
        resume.parsed_json = {"meta": {"error": error_msg}}
        audit_fail = AuditLog(
            user_id=current_user.id,
            action="RESUME_PARSE_FAILED",
            entity_type="Resume",
            entity_id=resume.id,
            details={"error": error_msg},
        )
        try:
            db.add(resume)
            db.add(audit_fail)
            db.commit()
        except Exception:
            db.rollback()

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg,
        )

    # Persist parsed results transactionally
    try:
        resume.raw_text = raw_text
        resume.parsed_json = parsed_data
        resume.parse_status = "parsed"

        # 1. Clear any prior skill associations idempotently
        db.query(ResumeSkill).filter(ResumeSkill.resume_id == resume.id).delete()

        # 2. Add newly extracted skills matched against the database taxonomy
        skills_response_items: List[ExtractedSkillItem] = []
        extracted_skills = parsed_data.get("skills", [])

        extracted_names = [s["name"].lower() for s in extracted_skills if isinstance(s, dict) and "name" in s]
        db_skills = db.query(Skill).filter(Skill.name.in_(extracted_names)).all()
        db_skills_map = {s.name: s for s in db_skills}

        seen_skill_ids = set()
        for s_data in extracted_skills:
            if not isinstance(s_data, dict) or "name" not in s_data:
                continue

            s_name = s_data["name"].lower()
            db_skill = db_skills_map.get(s_name)

            if db_skill and db_skill.id not in seen_skill_ids:
                seen_skill_ids.add(db_skill.id)
                evidence = s_data.get("evidence_text")
                resume_skill = ResumeSkill(
                    resume_id=resume.id,
                    skill_id=db_skill.id,
                    evidence_text=evidence,
                )
                db.add(resume_skill)
                skills_response_items.append(
                    ExtractedSkillItem(
                        name=db_skill.name,
                        category=db_skill.category,
                        evidence_text=evidence,
                        supported_by_context=s_data.get("supported_by_context"),
                    )
                )

        audit_success = AuditLog(
            user_id=current_user.id,
            action="RESUME_PARSED",
            entity_type="Resume",
            entity_id=resume.id,
            details={
                "original_filename": resume.original_filename,
                "skills_count": len(skills_response_items),
            },
        )
        db.add(audit_success)
        db.commit()
        db.refresh(resume)

        return ParsedResumeResponse(
            id=resume.id,
            candidate_id=resume.candidate_id,
            original_filename=resume.original_filename,
            parse_status=resume.parse_status,
            parsed_json=resume.parsed_json,
            skills=skills_response_items,
            created_at=resume.created_at,
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist parsed resume records.",
        )


@router.get(
    "/{resume_id}/parsed",
    response_model=ParsedResumeResponse,
    status_code=status.HTTP_200_OK,
)
def get_parsed_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("candidate")),
):
    """
    Retrieve structured parsed results and extracted skills for an owned resume.
    """
    resume = get_owned_resume(db, resume_id, current_user.id)

    skills_items: List[ExtractedSkillItem] = []
    context_map = {}
    if isinstance(resume.parsed_json, dict):
        for sk in resume.parsed_json.get("skills", []):
            if isinstance(sk, dict) and "name" in sk:
                context_map[sk["name"].lower()] = sk.get("supported_by_context")

    for rs in resume.resume_skills:
        if rs.skill:
            skills_items.append(
                ExtractedSkillItem(
                    name=rs.skill.name,
                    category=rs.skill.category,
                    evidence_text=rs.evidence_text,
                    supported_by_context=context_map.get(rs.skill.name.lower()),
                )
            )

    return ParsedResumeResponse(
        id=resume.id,
        candidate_id=resume.candidate_id,
        original_filename=resume.original_filename,
        parse_status=resume.parse_status,
        parsed_json=resume.parsed_json,
        skills=skills_items,
        created_at=resume.created_at,
    )
