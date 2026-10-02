from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.core.dependencies import get_current_user


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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be candidate or recruiter",
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
    db.commit()
    db.refresh(user)

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Prevent inactive accounts from logging in.
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create a JWT containing the user's ID.
    access_token = create_access_token(user.id)

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
