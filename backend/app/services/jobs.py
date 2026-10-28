"""
Job management service functions.
Handles taxonomy validation, response serialization, and job lifecycle transactions.
"""

from typing import List, Set
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.job import Job, JobSkill
from app.models.resume import Skill
from app.models.user import RecruiterProfile
from app.schemas.jobs import JobResponse, JobSkillResponse


def validate_skill_ids(db: Session, skill_ids: List[int]) -> None:
    """
    Ensure all referenced skill IDs exist in the standardized taxonomy.
    Raises HTTPException 400 if any skill ID is missing.
    """
    if not skill_ids:
        return

    unique_ids: Set[int] = set(skill_ids)
    existing_skills = (
        db.query(Skill.id)
        .filter(Skill.id.in_(unique_ids))
        .all()
    )
    existing_id_set = {s[0] for s in existing_skills}
    missing_ids = unique_ids - existing_id_set

    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The following skill IDs do not exist: {sorted(list(missing_ids))}",
        )


def build_job_response(job: Job, db: Session) -> JobResponse:
    """
    Serialize a Job model instance into a safe JobResponse,
    enriching with recruiter company name and skill details.
    """
    # Fetch recruiter company name if available
    company_name = None
    if job.recruiter_id:
        profile = (
            db.query(RecruiterProfile)
            .filter(RecruiterProfile.user_id == job.recruiter_id)
            .first()
        )
        if profile:
            company_name = profile.company_name

    # Load associated skills
    skills_response: List[JobSkillResponse] = []
    if job.job_skills:
        for js in job.job_skills:
            skill_name = js.skill.name if js.skill else "unknown"
            skill_category = js.skill.category if js.skill else "unknown"
            skills_response.append(
                JobSkillResponse(
                    skill_id=js.skill_id,
                    name=skill_name,
                    category=skill_category,
                    importance=js.importance,
                )
            )

    # Sort skills deterministically by name
    skills_response.sort(key=lambda x: (x.importance != "required", x.name))

    return JobResponse(
        id=job.id,
        recruiter_id=job.recruiter_id,
        title=job.title,
        description=job.description,
        min_experience_years=job.min_experience_years,
        education=job.education,
        status=job.status,
        created_at=job.created_at,
        company_name=company_name,
        skills=skills_response,
    )
