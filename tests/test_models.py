"""
Model and Database Constraint Tests for Smart Recruitment System.
Validates table constraints, unique keys, check constraints, foreign keys,
and cascade deletion rules using a dedicated test database (TEST_DATABASE_URL).
"""

import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

# Ensure backend directory is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.models import (
    Application,
    Base,
    Job,
    JobSkill,
    Resume,
    ResumeSkill,
    Skill,
    User,
)

# Normalize test database URL
test_db_url = settings.TEST_DATABASE_URL
if test_db_url.startswith("postgresql://"):
    test_db_url = test_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

# Dedicated engine for testing
test_engine = create_engine(test_db_url, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Session-wide fixture: Rebuilds schema on the isolated test database
    before running tests and cleans up after the test session finishes.
    """
    try:
        # Create all tables defined in Base.metadata
        Base.metadata.drop_all(bind=test_engine)
        Base.metadata.create_all(bind=test_engine)
    except Exception as exc:
        pytest.fail(f"Could not connect to or initialize test database at '{test_db_url}': {exc}")
    yield
    # Cleanup after test suite
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def db_session():
    """
    Per-test fixture: Provides a clean database session per test.
    Automatically rolls back and clears any lingering rows to ensure complete test isolation.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


# ==============================================================================
# Model Tests
# ==============================================================================


def test_create_user(db_session):
    """
    Verify that a user account can be created with valid credentials
    and read back from the database.
    """
    user = User(
        email="candidate.test@example.com",
        password_hash="argon2id$mock_hash_for_testing",
        full_name="Alice Candidate",
        role="candidate",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Query back the created user
    stmt = select(User).where(User.email == "candidate.test@example.com")
    saved_user = db_session.execute(stmt).scalar_one_or_none()

    assert saved_user is not None
    assert saved_user.id is not None
    assert saved_user.full_name == "Alice Candidate"
    assert saved_user.role == "candidate"
    assert saved_user.is_active is True
    assert saved_user.created_at is not None


def test_duplicate_email_fails(db_session):
    """
    Verify that the UNIQUE constraint on users.email is strictly enforced.
    Attempting to create a second user with the same email must raise IntegrityError.
    """
    user1 = User(
        email="duplicate.email@example.com",
        password_hash="hash1",
        full_name="First User",
        role="candidate",
    )
    db_session.add(user1)
    db_session.commit()

    user2 = User(
        email="duplicate.email@example.com",
        password_hash="hash2",
        full_name="Second User",
        role="recruiter",
    )
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_invalid_role_fails(db_session):
    """
    Verify that the CHECK constraint on users.role is enforced.
    Roles must be one of: 'candidate', 'recruiter', 'admin'.
    """
    invalid_user = User(
        email="invalid.role@example.com",
        password_hash="hash",
        full_name="Invalid Role User",
        role="super_admin",  # Invalid role not in check constraint
    )
    db_session.add(invalid_user)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_job_with_skills_saved_and_read_back(db_session):
    """
    Verify that a job posting can be created with associated skills
    and correct importance flags ('required', 'preferred'), then read back.
    """
    # Create recruiter user
    recruiter = User(
        email="recruiter.tech@company.com",
        password_hash="hash",
        full_name="Bob Recruiter",
        role="recruiter",
    )
    db_session.add(recruiter)
    db_session.flush()

    # Create skills
    python_skill = Skill(name="python", category="Programming Language")
    sql_skill = Skill(name="sql", category="Database")
    db_session.add_all([python_skill, sql_skill])
    db_session.flush()

    # Create job opening
    job = Job(
        recruiter_id=recruiter.id,
        title="Backend Software Engineer",
        description="Develop scalable FastAPI and SQLAlchemy services.",
        min_experience_years=2,
        education="Bachelor's in CS or equivalent",
        status="open",
    )
    db_session.add(job)
    db_session.flush()

    # Link skills with importance
    job_skill_1 = JobSkill(job_id=job.id, skill_id=python_skill.id, importance="required")
    job_skill_2 = JobSkill(job_id=job.id, skill_id=sql_skill.id, importance="preferred")
    db_session.add_all([job_skill_1, job_skill_2])
    db_session.commit()

    # Read back job with relationships
    stmt = select(Job).where(Job.id == job.id)
    retrieved_job = db_session.execute(stmt).scalar_one()

    assert retrieved_job.title == "Backend Software Engineer"
    assert len(retrieved_job.job_skills) == 2

    # Map skills and verify importance
    skill_importance = {js.skill.name: js.importance for js in retrieved_job.job_skills}
    assert skill_importance.get("python") == "required"
    assert skill_importance.get("sql") == "preferred"


def test_unique_candidate_job_application_enforced(db_session):
    """
    Verify that unique constraint uq_candidate_job on applications
    prevents a candidate from applying multiple times to the same job.
    """
    # Create candidate and recruiter
    candidate = User(
        email="candidate.applicant@example.com",
        password_hash="hash",
        full_name="Charlie Applicant",
        role="candidate",
    )
    recruiter = User(
        email="recruiter.hiring@example.com",
        password_hash="hash",
        full_name="Dave Hiring",
        role="recruiter",
    )
    db_session.add_all([candidate, recruiter])
    db_session.flush()

    # Create job
    job = Job(
        recruiter_id=recruiter.id,
        title="Data Analyst",
        description="Analyze recruitment metrics and pipelines.",
        status="open",
    )
    db_session.add(job)
    db_session.flush()

    # First application: succeeds
    app1 = Application(
        candidate_id=candidate.id,
        job_id=job.id,
        status="applied",
    )
    db_session.add(app1)
    db_session.commit()

    # Second application for same candidate and job: must fail
    app2 = Application(
        candidate_id=candidate.id,
        job_id=job.id,
        status="applied",
    )
    db_session.add(app2)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_delete_resume_removes_resume_skills(db_session):
    """
    Verify cascade delete: Deleting a candidate's resume must automatically
    delete all associated resume_skills records, while leaving the skill taxonomy intact.
    """
    # Create candidate
    candidate = User(
        email="resume.owner@example.com",
        password_hash="hash",
        full_name="Eve Candidate",
        role="candidate",
    )
    db_session.add(candidate)
    db_session.flush()

    # Create skills
    skill1 = Skill(name="react", category="Frontend")
    skill2 = Skill(name="typescript", category="Programming Language")
    db_session.add_all([skill1, skill2])
    db_session.flush()

    # Create resume
    resume = Resume(
        candidate_id=candidate.id,
        file_path="/storage/resumes/eve_resume.pdf",
        original_filename="eve_resume.pdf",
        raw_text="Experienced in React and TypeScript for 3 years.",
        parse_status="parsed",
    )
    db_session.add(resume)
    db_session.flush()

    # Associate resume skills
    rs1 = ResumeSkill(
        resume_id=resume.id,
        skill_id=skill1.id,
        evidence_text="Built single page applications using React.",
    )
    rs2 = ResumeSkill(
        resume_id=resume.id,
        skill_id=skill2.id,
        evidence_text="TypeScript used for type-safe frontend architecture.",
    )
    db_session.add_all([rs1, rs2])
    db_session.commit()

    # Verify resume skills exist
    rs_count = db_session.execute(
        select(ResumeSkill).where(ResumeSkill.resume_id == resume.id)
    ).scalars().all()
    assert len(rs_count) == 2

    # Delete resume
    db_session.delete(resume)
    db_session.commit()

    # Verify resume_skills records were cascade deleted
    remaining_rs = db_session.execute(
        select(ResumeSkill).where(ResumeSkill.resume_id == resume.id)
    ).scalars().all()
    assert len(remaining_rs) == 0

    # Verify global skills are NOT deleted
    remaining_skills = db_session.execute(
        select(Skill).where(Skill.id.in_([skill1.id, skill2.id]))
    ).scalars().all()
    assert len(remaining_skills) == 2
