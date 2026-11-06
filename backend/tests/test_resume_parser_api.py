"""
API integration tests for resume parsing:
- POST /resumes/{id}/parse (Candidate owner only, idempotent, audit logging, error handling)
- GET /resumes/{id}/parsed (Candidate owner only, structured JSON, extracted skills)
- GET /applications/{application_id} (Recruiter dossier, contact privacy, skill evidence)
"""

from datetime import datetime, timezone
from pathlib import Path
import docx
import pytest
from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.core.dependencies import get_current_user
from app.database import Base, get_db
from app.main import app
from app.models import (
    Application,
    AuditLog,
    CandidateProfile,
    Job,
    RecruiterProfile,
    RecruiterReview,
    Resume,
    ResumeSkill,
    Skill,
    User,
)


@pytest.fixture
def parser_api(tmp_path, monkeypatch):
    """
    Isolated test environment for resume parsing API endpoints.
    Uses in-memory SQLite and isolated temporary filesystem.
    """
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    upload_dir = tmp_path / "test_uploads"
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload_dir))

    with TestingSessionLocal() as db:
        # Create candidate users
        candidate1 = User(
            email="candidate1@example.com",
            password_hash="test-hash",
            full_name="Candidate One",
            role="candidate",
            is_active=True,
        )
        candidate2 = User(
            email="candidate2@example.com",
            password_hash="test-hash",
            full_name="Candidate Two",
            role="candidate",
            is_active=True,
        )
        recruiter1 = User(
            email="recruiter1@example.com",
            password_hash="test-hash",
            full_name="Recruiter One",
            role="recruiter",
            is_active=True,
        )
        recruiter2 = User(
            email="recruiter2@example.com",
            password_hash="test-hash",
            full_name="Recruiter Two",
            role="recruiter",
            is_active=True,
        )
        db.add_all([candidate1, candidate2, recruiter1, recruiter2])
        db.commit()

        # Profiles
        cp1 = CandidateProfile(
            user_id=candidate1.id,
            phone="+91 99999 11111",
            headline="Full Stack Python Engineer",
            consent_given_at=datetime.now(timezone.utc),
        )
        cp2 = CandidateProfile(
            user_id=candidate2.id,
            phone="+91 88888 22222",
            headline="Frontend Engineer",
            consent_given_at=datetime.now(timezone.utc),
        )
        rp1 = RecruiterProfile(user_id=recruiter1.id, company_name="TechCorp")
        rp2 = RecruiterProfile(user_id=recruiter2.id, company_name="InnovateCo")
        db.add_all([cp1, cp2, rp1, rp2])
        db.commit()

        # Seed Skills taxonomy
        skills = [
            Skill(name="python", category="Programming Language"),
            Skill(name="javascript", category="Programming Language"),
            Skill(name="react", category="Frontend Framework"),
            Skill(name="fastapi", category="Backend Framework"),
            Skill(name="postgresql", category="Database"),
            Skill(name="docker", category="DevOps"),
            Skill(name="ci/cd", category="DevOps"),
            Skill(name="c++", category="Programming Language"),
        ]
        db.add_all(skills)
        db.commit()

        # Jobs
        job1 = Job(
            recruiter_id=recruiter1.id,
            title="Senior Python Engineer",
            description="Build backend services",
            status="open",
        )
        job2 = Job(
            recruiter_id=recruiter2.id,
            title="Another Recruiter Job",
            description="Other role",
            status="open",
        )
        db.add_all([job1, job2])
        db.commit()

        # Create physical resume files for candidate1
        cand1_dir = upload_dir / str(candidate1.id)
        cand1_dir.mkdir(parents=True, exist_ok=True)

        # 1. Valid PDF resume with skills and projects
        valid_pdf_path = cand1_dir / "valid_resume.pdf"
        c = canvas.Canvas(str(valid_pdf_path), pagesize=letter)
        c.drawString(72, 750, "Candidate One")
        c.drawString(72, 735, "Email: candidate1@example.com | Phone: +91 99999 11111")
        c.drawString(72, 720, "https://github.com/candidateone https://linkedin.com/in/candidateone")
        c.drawString(72, 690, "EDUCATION")
        c.drawString(72, 675, "Bachelor of Technology in Computer Science - XYZ University 2018 - 2022")
        c.drawString(72, 650, "TECHNICAL SKILLS")
        c.drawString(72, 635, "Python, FastAPI, Postgres, Docker, ReactJS, CI/CD, C++")
        c.drawString(72, 605, "PROJECTS")
        c.drawString(72, 590, "Automated Recruitment System")
        c.drawString(72, 575, "- Developed RESTful backend APIs using Python and FastAPI.")
        c.drawString(72, 560, "- Containerized application deployments using Docker and GitHub Actions.")
        c.drawString(72, 530, "WORK EXPERIENCE")
        c.drawString(72, 515, "Junior Software Developer at Tech Labs")
        c.drawString(72, 500, "Jan 2022 - Present")
        c.drawString(72, 485, "- Maintained database schemas in PostgreSQL.")
        c.save()

        # 2. Corrupt file
        corrupt_path = cand1_dir / "corrupt_resume.pdf"
        corrupt_path.write_bytes(b"%PDF-corrupted data")

        # 3. Image-only PDF (no text)
        image_only_path = cand1_dir / "image_only.pdf"
        c_img = canvas.Canvas(str(image_only_path), pagesize=letter)
        c_img.rect(50, 50, 400, 600, stroke=1, fill=1)
        c_img.save()

        # Database Resume rows for candidate1
        resume_valid = Resume(
            candidate_id=candidate1.id,
            file_path=str(valid_pdf_path),
            original_filename="valid_resume.pdf",
            parse_status="pending",
        )
        resume_corrupt = Resume(
            candidate_id=candidate1.id,
            file_path=str(corrupt_path),
            original_filename="corrupt_resume.pdf",
            parse_status="pending",
        )
        resume_image = Resume(
            candidate_id=candidate1.id,
            file_path=str(image_only_path),
            original_filename="image_only.pdf",
            parse_status="pending",
        )
        resume_missing = Resume(
            candidate_id=candidate1.id,
            file_path=str(cand1_dir / "non_existent.pdf"),
            original_filename="non_existent.pdf",
            parse_status="pending",
        )
        db.add_all([resume_valid, resume_corrupt, resume_image, resume_missing])
        db.commit()

        # Application for Job1 by candidate1 linking resume_valid
        app1 = Application(
            candidate_id=candidate1.id,
            job_id=job1.id,
            resume_id=resume_valid.id,
            status="applied",
        )
        db.add(app1)
        db.commit()

        user_ids = {
            "candidate1": candidate1.id,
            "candidate2": candidate2.id,
            "recruiter1": recruiter1.id,
            "recruiter2": recruiter2.id,
        }
        resume_ids = {
            "valid": resume_valid.id,
            "corrupt": resume_corrupt.id,
            "image": resume_image.id,
            "missing": resume_missing.id,
        }
        app_ids = {
            "app1": app1.id,
        }

    active_user = {"id": user_ids["candidate1"]}

    def override_get_db():
        with TestingSessionLocal() as session:
            yield session

    def override_get_current_user(db=__import__("fastapi").Depends(override_get_db)):
        return db.query(User).filter(User.id == active_user["id"]).first()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as client:
        yield {
            "client": client,
            "users": user_ids,
            "resumes": resume_ids,
            "apps": app_ids,
            "active_user": active_user,
            "Session": TestingSessionLocal,
        }

    app.dependency_overrides.clear()


