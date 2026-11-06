"""
Resume and Skill Models.
Defines uploaded candidate resumes, parsed structured data, global skills taxonomy,
and the resume-to-skills association with extracted evidence snippets.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, validates

from app.database import Base


class Skill(Base):
    """
    Standardized taxonomy of technical and soft skills.
    Names are automatically stored in lowercase to prevent duplicates (e.g. 'Python' vs 'python').
    """

    __tablename__ = "skills"

    # Primary key identifier
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique skill name (e.g., 'python', 'sql', 'system design'), always stored lowercase
    name = Column(String(100), unique=True, index=True, nullable=False)

    # Category grouping (e.g., 'Programming Language', 'Database', 'Soft Skill')
    category = Column(String(100), nullable=False)

    # Timestamp when skill was added to taxonomy
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    resume_skills = relationship(
        "ResumeSkill",
        back_populates="skill",
        cascade="all, delete-orphan",
    )
    job_skills = relationship(
        "JobSkill",
        back_populates="skill",
    )
    questions = relationship(
        "Question",
        back_populates="skill",
    )
    skill_assessments = relationship(
        "SkillAssessment",
        back_populates="skill",
    )

    @validates("name")
    def validate_name(self, key: str, value: str) -> str:
        """Enforces lowercase storage for consistent matching."""
        if value:
            return value.strip().lower()
        return value

    def __repr__(self) -> str:
        return f"<Skill id={self.id} name='{self.name}' category='{self.category}'>"


class Resume(Base):
    """
    Candidate uploaded resumes.
    Stores file storage path, raw extracted text, AI-parsed JSON data, and processing status.
    """

    __tablename__ = "resumes"

    # Primary key identifier
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key referencing candidate user
    candidate_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Path to saved file on disk/storage
    file_path = Column(String(500), nullable=False)

    # Original filename as uploaded by candidate
    original_filename = Column(String(255), nullable=False)

    # Full text extracted from PDF/DOCX resume file
    raw_text = Column(Text, nullable=True)

    # Structured AI-parsed resume data (experience, education, skills, projects)
    parsed_json = Column(JSONB().with_variant(JSON, "sqlite"), nullable=True)

    # Resume processing lifecycle status: pending, parsed, failed
    parse_status = Column(String(50), default="pending", nullable=False)

    # Timestamp when resume was uploaded
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Enforce valid parse status transitions
    __table_args__ = (
        CheckConstraint(
            "parse_status IN ('pending', 'parsed', 'failed')",
            name="check_resume_parse_status",
        ),
    )

    # Relationships
    candidate = relationship("User", back_populates="resumes")

    # Deleting a resume automatically deletes its extracted resume_skills records
    resume_skills = relationship(
        "ResumeSkill",
        back_populates="resume",
        cascade="all, delete-orphan",
    )

    applications = relationship(
        "Application",
        back_populates="resume",
    )

    def __repr__(self) -> str:
        return f"<Resume id={self.id} candidate_id={self.candidate_id} status='{self.parse_status}'>"


class ResumeSkill(Base):
    """
    Association between a resume and an extracted skill.
    Includes the specific textual evidence snippet found within the resume text.
    """

    __tablename__ = "resume_skills"

    # Composite primary key: resume_id + skill_id
    resume_id = Column(
        Integer,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    skill_id = Column(
        Integer,
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    # Sentence or paragraph snippet from resume demonstrating skill usage
    evidence_text = Column(Text, nullable=True)

    # Relationships
    resume = relationship("Resume", back_populates="resume_skills")
    skill = relationship("Skill", back_populates="resume_skills")

    def __repr__(self) -> str:
        return f"<ResumeSkill resume_id={self.resume_id} skill_id={self.skill_id}>"
