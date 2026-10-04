from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.user import CandidateProfile, RecruiterProfile, User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.audit import log_event


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new candidate or recruiter account."""

    # Only candidates and recruiters can register publicly.
    allowed_roles = {"candidate", "recruiter"}

    if request.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration is only permitted for candidate and recruiter roles",
        )

    # Check whether the email is already registered.
    existing_user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    # Store only the secure password hash, never the plain password.
    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        role=request.role,
    )

    db.add(user)
    db.flush()

    # Automatically create the matching empty profile extension row
    if user.role == "candidate":
        db.add(CandidateProfile(user_id=user.id))
    elif user.role == "recruiter":
        db.add(RecruiterProfile(user_id=user.id, company_name=""))

    db.commit()
    db.refresh(user)

    # Record registration audit trail
    log_event(
        db=db,
        user_id=user.id,
        action="USER_REGISTERED",
        entity_type="user",
        entity_id=user.id,
        details={"email": user.email, "role": user.role},
    )

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login_user(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate a user and return a JWT access token."""

    # Find the user by email.
    user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    # Use the same error message for unknown email and wrong password.
    # This avoids revealing whether an email exists.
    if not user or not verify_password(
        request.password,
        user.password_hash,
    ):
        log_event(
            db=db,
            user_id=None,
            action="LOGIN_FAILED",
            entity_type="user",
            entity_id=None,
            details={"attempted_email": request.email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Prevent inactive accounts from logging in.
    if not user.is_active:
        log_event(
            db=db,
            user_id=user.id,
            action="LOGIN_FAILED",
            entity_type="user",
            entity_id=user.id,
            details={"attempted_email": request.email, "reason": "inactive_account"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create a JWT containing user ID, role, and expiry.
    access_token = create_access_token(user_id=user.id, role=user.role)

    # Record successful login audit trail
    log_event(
        db=db,
        user_id=user.id,
        action="LOGIN_SUCCESS",
        entity_type="user",
        entity_id=user.id,
        details={"email": user.email},
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """Return the currently authenticated user's information."""

    return current_user


# ==============================================================================
# Demo RBAC Endpoints (Demonstrating Role-Based Access Control)
# ==============================================================================


@router.get(
    "/candidate-only",
    status_code=status.HTTP_200_OK,
    tags=["Authentication Demo"],
)
def candidate_only_demo(
    current_user: User = Depends(require_roles("candidate")),
):
    """Demo endpoint restricted to candidates only."""
    return {
        "message": "Welcome candidate",
        "user_id": current_user.id,
        "role": current_user.role,
    }


@router.get(
    "/recruiter-only",
    status_code=status.HTTP_200_OK,
    tags=["Authentication Demo"],
)
def recruiter_only_demo(
    current_user: User = Depends(require_roles("recruiter")),
):
    """Demo endpoint restricted to recruiters only."""
    return {
        "message": "Welcome recruiter",
        "user_id": current_user.id,
        "role": current_user.role,
    }


@router.get(
    "/admin-only",
    status_code=status.HTTP_200_OK,
    tags=["Authentication Demo"],
)
def admin_only_demo(
    current_user: User = Depends(require_roles("admin")),
):
    """Demo endpoint restricted to system administrators only."""
    return {
        "message": "Welcome admin",
        "user_id": current_user.id,
        "role": current_user.role,
    }
