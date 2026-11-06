"""
Test Configuration and Shared Fixtures for Smart Recruitment Backend.
Sets up the isolated PostgreSQL test database, FastAPI TestClient, and role-based auth fixtures.
"""

import sys
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Ensure backend directory is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models.user import CandidateProfile, RecruiterProfile, User
from app.core.security import create_access_token, hash_password

# Normalize test database URL
test_db_url = settings.TEST_DATABASE_URL
if test_db_url.startswith("postgresql://"):
    test_db_url = test_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

test_engine = create_engine(test_db_url, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database schema is created on test database."""
    Base.metadata.create_all(bind=test_engine)
    yield
    # Clean up schema after entire test session finishes
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Provide a database session for test verification and setup."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def clean_database():
    """Clean all tables before and after each test to ensure complete test isolation."""
    with test_engine.connect() as conn:
        with conn.begin():
            for table in reversed(Base.metadata.sorted_tables):
                conn.execute(table.delete())
    yield
    with test_engine.connect() as conn:
        with conn.begin():
            for table in reversed(Base.metadata.sorted_tables):
                conn.execute(table.delete())


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient with database session overridden to use the test database."""
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def candidate_user(db: Session) -> User:
    """Create and return a candidate user fixture with a candidate profile."""
    user = User(
        email="candidate.fixture@example.com",
        password_hash=hash_password("Candidate123!"),
        full_name="Alice Candidate",
        role="candidate",
        is_active=True,
    )
    db.add(user)
    db.flush()
    profile = CandidateProfile(user_id=user.id)
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def candidate_headers(candidate_user: User) -> dict:
    """Return Authorization Bearer header for the candidate fixture."""
    token = create_access_token(user_id=candidate_user.id, role=candidate_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def recruiter_user(db: Session) -> User:
    """Create and return a recruiter user fixture with a recruiter profile."""
    user = User(
        email="recruiter.fixture@example.com",
        password_hash=hash_password("Recruiter123!"),
        full_name="Bob Recruiter",
        role="recruiter",
        is_active=True,
    )
    db.add(user)
    db.flush()
    profile = RecruiterProfile(user_id=user.id, company_name="Tech Recruitment Inc.")
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def recruiter_headers(recruiter_user: User) -> dict:
    """Return Authorization Bearer header for the recruiter fixture."""
    token = create_access_token(user_id=recruiter_user.id, role=recruiter_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db: Session) -> User:
    """Create and return an admin user fixture."""
    user = User(
        email="admin.fixture@example.com",
        password_hash=hash_password("Admin123!"),
        full_name="Charlie Admin",
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_headers(admin_user: User) -> dict:
    """Return Authorization Bearer header for the admin fixture."""
    token = create_access_token(user_id=admin_user.id, role=admin_user.role)
    return {"Authorization": f"Bearer {token}"}
