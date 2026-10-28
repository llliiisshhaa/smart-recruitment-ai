"""
Skills taxonomy routes.
Allows authenticated users to search standard technical and soft skills.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.resume import Skill
from app.models.user import User
from app.schemas.skills import SkillResponse

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("", response_model=List[SkillResponse])
def search_skills(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[SkillResponse]:
    """
    Search available skills in the global taxonomy.
    Accessible to all authenticated users.
    Limits results to a maximum of 50 with deterministic ordering.
    """
    query = db.query(Skill)

    if q and q.strip():
        search_term = f"%{q.strip().lower()}%"
        query = query.filter(Skill.name.ilike(search_term))

    skills = (
        query.order_by(Skill.name.asc(), Skill.id.asc())
        .limit(50)
        .all()
    )

    return skills
