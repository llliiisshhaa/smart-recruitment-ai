"""
User and Profile Models.
Defines the core authentication entity (User) and role-specific profile extensions
(CandidateProfile, RecruiterProfile).
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """
    Core user account table.
    Stores login credentials, system roles, and account status for all actors
    (candidates, recruiters, system admins).
    """

    __tablename__ = "users"

    # Primary key: unique auto-incrementing integer identifier
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique email address used for login, indexed for fast lookup
    email = Column(String(255), unique=True, index=True, nullable=False)

    # Securely hashed password (never plain text)
    password_hash = Column(String(255), nullable=False)

    # User's full display name
    full_name = Column(String(255), nullable=False)

    # Role in the recruitment system: candidate, recruiter, or admin
    role = Column(String(50), nullable=False)

    # Account activation flag (e.g. for soft-disabling accounts)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamp when the user registered
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Role constraint ensuring only authorized role values can be stored
    __table_args__ = (
        CheckConstraint(
            "role IN ('candidate', 'recruiter', 'admin')",
            name="check_user_role",
        ),
    )

    # One-to-one profile relationships (cascade delete when user is deleted)
    candidate_profile = relationship(
        "CandidateProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    recruiter_profile = relationship(
        "RecruiterProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Domain entity relationships
    resumes = relationship(
        "Resume",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
    jobs = relationship(
        "Job",
        back_populates="recruiter",
        cascade="all, delete-orphan",
    )
    applications = relationship(
        "Application",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
    recruiter_reviews = relationship(
        "RecruiterReview",
        back_populates="recruiter",
        cascade="all, delete-orphan",
    )

    # Audit logs relationship: NEVER cascade delete audit records!
    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email='{self.email}' role='{self.role}'>"


class CandidateProfile(Base):
    """
    Profile extension for candidates.
    Stores additional personal details, headline, and GDPR/privacy consent timestamp.
    """

    __tablename__ = "candidate_profiles"

    # Primary key identifier
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key referencing users.id; unique=True enforces 1:1 relationship
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Contact phone number
    phone = Column(String(50), nullable=True)

    # Professional headline or summary (e.g., "Full Stack Developer")
    headline = Column(String(255), nullable=True)

    # Location (e.g., "San Francisco, CA")
    location = Column(String(255), nullable=True)

    # Timestamp when candidate provided consent for AI evaluation and data processing
    consent_given_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamp when profile was created
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Back-reference to User
    user = relationship("User", back_populates="candidate_profile")

    def __repr__(self) -> str:
        return f"<CandidateProfile id={self.id} user_id={self.user_id}>"


class RecruiterProfile(Base):
    """
    Profile extension for recruiters.
    Stores employer company information.
    """

    __tablename__ = "recruiter_profiles"

    # Primary key identifier
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key referencing users.id; unique=True enforces 1:1 relationship
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Company or organization name
    company_name = Column(String(255), nullable=False)

    # Timestamp when profile was created
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Back-reference to User
    user = relationship("User", back_populates="recruiter_profile")

    def __repr__(self) -> str:
        return f"<RecruiterProfile id={self.id} user_id={self.user_id} company='{self.company_name}'>"
