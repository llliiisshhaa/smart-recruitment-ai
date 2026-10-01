"""
SQLAlchemy Models for Smart Recruitment System.
Central registry exporting all database entity models and Base metadata.
"""

from app.database import Base
from app.models.user import User, CandidateProfile, RecruiterProfile
from app.models.resume import Skill, Resume, ResumeSkill
from app.models.job import Job, JobSkill, Application, RecruiterReview
from app.models.interview import (
    Question,
    Interview,
    InterviewQuestion,
    Answer,
    Evaluation,
    SkillAssessment,
    Report,
)
from app.models.audit import AuditLog

__all__ = [
    "Base",
    "User",
    "CandidateProfile",
    "RecruiterProfile",
    "Skill",
    "Resume",
    "ResumeSkill",
    "Job",
    "JobSkill",
    "Application",
    "RecruiterReview",
    "Question",
    "Interview",
    "InterviewQuestion",
    "Answer",
    "Evaluation",
    "SkillAssessment",
    "Report",
    "AuditLog",
]
