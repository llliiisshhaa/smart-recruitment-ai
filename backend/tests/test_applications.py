"""
Tests for Stage 7: Applications, Recruiter Applicant Access, Privacy Controls,
Resume Downloads, and Human Review Decisions.
"""

from datetime import datetime, timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
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
    JobSkill,
    RecruiterProfile,
    RecruiterReview,
    Resume,
    Skill,
    User,
)


@pytest.fixture
def app_api(tmp_path, monkeypatch):
    """
    Isolated test environment for candidate applications and recruiter reviews.
    Uses in-memory SQLite database and isolated file storage.
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
        # Users
        candidate1 = User(
            email="candidate1@test.example",
            password_hash="test-hash",
            full_name="Candidate One",
            role="candidate",
            is_active=True,
        )
        candidate2 = User(
            email="candidate2@test.example",
            password_hash="test-hash",
            full_name="Candidate Two",
            role="candidate",
            is_active=True,
        )
        candidate_no_consent = User(
            email="noconsent@test.example",
            password_hash="test-hash",
            full_name="No Consent Candidate",
            role="candidate",
            is_active=True,
        )
        recruiter1 = User(
            email="recruiter1@test.example",
            password_hash="test-hash",
            full_name="Recruiter One",
            role="recruiter",
            is_active=True,
        )
        recruiter2 = User(
            email="recruiter2@test.example",
            password_hash="test-hash",
            full_name="Recruiter Two",
            role="recruiter",
            is_active=True,
        )
        db.add_all([candidate1, candidate2, candidate_no_consent, recruiter1, recruiter2])
        db.commit()

        # Profiles
        p1 = CandidateProfile(
            user_id=candidate1.id,
            phone="+1234567890",
            headline="Python Backend Engineer",
            location="Remote",
            consent_given_at=datetime.now(timezone.utc),
        )
        p2 = CandidateProfile(
            user_id=candidate2.id,
            phone="+9876543210",
            headline="Frontend Developer",
            location="New York",
            consent_given_at=datetime.now(timezone.utc),
        )
        p3 = CandidateProfile(
            user_id=candidate_no_consent.id,
            consent_given_at=None,
        )
        rp1 = RecruiterProfile(
            user_id=recruiter1.id,
            company_name="Alpha Tech",
        )
        rp2 = RecruiterProfile(
            user_id=recruiter2.id,
            company_name="Beta Corp",
        )
        db.add_all([p1, p2, p3, rp1, rp2])
        db.commit()

        # Skills
        py_skill = Skill(name="python", category="Programming Language")
        db.add(py_skill)
        db.commit()

        # Jobs
        job_open = Job(
            recruiter_id=recruiter1.id,
            title="Senior Python Developer",
            description="Open backend role",
            min_experience_years=3,
            status="open",
        )
        job_closed = Job(
            recruiter_id=recruiter1.id,
            title="Archived Python Role",
            description="Closed role",
            min_experience_years=2,
            status="closed",
        )
        job_rec2 = Job(
            recruiter_id=recruiter2.id,
            title="Recruiter 2 Job",
            description="Private to Recruiter 2",
            min_experience_years=1,
            status="open",
        )
        db.add_all([job_open, job_closed, job_rec2])
        db.commit()

        # Resumes on disk
        cand1_dir = upload_dir / str(candidate1.id)
        cand1_dir.mkdir(parents=True, exist_ok=True)
        resume1_file = cand1_dir / "resume1.pdf"
        resume1_file.write_bytes(b"%PDF-1.7\nCandidate 1 Resume\n%%EOF")

        resume1 = Resume(
            candidate_id=candidate1.id,
            file_path=str(resume1_file),
            original_filename="cand1_resume.pdf",
            parse_status="parsed",
            parsed_json={"skills": ["python", "docker"]},
        )

        cand2_dir = upload_dir / str(candidate2.id)
        cand2_dir.mkdir(parents=True, exist_ok=True)
        resume2_file = cand2_dir / "resume2.pdf"
        resume2_file.write_bytes(b"%PDF-1.7\nCandidate 2 Resume\n%%EOF")

        resume2 = Resume(
            candidate_id=candidate2.id,
            file_path=str(resume2_file),
            original_filename="cand2_resume.pdf",
            parse_status="pending",
        )

        db.add_all([resume1, resume2])
        db.commit()

        user_ids = {
            "candidate1": candidate1.id,
            "candidate2": candidate2.id,
            "candidate_no_consent": candidate_no_consent.id,
            "recruiter1": recruiter1.id,
            "recruiter2": recruiter2.id,
        }
        job_ids = {
            "open": job_open.id,
            "closed": job_closed.id,
            "rec2": job_rec2.id,
        }
        resume_ids = {
            "candidate1": resume1.id,
            "candidate2": resume2.id,
        }

    active_user = {"id": user_ids["candidate1"]}
    auth_enabled = {"enabled": True}

    def override_get_db():
        with TestingSessionLocal() as db:
            yield db

    def override_get_current_user(db=__import__("fastapi").Depends(override_get_db)):
        if not auth_enabled["enabled"] or active_user["id"] is None:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication credentials were not provided",
            )
        return db.query(User).filter(User.id == active_user["id"]).first()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as client:
        yield {
            "client": client,
            "active_user": active_user,
            "auth_enabled": auth_enabled,
            "user_ids": user_ids,
            "job_ids": job_ids,
            "resume_ids": resume_ids,
            "session_factory": TestingSessionLocal,
        }

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_unauthenticated_requests_return_401(app_api):
    client = app_api["client"]
    app_api["auth_enabled"]["enabled"] = False

    assert client.get("/applications/mine").status_code == 401
    assert client.post(f"/jobs/{app_api['job_ids']['open']}/apply", json={"resume_id": 1}).status_code == 401
    assert client.get(f"/jobs/{app_api['job_ids']['open']}/applications").status_code == 401
    assert client.get("/applications/1").status_code == 401
    assert client.get("/applications/1/resume").status_code == 401
    assert client.post("/applications/1/review", json={"decision": "shortlist"}).status_code == 401


def test_candidate_applies_with_own_resume(app_api):
    client = app_api["client"]
    app_api["active_user"]["id"] = app_api["user_ids"]["candidate1"]

    res = client.post(
        f"/jobs/{app_api['job_ids']['open']}/apply",
        json={"resume_id": app_api["resume_ids"]["candidate1"]},
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["job_id"] == app_api["job_ids"]["open"]
    assert data["status"] == "applied"
    app_id = data["id"]

    # Verify database state: match_score is None
    with app_api["session_factory"]() as db:
        app_record = db.query(Application).filter(Application.id == app_id).first()
        assert app_record.match_score is None
        assert app_record.match_breakdown is None

        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == app_api["user_ids"]["candidate1"],
                AuditLog.action == "APPLICATION_SUBMITTED",
            )
            .first()
        )
        assert audit is not None
        assert audit.entity_id == app_id


def test_applying_without_consent_fails(app_api):
    client = app_api["client"]
    app_api["active_user"]["id"] = app_api["user_ids"]["candidate_no_consent"]

    res = client.post(
        f"/jobs/{app_api['job_ids']['open']}/apply",
        json={"resume_id": app_api["resume_ids"]["candidate1"]},
    )
    assert res.status_code == 403
    assert "consent" in res.json()["detail"].lower()


def test_applying_with_another_candidates_resume_fails(app_api):
    client = app_api["client"]
    app_api["active_user"]["id"] = app_api["user_ids"]["candidate1"]

    # Attempt to use candidate 2's resume
    res = client.post(
        f"/jobs/{app_api['job_ids']['open']}/apply",
        json={"resume_id": app_api["resume_ids"]["candidate2"]},
    )
    assert res.status_code == 404


def test_applying_to_closed_or_nonexistent_job_fails(app_api):
    client = app_api["client"]
    app_api["active_user"]["id"] = app_api["user_ids"]["candidate1"]

    # Nonexistent job
    res_404 = client.post(
        "/jobs/99999/apply",
        json={"resume_id": app_api["resume_ids"]["candidate1"]},
    )
    assert res_404.status_code == 404

    # Closed job
    res_closed = client.post(
        f"/jobs/{app_api['job_ids']['closed']}/apply",
        json={"resume_id": app_api["resume_ids"]["candidate1"]},
    )
    assert res_closed.status_code == 400


def test_duplicate_applications_return_409(app_api):
    client = app_api["client"]
    app_api["active_user"]["id"] = app_api["user_ids"]["candidate1"]

    first_res = client.post(
        f"/jobs/{app_api['job_ids']['open']}/apply",
        json={"resume_id": app_api["resume_ids"]["candidate1"]},
    )
    assert first_res.status_code == 201

    # Second application must return 409
    second_res = client.post(
        f"/jobs/{app_api['job_ids']['open']}/apply",
        json={"resume_id": app_api["resume_ids"]["candidate1"]},
    )
    assert second_res.status_code == 409


def test_candidate_sees_only_own_applications(app_api):
    client = app_api["client"]
    app_api["active_user"]["id"] = app_api["user_ids"]["candidate1"]

    # Candidate 1 applies
    client.post(
        f"/jobs/{app_api['job_ids']['open']}/apply",
        json={"resume_id": app_api["resume_ids"]["candidate1"]},
    )

    # Candidate 1 lists applications
    c1_apps = client.get("/applications/mine").json()
    assert len(c1_apps) == 1
    assert c1_apps[0]["job_title"] == "Senior Python Developer"
    assert c1_apps[0]["status"] == "applied"

    # Candidate 2 lists applications
    app_api["active_user"]["id"] = app_api["user_ids"]["candidate2"]
    c2_apps = client.get("/applications/mine").json()
    assert len(c2_apps) == 0


def test_recruiter_applicant_list_privacy_and_cross_isolation(app_api):
    client = app_api["client"]
    # Candidate 1 applies
    app_api["active_user"]["id"] = app_api["user_ids"]["candidate1"]
    client.post(
        f"/jobs/{app_api['job_ids']['open']}/apply",
        json={"resume_id": app_api["resume_ids"]["candidate1"]},
    )

    # Recruiter 1 checks applicants
    app_api["active_user"]["id"] = app_api["user_ids"]["recruiter1"]
    res = client.get(f"/jobs/{app_api['job_ids']['open']}/applications")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["candidate_name"] == "Candidate One"
    assert item["headline"] == "Python Backend Engineer"
    assert item["status"] == "applied"
    assert item["latest_review_decision"] is None
    # Crucial privacy requirement: NO email or phone in list
    assert "email" not in item
    assert "phone" not in item

    # Recruiter 2 cannot see Recruiter 1's applicants
    app_api["active_user"]["id"] = app_api["user_ids"]["recruiter2"]
    res_rec2 = client.get(f"/jobs/{app_api['job_ids']['open']}/applications")
    assert res_rec2.status_code == 404


def test_applicant_detail_contact_hidden_by_default_and_revealed(app_api):
    client = app_api["client"]
    # Candidate 1 applies
    app_api["active_user"]["id"] = app_api["user_ids"]["candidate1"]
    apply_res = client.post(
        f"/jobs/{app_api['job_ids']['open']}/apply",
        json={"resume_id": app_api["resume_ids"]["candidate1"]},
    )
    application_id = apply_res.json()["id"]

    # Recruiter 1 views detail (default: contact hidden)
    app_api["active_user"]["id"] = app_api["user_ids"]["recruiter1"]
    detail_res = client.get(f"/applications/{application_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["candidate_name"] == "Candidate One"
    assert detail["email"] is None
    assert detail["phone"] is None
    # Resume metadata present, file_path and raw_text omitted
    assert detail["resume"]["original_filename"] == "cand1_resume.pdf"
    assert "file_path" not in str(detail)
    assert "raw_text" not in str(detail)

    # Recruiter 2 tries to view detail -> 404
    app_api["active_user"]["id"] = app_api["user_ids"]["recruiter2"]
    assert client.get(f"/applications/{application_id}").status_code == 404

    # Recruiter 1 reveals contact
    app_api["active_user"]["id"] = app_api["user_ids"]["recruiter1"]
    reveal_res = client.get(f"/applications/{application_id}?reveal_contact=true")
    assert reveal_res.status_code == 200
    revealed = reveal_res.json()
    assert revealed["email"] == "candidate1@test.example"
    assert revealed["phone"] == "+1234567890"

    # Verify audit log for contact revealed (without logging sensitive details)
    with app_api["session_factory"]() as db:
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == app_api["user_ids"]["recruiter1"],
                AuditLog.action == "CONTACT_REVEALED",
            )
            .first()
        )
        assert audit is not None
        assert audit.entity_id == application_id
        # Confirm candidate email or phone is NOT in audit log details
        assert "candidate1@test.example" not in str(audit.details)
        assert "+1234567890" not in str(audit.details)


def test_recruiter_resume_download_and_isolation(app_api):
    client = app_api["client"]
    # Candidate 1 applies
    app_api["active_user"]["id"] = app_api["user_ids"]["candidate1"]
    apply_res = client.post(
        f"/jobs/{app_api['job_ids']['open']}/apply",
        json={"resume_id": app_api["resume_ids"]["candidate1"]},
    )
    application_id = apply_res.json()["id"]

    # Recruiter 2 cannot download resume
    app_api["active_user"]["id"] = app_api["user_ids"]["recruiter2"]
    assert client.get(f"/applications/{application_id}/resume").status_code == 404

    # Recruiter 1 downloads resume
    app_api["active_user"]["id"] = app_api["user_ids"]["recruiter1"]
    dl_res = client.get(f"/applications/{application_id}/resume")
    assert dl_res.status_code == 200
    assert dl_res.content.startswith(b"%PDF-")

    # Verify audit log
    with app_api["session_factory"]() as db:
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == app_api["user_ids"]["recruiter1"],
                AuditLog.action == "RESUME_VIEWED_BY_RECRUITER",
            )
            .first()
        )
        assert audit is not None


def test_review_submission_updates_status_and_preserves_history(app_api):
    client = app_api["client"]
    # Candidate 1 applies
    app_api["active_user"]["id"] = app_api["user_ids"]["candidate1"]
    apply_res = client.post(
        f"/jobs/{app_api['job_ids']['open']}/apply",
        json={"resume_id": app_api["resume_ids"]["candidate1"]},
    )
    application_id = apply_res.json()["id"]

    # Recruiter 2 cannot review
    app_api["active_user"]["id"] = app_api["user_ids"]["recruiter2"]
    assert client.post(
        f"/applications/{application_id}/review",
        json={"decision": "shortlist", "notes": "Hacker note"},
    ).status_code == 404

    # Recruiter 1 submits first review: hold
    app_api["active_user"]["id"] = app_api["user_ids"]["recruiter1"]
    rev1_res = client.post(
        f"/applications/{application_id}/review",
        json={"decision": "hold", "notes": "Needs more background checks."},
    )
    assert rev1_res.status_code == 201
    assert rev1_res.json()["decision"] == "hold"

    # Application status is updated to 'reviewed'
    with app_api["session_factory"]() as db:
        app_record = db.query(Application).filter(Application.id == application_id).first()
        assert app_record.status == "reviewed"

        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == app_api["user_ids"]["recruiter1"],
                AuditLog.action == "REVIEW_SUBMITTED",
            )
            .first()
        )
        assert audit is not None
        assert audit.details["decision"] == "hold"

    # Recruiter 1 submits second review: shortlist (preserves review history)
    rev2_res = client.post(
        f"/applications/{application_id}/review",
        json={"decision": "shortlist", "notes": "Candidate passed background check."},
    )
    assert rev2_res.status_code == 201
    assert rev2_res.json()["decision"] == "shortlist"

    # Verify both reviews exist in applicant detail
    detail_res = client.get(f"/applications/{application_id}")
    assert detail_res.status_code == 200
    reviews = detail_res.json()["reviews"]
    assert len(reviews) == 2
    assert reviews[0]["decision"] == "hold"
    assert reviews[1]["decision"] == "shortlist"

    # Verify applicant list shows latest review decision
    list_res = client.get(f"/jobs/{app_api['job_ids']['open']}/applications")
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert items[0]["latest_review_decision"] == "shortlist"
