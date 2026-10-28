"""
Pydantic schemas for job postings and associated skills.
"""

from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobSkillInput(BaseModel):
    """Associates a taxonomy skill with a job requirement."""

    skill_id: int = Field(..., gt=0, description="Skill identifier")
    importance: Literal["required", "preferred"] = Field(
        ...,
        description="Whether skill is mandatory or preferred",
    )


class JobSkillResponse(BaseModel):
    """Enriched skill detail associated with a job posting."""

    model_config = ConfigDict(from_attributes=True)

    skill_id: int
    name: str
    category: str
    importance: str


class JobCreate(BaseModel):
    """Payload for creating a new job posting."""

    title: str = Field(..., min_length=3, max_length=150)
    description: str = Field(...)
    min_experience_years: int = Field(default=0, ge=0, le=40)
    education: Optional[str] = Field(default=None, max_length=255)
    skills: List[JobSkillInput] = Field(..., min_length=1)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("title must be a string")
        stripped = v.strip()
        if len(stripped) < 3 or len(stripped) > 150:
            raise ValueError("Title length must be between 3 and 150 characters after trimming")
        return stripped

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("description must be a string")
        stripped = v.strip()
        if not stripped:
            raise ValueError("Description is required and cannot be blank")
        return stripped

    @field_validator("education")
    @classmethod
    def validate_education(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            return stripped if stripped else None
        return None

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v: List[JobSkillInput]) -> List[JobSkillInput]:
        if not v:
            raise ValueError("Job must specify at least one skill requirement")

        seen_ids = set()
        for item in v:
            if item.skill_id in seen_ids:
                raise ValueError("Duplicate skill IDs are not allowed in a job posting")
            seen_ids.add(item.skill_id)

        has_required = any(item.importance == "required" for item in v)
        if not has_required:
            raise ValueError("Job must require at least one required skill")

        return v


class JobUpdate(JobCreate):
    """Payload for updating an existing job posting."""
    pass


class JobStatusUpdate(BaseModel):
    """Payload for altering the lifecycle status of a job posting."""

    status: Literal["open", "closed"]


class JobResponse(BaseModel):
    """Publicly safe representation of a job opening."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    recruiter_id: int
    title: str
    description: str
    min_experience_years: int
    education: Optional[str] = None
    status: str
    created_at: datetime
    company_name: Optional[str] = None
    skills: List[JobSkillResponse] = []
