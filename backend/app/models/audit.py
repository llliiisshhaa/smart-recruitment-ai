"""
Audit Log Model.
Maintains an immutable audit trail of critical system actions (e.g. logins, reviews,
score overrides, consent actions). Designed for compliance and accountability.
Never cascade-deleted when users or related entities are removed.
"""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class AuditLog(Base):
    """
    Immutable system audit log entry.
    Tracks user actions, target entity types, changes, and contextual metadata.
    Preserves audit history even if the initiating user account is subsequently deleted.
    """

    __tablename__ = "audit_logs"

    # Primary key identifier
    id = Column(Integer, primary_key=True, autoincrement=True)

    # User who performed the action (nullable so log persists if user account is deleted)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    # Action performed (e.g., 'user.login', 'score.override', 'candidate.consent_given')
    action = Column(String(100), nullable=False)

    # Type of entity affected (e.g., 'user', 'interview', 'evaluation', 'job')
    entity_type = Column(String(100), nullable=False)

    # Primary key of the affected entity (nullable for global actions)
    entity_id = Column(Integer, nullable=True)

    # Additional contextual metadata and diff payload stored as JSON
    details = Column(JSONB().with_variant(JSON, "sqlite"), nullable=True)

    # Timestamp when the event occurred
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships: reference user without cascading deletions
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action='{self.action}' entity='{self.entity_type}:{self.entity_id}'>"
