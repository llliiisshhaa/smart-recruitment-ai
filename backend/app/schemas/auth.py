from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Data required to create a new user account."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)
    role: str


class LoginRequest(BaseModel):
    """Credentials required to log in."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"