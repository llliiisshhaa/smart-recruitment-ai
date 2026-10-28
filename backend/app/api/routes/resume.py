from io import BytesIO
from pathlib import Path
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

from app.config import settings
from app.core.dependencies import require_roles
from app.database import get_db
from app.models.audit import AuditLog
from app.models.resume import Resume
from app.models.user import CandidateProfile, User
from app.schemas.resume import ResumeListItem, ResumeResponse


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
        # The database record has already been deleted.
        # A leftover file can be cleaned up separately.
        pass

    return None