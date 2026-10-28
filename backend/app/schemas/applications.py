"""
Pydantic schemas for candidate applications, applicant listings, recruiter reviews,
and privacy-controlled applicant details.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApplicationCreate(BaseModel):
    """Payload submitted by a candidate to apply for an open job."""

    resume_id: int = Field(..., gt=0, description="Candidate resume ID to attach")


class CandidateApplicationItem(BaseModel):
    """Application summary returned to the authenticated candidate."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    job_title: str
    job_status: str
    status: str
    created_at: datetime


class ApplicantSummaryItem(BaseModel):
    """
    Summary view of an applicant in recruiter job applicant listings.
    Excludes candidate email and phone to enforce privacy.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    candidate_name: str
    headline: Optional[str] = None
    status: str
    created_at: datetime
    latest_review_decision: Optional[str] = None


class ReviewCreate(BaseModel):
    """Recruiter decision and feedback on a candidate application."""

    decision: Literal["shortlist", "hold", "reject"]
    notes: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            return stripped if stripped else None
        return None


class ReviewResponse(BaseModel):
    """Recruiter evaluation record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    recruiter_id: int
    decision: str
    notes: Optional[str] = None
    created_at: datetime


class ResumeMetaResponse(BaseModel):
    """
    Safe resume metadata view for recruiters.
    Explicitly excludes filesystem paths and raw resume text.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    parse_status: str
    created_at: datetime
    parsed_json: Optional[Dict[str, Any]] = None
    extracted_skills: Optional[List[str]] = None


class ApplicantDetailResponse(BaseModel):
    """
    Comprehensive applicant dossier for the hiring recruiter.
    Candidate email and phone are hidden by default unless reveal_contact is requested.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    job_id: int
    status: str
    created_at: datetime
    candidate_name: str
    headline: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    resume: Optional[ResumeMetaResponse] = None
    reviews: List[ReviewResponse] = []
