"""
Pydantic schemas for recruiter profile management.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RecruiterProfileUpdate(BaseModel):
    """Schema for creating or updating recruiter company details."""

    company_name: str = Field(..., max_length=255, description="Employer or company name")

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("company_name must be a string")
        stripped = v.strip()
        if not stripped:
            raise ValueError("company_name cannot be blank")
        if len(stripped) > 255:
            raise ValueError("company_name cannot exceed 255 characters")
        return stripped


class RecruiterProfileResponse(BaseModel):
    """Safe recruiter profile representation."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: int
    company_name: Optional[str] = None
    created_at: Optional[datetime] = None
