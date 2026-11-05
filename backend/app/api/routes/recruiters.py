"""
Recruiter profile and dashboard statistics routes.
Handles retrieval and updates of recruiter company profiles and aggregate job/application stats.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.database import get_db
from app.models.job import Application, Job, RecruiterReview
from app.models.user import RecruiterProfile, User
from app.schemas.recruiter import (
    JobApplicationCount,
    RecentApplicationItem,
    RecruiterProfileResponse,
    RecruiterProfileUpdate,
    RecruiterStatsResponse,
)

router = APIRouter(prefix="/recruiters", tags=["Recruiters"])


@router.get("/me", response_model=RecruiterProfileResponse)
def get_my_recruiter_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("recruiter")),
) -> RecruiterProfileResponse:
    """
    Get the authenticated recruiter's profile.
    Handles missing profiles cleanly without violating the non-null company_name constraint.
    """
    profile = (
        db.query(RecruiterProfile)
        .filter(RecruiterProfile.user_id == current_user.id)
        .first()
    )

    if profile is None:
        return RecruiterProfileResponse(
            id=None,
            user_id=current_user.id,
            company_name=None,
            created_at=None,
        )

    return profile


@router.put("/me", response_model=RecruiterProfileResponse)
def update_my_recruiter_profile(
    profile_data: RecruiterProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("recruiter")),
) -> RecruiterProfileResponse:
    """
    Create or update the recruiter profile with company name.
    Creates the profile on the first successful update if it does not yet exist.
    """
    profile = (
        db.query(RecruiterProfile)
        .filter(RecruiterProfile.user_id == current_user.id)
        .first()
    )

    if profile is None:
        profile = RecruiterProfile(
            user_id=current_user.id,
            company_name=profile_data.company_name,
        )
        db.add(profile)
    else:
        profile.company_name = profile_data.company_name

    try:
        db.commit()
        db.refresh(profile)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save recruiter profile.",
        )

    return profile


@router.get("/me/stats", response_model=RecruiterStatsResponse)
def get_recruiter_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("recruiter")),
) -> RecruiterStatsResponse:
    """
    Get aggregated dashboard statistics for the authenticated recruiter.
    All statistics are scoped strictly to jobs owned by this recruiter.
    """
    # 1. Active and closed jobs count
    job_counts = db.execute(
        select(
            func.count(case((Job.status == "open", Job.id), else_=None)).label("active_jobs"),
            func.count(case((Job.status == "closed", Job.id), else_=None)).label("closed_jobs"),
        ).where(Job.recruiter_id == current_user.id)
    ).one()

    active_jobs = job_counts.active_jobs or 0
    closed_jobs = job_counts.closed_jobs or 0

    # 2. Latest review per application subquery for applications to this recruiter's jobs
    latest_review_id_subq = (
        select(
            RecruiterReview.application_id.label("application_id"),
            func.max(RecruiterReview.id).label("latest_review_id"),
        )
        .join(Application, Application.id == RecruiterReview.application_id)
        .join(Job, Job.id == Application.job_id)
        .where(Job.recruiter_id == current_user.id)
        .group_by(RecruiterReview.application_id)
        .subquery()
    )

    latest_review_subq = (
        select(
            latest_review_id_subq.c.application_id,
            RecruiterReview.decision.label("latest_decision"),
        )
        .join(
            RecruiterReview,
            RecruiterReview.id == latest_review_id_subq.c.latest_review_id,
        )
        .subquery()
    )

    # 3. Aggregate application status and latest review decision counts
    app_stats = db.execute(
        select(
            func.count(Application.id).label("total_applications"),
            func.count(case((Application.status == "applied", Application.id), else_=None)).label("awaiting_review"),
            func.count(case((latest_review_subq.c.latest_decision == "shortlist", Application.id), else_=None)).label("shortlisted"),
            func.count(case((latest_review_subq.c.latest_decision == "hold", Application.id), else_=None)).label("on_hold"),
            func.count(case((latest_review_subq.c.latest_decision == "reject", Application.id), else_=None)).label("rejected"),
        )
        .select_from(Application)
        .join(Job, Job.id == Application.job_id)
        .outerjoin(
            latest_review_subq,
            latest_review_subq.c.application_id == Application.id,
        )
        .where(Job.recruiter_id == current_user.id)
    ).one()

    total_applications = app_stats.total_applications or 0
    awaiting_review = app_stats.awaiting_review or 0
    shortlisted = app_stats.shortlisted or 0
    on_hold = app_stats.on_hold or 0
    rejected = app_stats.rejected or 0

    # 4. Applications per job
    apps_per_job_rows = db.execute(
        select(
            Job.id.label("job_id"),
            Job.title.label("title"),
            func.count(Application.id).label("count"),
        )
        .outerjoin(Application, Application.job_id == Job.id)
        .where(Job.recruiter_id == current_user.id)
        .group_by(Job.id, Job.title)
        .order_by(Job.id.asc())
    ).all()

    applications_per_job = [
        JobApplicationCount(
            job_id=row.job_id,
            title=row.title,
            count=row.count,
        )
        for row in apps_per_job_rows
    ]

    # 5. Latest 5 applications
    recent_apps_rows = db.execute(
        select(
            Application.id.label("application_id"),
            User.full_name.label("candidate_name"),
            Job.title.label("job_title"),
            Application.status.label("status"),
            Application.created_at.label("applied_at"),
        )
        .join(Job, Job.id == Application.job_id)
        .join(User, User.id == Application.candidate_id)
        .where(Job.recruiter_id == current_user.id)
        .order_by(Application.created_at.desc(), Application.id.desc())
        .limit(5)
    ).all()

    recent_applications = [
        RecentApplicationItem(
            application_id=row.application_id,
            candidate_name=row.candidate_name,
            job_title=row.job_title,
            status=row.status,
            applied_at=row.applied_at,
        )
        for row in recent_apps_rows
    ]

    return RecruiterStatsResponse(
        active_jobs=active_jobs,
        closed_jobs=closed_jobs,
        total_applications=total_applications,
        awaiting_review=awaiting_review,
        shortlisted=shortlisted,
        on_hold=on_hold,
        rejected=rejected,
        applications_per_job=applications_per_job,
        recent_applications=recent_applications,
    )
