from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class ExtractedSkillItem(BaseModel):
    """Extracted skill information with evidence snippet and contextual support."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    category: Optional[str] = None
    evidence_text: Optional[str] = None
    supported_by_context: Optional[bool] = None


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


class ParsedResumeResponse(BaseModel):
    """Detailed response for parsed resume results."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    original_filename: str
    parse_status: str
    parsed_json: Optional[Dict[str, Any]] = None
    skills: List[ExtractedSkillItem] = []
    created_at: datetime