# ==============================================================================
# 1. PARSE RESUME (POST /resumes/{id}/parse) TESTS
# ==============================================================================

def test_parse_resume_success(parser_api):
    client = parser_api["client"]
    resume_id = parser_api["resumes"]["valid"]

    response = client.post(f"/resumes/{resume_id}/parse")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == resume_id
    assert data["parse_status"] == "parsed"
    assert data["parsed_json"] is not None

    # Check extracted skills with evidence
    skills = data["skills"]
    assert len(skills) > 0
    skill_names = {s["name"] for s in skills}
    assert "python" in skill_names
    assert "fastapi" in skill_names
    assert "postgresql" in skill_names
    assert "docker" in skill_names

    # Check that python has contextual support (from Projects section)
    py_skill = next(s for s in skills if s["name"] == "python")
    assert py_skill["supported_by_context"] is True
    assert "FastAPI" in py_skill["evidence_text"]

    # Verify database persistence
    with parser_api["Session"]() as db:
        db_resume = db.query(Resume).filter(Resume.id == resume_id).first()
        assert db_resume.parse_status == "parsed"
        assert "Candidate One" in db_resume.raw_text
        assert db_resume.parsed_json is not None

        # Check ResumeSkill records
        db_skills = db.query(ResumeSkill).filter(ResumeSkill.resume_id == resume_id).all()
        assert len(db_skills) >= 4
        for rs in db_skills:
            assert rs.evidence_text is not None

        # Check Audit Log
        audit = (
            db.query(AuditLog)
            .filter(AuditLog.entity_id == resume_id, AuditLog.action == "RESUME_PARSED")
            .first()
        )
        assert audit is not None
        assert "password" not in str(audit.details)
        assert "raw_text" not in str(audit.details)


