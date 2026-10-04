"""
Audit Logging Service.
Provides a resilient helper function to record immutable audit trail events
without interrupting or breaking active user requests.
"""

import logging
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


def log_event(
    db: Session,
    user_id: Optional[int],
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Optional[AuditLog]:
    """
    Record an immutable audit log event in the database.

    Args:
        db: SQLAlchemy database session.
        user_id: ID of the user performing the action (None for unauthenticated actions).
        action: Identifier for the action (e.g., 'USER_REGISTERED', 'LOGIN_SUCCESS', 'LOGIN_FAILED').
        entity_type: Name of the target entity type (e.g., 'user', 'resume').
        entity_id: Primary key of the affected entity (optional).
        details: Metadata dictionary (e.g., {'email': ...}). Sensitive values like passwords
                 MUST NEVER be included.

    Returns:
        The created AuditLog instance, or None if logging failed.
        Logging failures NEVER break the caller's request.
    """
    try:
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry
    except Exception as exc:
        logger.error(
            "Failed to record audit log for action='%s', entity='%s:%s': %s",
            action,
            entity_type,
            entity_id,
            exc,
        )
        try:
            db.rollback()
        except Exception:
            pass
        return None
