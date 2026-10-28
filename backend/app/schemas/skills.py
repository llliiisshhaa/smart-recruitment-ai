"""
Pydantic schemas for skill endpoints.
"""

from pydantic import BaseModel, ConfigDict


class SkillResponse(BaseModel):
    """Safe skill item response exposing only public taxonomy information."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
