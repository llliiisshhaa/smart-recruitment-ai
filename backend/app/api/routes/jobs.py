"""
Job management and browsing routes.
Includes recruiter job creation/updating, candidate job searching, application submission,
and recruiter applicant listing.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models.audit import AuditLog
from app.models.job import Application, Job, JobSkill, RecruiterReview
from app.models.resume import Resume
from app.models.user import CandidateProfile, User
from app.schemas.applications import (
    ApplicantSummaryItem,
    ApplicationCreate,
    CandidateApplicationItem,
)
from app.schemas.jobs import (
    JobCreate,
    JobResponse,
    JobStatusUpdate,
    JobUpdate,
)
from app.services.jobs import build_job_response, validate_skill_ids
from app.services.pagination import PaginatedResponse, validate_pagination_params

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("recruiter")),
) -> JobResponse:
    """
    Create a new job posting with associated skills.
    All skills are validated against the taxonomy and stored atomically.
    """
    skill_ids = [s.skill_id for s in job_in.skills]
    validate_skill_ids(db, skill_ids)

    job = Job(
        recruiter_id=current_user.id,
        title=job_in.title,
        description=job_in.description,
        min_experience_years=job_in.min_experience_years,
        education=job_in.education,
        status="open",
    )
    db.add(job)
    db.flush()

    for s in job_in.skills:
        db.add(
            JobSkill(
                job_id=job.id,
                skill_id=s.skill_id,
                importance=s.importance,
            )
        )

    audit = AuditLog(
        user_id=current_user.id,
        action="JOB_CREATED",
        entity_type="Job",
        entity_id=job.id,
        details={"title": job.title},
    )
    db.add(audit)

    try:
        db.commit()
        db.refresh(job)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create job posting.",
        )

    return build_job_response(job, db)


@router.get("/mine", response_model=List[JobResponse])
def get_my_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("recruiter")),
) -> List[JobResponse]:
    """
    List all job openings created by the authenticated recruiter.
    Returns deterministic order by creation date.
    """
    jobs = (
        db.query(Job)
        .filter(Job.recruiter_id == current_user.id)
        .order_by(Job.created_at.desc(), Job.id.desc())
        .all()
    )

    return [build_job_response(j, db) for j in jobs]


@router.get("", response_model=PaginatedResponse[JobResponse])
def browse_jobs(
    q: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("candidate")),
) -> PaginatedResponse[JobResponse]:
    """
    Candidate endpoint to browse available open jobs.
    Supports title keyword search and pagination.
    """
    clamped_limit, safe_offset = validate_pagination_params(limit, offset, max_limit=50)

    query = db.query(Job).filter(Job.status == "open")

    if q and q.strip():
        query = query.filter(Job.title.ilike(f"%{q.strip()}%"))

    total = query.count()

    jobs = (
        query.order_by(Job.created_at.desc(), Job.id.desc())
        .offset(safe_offset)
        .limit(clamped_limit)
        .all()
    )

    items = [build_job_response(j, db) for j in jobs]

    return PaginatedResponse(
        items=items,
        total=total,
        limit=clamped_limit,
        offset=safe_offset,
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job_by_id(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobResponse:
    """
    Retrieve job posting details.
    Candidates can view open jobs only.
    Recruiters can view their own jobs (even if closed).
    Returns 404 for unauthorized recruiter access or closed jobs requested by candidates.
    """
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    if current_user.role == "candidate":
        if job.status != "open":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found.",
            )
    elif current_user.role == "recruiter":
        if job.recruiter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found.",
            )
    elif current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted for current role.",
        )

    return build_job_response(job, db)


@router.put("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    job_in: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("recruiter")),
) -> JobResponse:
    """
    Update an owned job posting and replace its required skills transactionally.
    Returns 404 if the job does not exist or belongs to another recruiter.
    """
    job = (
        db.query(Job)
        .filter(Job.id == job_id, Job.recruiter_id == current_user.id)
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    skill_ids = [s.skill_id for s in job_in.skills]
    validate_skill_ids(db, skill_ids)

    # Update basic job fields
    job.title = job_in.title
    job.description = job_in.description
    job.min_experience_years = job_in.min_experience_years
    job.education = job_in.education

    # Replace the skills list transactionally
    db.query(JobSkill).filter(JobSkill.job_id == job.id).delete(synchronize_session=False)

    for s in job_in.skills:
        db.add(
            JobSkill(
                job_id=job.id,
                skill_id=s.skill_id,
                importance=s.importance,
            )
        )

    audit = AuditLog(
        user_id=current_user.id,
        action="JOB_UPDATED",
        entity_type="Job",
        entity_id=job.id,
        details={"title": job.title},
    )
    db.add(audit)

    try:
        db.commit()
        db.refresh(job)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update job posting.",
        )

    return build_job_response(job, db)


@router.patch("/{job_id}/status", response_model=JobResponse)
def update_job_status(
    job_id: int,
    status_in: JobStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("recruiter")),
) -> JobResponse:
    """
    Open or close a job opening owned by the authenticated recruiter.
    Returns 404 if the job belongs to another recruiter.
    """
    job = (
        db.query(Job)
        .filter(Job.id == job_id, Job.recruiter_id == current_user.id)
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    old_status = job.status
    job.status = status_in.status

    audit = AuditLog(
        user_id=current_user.id,
        action="JOB_STATUS_CHANGED",
        entity_type="Job",
        entity_id=job.id,
        details={"status": job.status, "previous_status": old_status},
    )
    db.add(audit)

    try:
        db.commit()
        db.refresh(job)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update job status.",
        )

    return build_job_response(job, db)


@router.post(
    "/{job_id}/apply",
    response_model=CandidateApplicationItem,
    status_code=status.HTTP_201_CREATED,
)
def apply_to_job(
    job_id: int,
    app_in: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("candidate")),
) -> CandidateApplicationItem:
    """
    Candidate applies to an open job opening using their uploaded resume.
    Enforces privacy consent, resume ownership, open job status, and duplicate prevention.
    """
    # 1. Candidate must have given consent
    profile = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )
    if profile is None or profile.consent_given_at is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please provide consent before applying for jobs.",
        )

    # 2. Job must exist and be open
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )
    if job.status != "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot apply to a closed job.",
        )

    # 3. Resume must exist and belong to the authenticated candidate
    resume = (
        db.query(Resume)
        .filter(
            Resume.id == app_in.resume_id,
            Resume.candidate_id == current_user.id,
        )
        .first()
    )
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or does not belong to you.",
        )

    # 4. Check for existing application
    existing_app = (
        db.query(Application)
        .filter(
            Application.candidate_id == current_user.id,
            Application.job_id == job.id,
        )
        .first()
    )
    if existing_app is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied to this job.",
        )

    # 5. Create application and record audit entry atomically
    application = Application(
        candidate_id=current_user.id,
        job_id=job.id,
        resume_id=resume.id,
        match_score=None,
        match_breakdown=None,
        status="applied",
    )
    db.add(application)
    db.flush()

    audit = AuditLog(
        user_id=current_user.id,
        action="APPLICATION_SUBMITTED",
        entity_type="Application",
        entity_id=application.id,
        details={"job_id": job.id, "resume_id": resume.id},
    )
    db.add(audit)

    try:
        db.commit()
        db.refresh(application)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied to this job.",
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not submit application.",
        )

    return CandidateApplicationItem(
        id=application.id,
        job_id=job.id,
        job_title=job.title,
        job_status=job.status,
        status=application.status,
        created_at=application.created_at,
    )


@router.get(
    "/{job_id}/applications",
    response_model=PaginatedResponse[ApplicantSummaryItem],
)
def list_job_applications(
    job_id: int,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("recruiter")),
) -> PaginatedResponse[ApplicantSummaryItem]:
    """
    List applicants for a job owned by the authenticated recruiter.
    Returns 404 if the job belongs to another recruiter.
    Enforces privacy by omitting candidate email and phone.
    """
    job = (
        db.query(Job)
        .filter(Job.id == job_id, Job.recruiter_id == current_user.id)
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    clamped_limit, safe_offset = validate_pagination_params(limit, offset, max_limit=50)

    query = db.query(Application).filter(Application.job_id == job.id)
    total = query.count()

    applications = (
        query.order_by(Application.created_at.desc(), Application.id.desc())
        .offset(safe_offset)
        .limit(clamped_limit)
        .all()
    )

    items: List[ApplicantSummaryItem] = []
    for app in applications:
        candidate_name = app.candidate.full_name if app.candidate else "Unknown"
        headline = None
        if app.candidate and app.candidate.candidate_profile:
            headline = app.candidate.candidate_profile.headline

        # Latest review decision
        latest_review = (
            db.query(RecruiterReview)
            .filter(RecruiterReview.application_id == app.id)
            .order_by(RecruiterReview.created_at.desc(), RecruiterReview.id.desc())
            .first()
        )
        latest_decision = latest_review.decision if latest_review else None

        items.append(
            ApplicantSummaryItem(
                id=app.id,
                candidate_id=app.candidate_id,
                candidate_name=candidate_name,
                headline=headline,
                status=app.status,
                created_at=app.created_at,
                latest_review_decision=latest_decision,
            )
        )

    return PaginatedResponse(
        items=items,
        total=total,
        limit=clamped_limit,
        offset=safe_offset,
    )