def test_parse_resume_idempotent_no_duplicates(parser_api):
    client = parser_api["client"]
    resume_id = parser_api["resumes"]["valid"]

    # First parse
    resp1 = client.post(f"/resumes/{resume_id}/parse")
    assert resp1.status_code == 200
    skills_count_1 = len(resp1.json()["skills"])

    # Second parse
    resp2 = client.post(f"/resumes/{resume_id}/parse")
    assert resp2.status_code == 200
    skills_count_2 = len(resp2.json()["skills"])

    assert skills_count_1 == skills_count_2

    with parser_api["Session"]() as db:
        # Verify no duplicate associations in database
        db_skills = db.query(ResumeSkill).filter(ResumeSkill.resume_id == resume_id).all()
        assert len(db_skills) == skills_count_1


def test_parse_resume_other_candidate_gets_404(parser_api):
    client = parser_api["client"]
    # Switch active user to candidate2
    parser_api["active_user"]["id"] = parser_api["users"]["candidate2"]
    resume_id = parser_api["resumes"]["valid"]

    response = client.post(f"/resumes/{resume_id}/parse")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_parse_resume_recruiter_gets_403(parser_api):
    client = parser_api["client"]
    # Switch active user to recruiter
    parser_api["active_user"]["id"] = parser_api["users"]["recruiter1"]
    resume_id = parser_api["resumes"]["valid"]

    response = client.post(f"/resumes/{resume_id}/parse")
    assert response.status_code == 403


def test_parse_resume_corrupt_file_sets_failed_and_returns_422(parser_api):
    client = parser_api["client"]
    resume_id = parser_api["resumes"]["corrupt"]

    response = client.post(f"/resumes/{resume_id}/parse")
    assert response.status_code == 422

    with parser_api["Session"]() as db:
        db_resume = db.query(Resume).filter(Resume.id == resume_id).first()
        assert db_resume.parse_status == "failed"
        assert "error" in db_resume.parsed_json["meta"]

        audit = (
            db.query(AuditLog)
            .filter(AuditLog.entity_id == resume_id, AuditLog.action == "RESUME_PARSE_FAILED")
            .first()
        )
        assert audit is not None


def test_parse_resume_image_only_pdf_returns_no_extractable_text(parser_api):
    client = parser_api["client"]
    resume_id = parser_api["resumes"]["image"]

    response = client.post(f"/resumes/{resume_id}/parse")
    assert response.status_code == 422
    detail = response.json()["detail"].lower()
    assert "no extractable text" in detail

    with parser_api["Session"]() as db:
        db_resume = db.query(Resume).filter(Resume.id == resume_id).first()
        assert db_resume.parse_status == "failed"
        assert "no extractable text" in db_resume.parsed_json["meta"]["error"].lower()


