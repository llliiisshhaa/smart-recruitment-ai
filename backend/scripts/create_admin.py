"""
Admin User Creation Script.
Safely and idempotently creates or verifies an administrative user account.
Reads credentials from the ADMIN_EMAIL and ADMIN_PASSWORD environment variables.

Usage:
    python backend/scripts/create_admin.py
"""

import os
import sys
from pathlib import Path

# Add backend directory to sys.path so app modules can be imported
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password
from app.services.audit import log_event


def create_or_verify_admin() -> int:
    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "").strip()

    if not admin_email or not admin_password:
        print(
            "ERROR: Both ADMIN_EMAIL and ADMIN_PASSWORD environment variables must be set.",
            file=sys.stderr,
        )
        print("Example: ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=AdminPassword123 python backend/scripts/create_admin.py")
        return 1

    if len(admin_password) < 8 or not any(c.isalpha() for c in admin_password) or not any(c.isdigit() for c in admin_password):
        print(
            "ERROR: ADMIN_PASSWORD must be at least 8 characters long and contain at least one letter and one digit.",
            file=sys.stderr,
        )
        return 1

    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.email == admin_email).first()

        if existing_user:
            if existing_user.role == "admin":
                print(f"[OK] Admin user '{admin_email}' already exists (id={existing_user.id}). No changes needed.")
                return 0

            # Promote existing user to admin
            existing_user.role = "admin"
            existing_user.is_active = True
            existing_user.password_hash = hash_password(admin_password)
            db.commit()
            db.refresh(existing_user)

            log_event(
                db=db,
                user_id=existing_user.id,
                action="ADMIN_PROMOTED",
                entity_type="user",
                entity_id=existing_user.id,
                details={"email": admin_email},
            )
            print(f"[SUCCESS] User '{admin_email}' (id={existing_user.id}) promoted to admin role.")
            return 0

        # Create new admin user
        new_admin = User(
            email=admin_email,
            password_hash=hash_password(admin_password),
            full_name="System Administrator",
            role="admin",
            is_active=True,
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)

        log_event(
            db=db,
            user_id=new_admin.id,
            action="ADMIN_CREATED",
            entity_type="user",
            entity_id=new_admin.id,
            details={"email": admin_email},
        )
        print(f"[SUCCESS] Admin user '{admin_email}' (id={new_admin.id}) created successfully.")
        return 0

    except Exception as exc:
        db.rollback()
        print(f"ERROR: Failed to create or update admin user: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(create_or_verify_admin())
