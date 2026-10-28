"""
Recruiter profile routes.
Handles retrieval and updates of recruiter company profiles.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.database import get_db
from app.models.user import RecruiterProfile, User
from app.schemas.recruiter import RecruiterProfileResponse, RecruiterProfileUpdate

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
