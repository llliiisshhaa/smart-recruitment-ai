from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    """Safe response returned after uploading or viewing a resume."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    original_filename: str
    parse_status: str
    created_at: datetime


class ResumeListItem(BaseModel):
    """Safe summary returned when listing resumes."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    parse_status: str
    created_at: datetime