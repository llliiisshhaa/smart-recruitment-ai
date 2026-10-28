"""
Application and Recruiter Review routes.
Provides candidate application status tracking, recruiter applicant dossier inspection,
resume downloading, and recruiter evaluation reviews.
"""

from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.database import get_db
from app.models.audit import AuditLog
from app.models.job import Application, Job, RecruiterReview
from app.models.resume import Resume
from app.models.user import User
from app.schemas.applications import (
    ApplicantDetailResponse,
    CandidateApplicationItem,
    ResumeMetaResponse,
    ReviewCreate,
    ReviewResponse,
)

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.get("/mine", response_model=List[CandidateApplicationItem])
def get_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("candidate")),
) -> List[CandidateApplicationItem]:
    """
    List all applications submitted by the authenticated candidate.
    Ordered deterministically by application date.
    """
    applications = (
        db.query(Application)
        .join(Job, Application.job_id == Job.id)
        .filter(Application.candidate_id == current_user.id)
        .order_by(Application.created_at.desc(), Application.id.desc())
        .all()
    )

    items: List[CandidateApplicationItem] = []
    for app in applications:
        items.append(
            CandidateApplicationItem(
                id=app.id,
                job_id=app.job_id,
                job_title=app.job.title if app.job else "Unknown Job",
                job_status=app.job.status if app.job else "closed",
                status=app.status,
                created_at=app.created_at,
            )
        )

    return items


@router.get("/{application_id}", response_model=ApplicantDetailResponse)
def get_applicant_detail(
    application_id: int,
    reveal_contact: bool = Query(default=False, description="Flag to reveal candidate contact details"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("recruiter")),
) -> ApplicantDetailResponse:
    """
    Inspect applicant profile and evaluation dossier for a job owned by the recruiter.
    Enforces ownership via a single database query.
    Protects candidate privacy: contact information is hidden by default.
    """
    app_record = (
        db.query(Application)
        .join(Job, Application.job_id == Job.id)
        .filter(
            Application.id == application_id,
            Job.recruiter_id == current_user.id,
        )
        .first()
    )

    if app_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    candidate = app_record.candidate
    candidate_profile = candidate.candidate_profile if candidate else None

    # Determine contact visibility
    email = None
    phone = None
    if reveal_contact and candidate:
        email = candidate.email
        phone = candidate_profile.phone if candidate_profile else None

        # Record contact reveal audit event (without logging sensitive contact values)
        audit = AuditLog(
            user_id=current_user.id,
            action="CONTACT_REVEALED",
            entity_type="Application",
            entity_id=app_record.id,
            details={"candidate_id": candidate.id},
        )
        db.add(audit)
        db.commit()

    # Resume metadata (never expose file_path or raw_text)
    resume_meta = None
    if app_record.resume:
        resume_obj = app_record.resume
        extracted_skills = None
        if resume_obj.resume_skills:
            extracted_skills = [
                rs.skill.name for rs in resume_obj.resume_skills if rs.skill
            ]

        resume_meta = ResumeMetaResponse(
            id=resume_obj.id,
            original_filename=resume_obj.original_filename,
            parse_status=resume_obj.parse_status,
            created_at=resume_obj.created_at,
            parsed_json=resume_obj.parsed_json,
            extracted_skills=extracted_skills,
        )

    # Chronologically ordered reviews
    reviews_records = (
        db.query(RecruiterReview)
        .filter(RecruiterReview.application_id == app_record.id)
        .order_by(RecruiterReview.created_at.asc(), RecruiterReview.id.asc())
        .all()
    )

    review_items = [
        ReviewResponse(
            id=r.id,
            application_id=r.application_id,
            recruiter_id=r.recruiter_id,
            decision=r.decision,
            notes=r.notes,
            created_at=r.created_at,
        )
        for r in reviews_records
    ]

    return ApplicantDetailResponse(
        id=app_record.id,
        candidate_id=app_record.candidate_id,
        job_id=app_record.job_id,
        status=app_record.status,
        created_at=app_record.created_at,
        candidate_name=candidate.full_name if candidate else "Unknown",
        headline=candidate_profile.headline if candidate_profile else None,
        location=candidate_profile.location if candidate_profile else None,
        email=email,
        phone=phone,
        resume=resume_meta,
        reviews=review_items,
    )


@router.get("/{application_id}/resume")
def download_applicant_resume(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("recruiter")),
):
    """
    Download applicant resume file for a job owned by the recruiter.
    Verifies ownership at query time and serves file securely.
    """
    app_record = (
        db.query(Application)
        .join(Job, Application.job_id == Job.id)
        .filter(
            Application.id == application_id,
            Job.recruiter_id == current_user.id,
        )
        .first()
    )

    if app_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    if app_record.resume_id is None or app_record.resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not associated with this application.",
        )

    resume = app_record.resume
    if resume.candidate_id != app_record.candidate_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume candidate mismatch.",
        )

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

    audit = AuditLog(
        user_id=current_user.id,
        action="RESUME_VIEWED_BY_RECRUITER",
        entity_type="Resume",
        entity_id=resume.id,
        details={"application_id": app_record.id},
    )
    db.add(audit)
    db.commit()

    return FileResponse(
        path=stored_path,
        media_type=media_type,
        filename=resume.original_filename,
    )


@router.post(
    "/{application_id}/review",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_recruiter_review(
    application_id: int,
    review_in: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("recruiter")),
) -> ReviewResponse:
    """
    Submit a human recruiter evaluation decision on an application.
    Updates application status to 'reviewed' and preserves review history.
    """
    app_record = (
        db.query(Application)
        .join(Job, Application.job_id == Job.id)
        .filter(
            Application.id == application_id,
            Job.recruiter_id == current_user.id,
        )
        .first()
    )

    if app_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    review = RecruiterReview(
        application_id=app_record.id,
        recruiter_id=current_user.id,
        decision=review_in.decision,
        notes=review_in.notes,
    )
    db.add(review)

    # Set application status to reviewed
    app_record.status = "reviewed"

    audit = AuditLog(
        user_id=current_user.id,
        action="REVIEW_SUBMITTED",
        entity_type="Application",
        entity_id=app_record.id,
        details={"decision": review_in.decision},
    )
    db.add(audit)

    try:
        db.commit()
        db.refresh(review)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not submit review decision.",
        )

    return ReviewResponse(
        id=review.id,
        application_id=review.application_id,
        recruiter_id=review.recruiter_id,
        decision=review.decision,
        notes=review.notes,
        created_at=review.created_at,
    )
