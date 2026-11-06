"""
Pydantic schemas for recruiter profile management and dashboard statistics.
"""

from datetime import datetime
from typing import List, Optional
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


class JobApplicationCount(BaseModel):
    """Application count summary per job posting."""

    model_config = ConfigDict(from_attributes=True)

    job_id: int
    title: str
    count: int


class RecentApplicationItem(BaseModel):
    """Recent application summary item for recruiter overview."""

    model_config = ConfigDict(from_attributes=True)

    application_id: int
    candidate_name: str
    job_title: str
    status: str
    applied_at: datetime


class RecruiterStatsResponse(BaseModel):
    """Aggregated statistics for authenticated recruiter's job openings and applicants."""

    model_config = ConfigDict(from_attributes=True)

    active_jobs: int
    closed_jobs: int
    total_applications: int
    awaiting_review: int
    shortlisted: int
    on_hold: int
    rejected: int
    applications_per_job: List[JobApplicationCount] = Field(default_factory=list)
    recent_applications: List[RecentApplicationItem] = Field(default_factory=list)