def test_parse_resume_missing_file_sets_failed_and_returns_422(parser_api):
    client = parser_api["client"]
    resume_id = parser_api["resumes"]["missing"]

    response = client.post(f"/resumes/{resume_id}/parse")
    assert response.status_code == 422

    with parser_api["Session"]() as db:
        db_resume = db.query(Resume).filter(Resume.id == resume_id).first()
        assert db_resume.parse_status == "failed"


# ==============================================================================
# 2. GET PARSED RESUME (GET /resumes/{id}/parsed) TESTS
# ==============================================================================

def test_get_parsed_resume_by_owner(parser_api):
    client = parser_api["client"]
    resume_id = parser_api["resumes"]["valid"]

    # First parse
    client.post(f"/resumes/{resume_id}/parse")

    # Then retrieve parsed
    response = client.get(f"/resumes/{resume_id}/parsed")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == resume_id
    assert data["parse_status"] == "parsed"
    assert "file_path" not in data
    assert "raw_text" not in data
    assert len(data["skills"]) > 0


def test_get_parsed_resume_other_candidate_gets_404(parser_api):
    client = parser_api["client"]
    resume_id = parser_api["resumes"]["valid"]

    # Switch active user to candidate2
    parser_api["active_user"]["id"] = parser_api["users"]["candidate2"]
    response = client.get(f"/resumes/{resume_id}/parsed")
    assert response.status_code == 404


# ==============================================================================
# 3. RECRUITER APPLICATION DOSSIER INTEGRATION TESTS
# ==============================================================================

def test_recruiter_views_application_dossier_with_parsed_data(parser_api):
    client = parser_api["client"]
    resume_id = parser_api["resumes"]["valid"]
    app_id = parser_api["apps"]["app1"]

    # Candidate parses resume
    client.post(f"/resumes/{resume_id}/parse")

    # Switch to recruiter 1 (owns job1)
    parser_api["active_user"]["id"] = parser_api["users"]["recruiter1"]

    # Recruiter views application with reveal_contact=False (default)
    response = client.get(f"/applications/{app_id}?reveal_contact=false")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == app_id
    assert data["resume"] is not None
    assert data["resume"]["parse_status"] == "parsed"
    assert "file_path" not in data["resume"]
    assert "raw_text" not in data["resume"]

    # Skills detail is populated
    assert data["resume"]["skills"] is not None
    assert len(data["resume"]["skills"]) > 0

    # Privacy: Contact details MUST be hidden when reveal_contact=False
    assert data["email"] is None
    assert data["phone"] is None
    # Contact inside parsed_json must also be redacted
    parsed_contact = data["resume"]["parsed_json"]["contact"]
    assert parsed_contact["email"] is None
    assert parsed_contact["phone"] is None


def test_recruiter_reveal_contact_privacy_workflow(parser_api):
    client = parser_api["client"]
    resume_id = parser_api["resumes"]["valid"]
    app_id = parser_api["apps"]["app1"]

    # Candidate parses resume
    client.post(f"/resumes/{resume_id}/parse")

    # Switch to recruiter 1
    parser_api["active_user"]["id"] = parser_api["users"]["recruiter1"]

    # Recruiter requests contact reveal
    response = client.get(f"/applications/{app_id}?reveal_contact=true")
    assert response.status_code == 200

    data = response.json()
    assert data["email"] == "candidate1@example.com"
    assert data["phone"] == "+91 99999 11111"

    with parser_api["Session"]() as db:
        # Verify CONTACT_REVEALED audit event recorded without plain contact data
        audit = (
            db.query(AuditLog)
            .filter(AuditLog.entity_id == app_id, AuditLog.action == "CONTACT_REVEALED")
            .first()
        )
        assert audit is not None
        assert "candidate1@example.com" not in str(audit.details)


def test_unauthorized_recruiter_cannot_view_application(parser_api):
    client = parser_api["client"]
    app_id = parser_api["apps"]["app1"]

    # Switch to recruiter 2 (does NOT own job1)
    parser_api["active_user"]["id"] = parser_api["users"]["recruiter2"]

    response = client.get(f"/applications/{app_id}")
    assert response.status_code == 404

