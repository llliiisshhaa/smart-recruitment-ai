from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CandidateProfileUpdate(BaseModel):
    """Fields a candidate can update in their profile."""

    phone: str | None = Field(default=None, max_length=30)
    headline: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)


class CandidateProfileResponse(BaseModel):
    """Safe candidate profile information returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    phone: str | None = None
    headline: str | None = None
    location: str | None = None
    consent_given_at: datetime | None = None
    created_at: datetime