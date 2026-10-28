from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.database import get_db
from app.models.audit import AuditLog
from app.models.user import CandidateProfile, User
from app.schemas.candidate import (
    CandidateProfileResponse,
    CandidateProfileUpdate,
)

router = APIRouter(prefix="/candidates", tags=["Candidates"])


def get_or_create_profile(
    db: Session,
    user: User,
) -> CandidateProfile:
    """Return the candidate's profile, creating it if necessary."""

    profile = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == user.id)
        .first()
    )

    if profile is None:
        profile = CandidateProfile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return profile


@router.get(
    "/me",
    response_model=CandidateProfileResponse,
)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("candidate")),
):
    """Get the authenticated candidate's profile."""

    return get_or_create_profile(db, current_user)


@router.put(
    "/me",
    response_model=CandidateProfileResponse,
)
def update_my_profile(
    profile_data: CandidateProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("candidate")),
):
    """Update the authenticated candidate's profile."""

    profile = get_or_create_profile(db, current_user)

    updates = profile_data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(profile, field, value)

    try:
        db.commit()
        db.refresh(profile)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update candidate profile.",
        )

    return profile


@router.post(
    "/me/consent",
    response_model=CandidateProfileResponse,
)
def give_consent(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("candidate")),
):
    """Record candidate consent without overwriting an existing timestamp."""

    profile = get_or_create_profile(db, current_user)

    # Consent is idempotent: repeated requests preserve the original timestamp.
    if profile.consent_given_at is not None:
        return profile

    profile.consent_given_at = datetime.now(timezone.utc)

    audit_log = AuditLog(
        user_id=current_user.id,
        action="CONSENT_GIVEN",
        entity_type="CandidateProfile",
        entity_id=profile.id,
        details={"message": "Candidate consent recorded"},
    )

    try:
        db.add(audit_log)
        db.commit()
        db.refresh(profile)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not record candidate consent.",
        )

    return profile