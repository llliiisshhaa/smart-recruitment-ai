"""
Job and Application Models.
Defines recruiter job postings, required/preferred job skills, candidate job applications
with match scoring breakdowns, and recruiter review decisions.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Job(Base):
    """
    Job opening published by a recruiter.
    Contains job description, requirements, experience levels, and status.
    """

    __tablename__ = "jobs"

    # Primary key identifier
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Recruiter user who created and manages the job opening
    recruiter_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Job title (e.g., "Senior Python Engineer")
    title = Column(String(255), nullable=False)

    # Full job description and requirements
    description = Column(Text, nullable=False)

    # Minimum years of relevant experience requested
    min_experience_years = Column(Integer, default=0, nullable=False)

    # Educational qualification preferred/required (e.g., "Bachelor's in Computer Science")
    education = Column(String(255), nullable=True)

    # Job posting status: open or closed
    status = Column(String(50), default="open", nullable=False)

    # Timestamp when job was created
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Check constraint for valid job lifecycle status
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'closed')",
            name="check_job_status",
        ),
    )

    # Relationships
    recruiter = relationship("User", back_populates="jobs")

    # Associated skills with required/preferred importance
    job_skills = relationship(
        "JobSkill",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    # Job applications submitted for this role
    applications = relationship(
        "Application",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Job id={self.id} title='{self.title}' status='{self.status}'>"


class JobSkill(Base):
    """
    Association between a job posting and a skill.
    Specifies whether the skill is strictly required or preferred for the job.
    """

    __tablename__ = "job_skills"

    # Composite primary key: job_id + skill_id
    job_id = Column(
        Integer,
        ForeignKey("jobs.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    skill_id = Column(
        Integer,
        ForeignKey("skills.id", ondelete="RESTRICT"),
        primary_key=True,
        index=True,
    )

    # Skill priority level: required vs preferred
    importance = Column(String(50), default="required", nullable=False)

    # Check constraint for valid importance levels
    __table_args__ = (
        CheckConstraint(
            "importance IN ('required', 'preferred')",
            name="check_job_skill_importance",
        ),
    )

    # Relationships
    job = relationship("Job", back_populates="job_skills")
    skill = relationship("Skill", back_populates="job_skills")

    def __repr__(self) -> str:
        return f"<JobSkill job_id={self.job_id} skill_id={self.skill_id} importance='{self.importance}'>"


class Application(Base):
    """
    Candidate application for a specific job posting.
    Tracks application lifecycle stage, AI match score, and detailed scoring breakdown.
    Enforces that a candidate can only apply once to a given job.
    """

    __tablename__ = "applications"

    # Primary key identifier
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Candidate applying for the job
    candidate_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Job position being applied to
    job_id = Column(
        Integer,
        ForeignKey("jobs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Specific resume version used for this application (nullable if deleted)
    resume_id = Column(
        Integer,
        ForeignKey("resumes.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    # Overall AI resume-to-job match score percentage (0.0 - 100.0)
    match_score = Column(Float, nullable=True)

    # Detailed JSON breakdown of skills match, experience match, and gaps
    match_breakdown = Column(JSONB().with_variant(JSON, "sqlite"), nullable=True)

    # Application pipeline stage
    status = Column(String(50), default="applied", nullable=False)

    # Timestamp when application was submitted
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Constraints: Unique application per candidate per job, and valid status values
    __table_args__ = (
        UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job"),
        CheckConstraint(
            "status IN ('applied', 'interviewing', 'completed', 'reviewed')",
            name="check_application_status",
        ),
    )

    # Relationships
    candidate = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")
    interviews = relationship(
        "Interview",
        back_populates="application",
        cascade="all, delete-orphan",
    )
    reviews = relationship(
        "RecruiterReview",
        back_populates="application",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Application id={self.id} candidate_id={self.candidate_id} job_id={self.job_id} status='{self.status}'>"


class RecruiterReview(Base):
    """
    Recruiter feedback and decision on a candidate's application.
    Records shortlist, hold, or reject status with recruiter notes.
    """

    __tablename__ = "recruiter_reviews"

    # Primary key identifier
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Application under review
    application_id = Column(
        Integer,
        ForeignKey("applications.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Recruiter who evaluated the candidate
    recruiter_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Hiring decision: shortlist, hold, or reject
    decision = Column(String(50), nullable=False)

    # Qualitative notes and recruiter observations
    notes = Column(Text, nullable=True)

    # Timestamp when review decision was recorded
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Check constraint for valid review decisions
    __table_args__ = (
        CheckConstraint(
            "decision IN ('shortlist', 'hold', 'reject')",
            name="check_review_decision",
        ),
    )

    # Relationships
    application = relationship("Application", back_populates="reviews")
    recruiter = relationship("User", back_populates="recruiter_reviews")

    def __repr__(self) -> str:
        return f"<RecruiterReview id={self.id} application_id={self.application_id} decision='{self.decision}'>"
