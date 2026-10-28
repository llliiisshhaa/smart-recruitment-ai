"""
Tests for Stage 7: Skill taxonomy, Recruiter profiles, and Job management.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.core.dependencies import get_current_user
from app.database import Base, get_db
from app.main import app
from app.models import AuditLog, Job, RecruiterProfile, Skill, User


@pytest.fixture
def job_api(tmp_path, monkeypatch):
    """
    Isolated test environment for jobs, recruiter profiles, and skill endpoints.
    Uses in-memory SQLite database.
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
        # Create test users
        candidate = User(
            email="candidate@test.example",
            password_hash="test-hash",
            full_name="Candidate User",
            role="candidate",
            is_active=True,
        )
        recruiter_one = User(
            email="recruiter1@test.example",
            password_hash="test-hash",
            full_name="Recruiter One",
            role="recruiter",
            is_active=True,
        )
        recruiter_two = User(
            email="recruiter2@test.example",
            password_hash="test-hash",
            full_name="Recruiter Two",
            role="recruiter",
            is_active=True,
        )
        db.add_all([candidate, recruiter_one, recruiter_two])
        db.commit()

        # Seed skills
        skills_data = [
            ("python", "Programming Language"),
            ("fastapi", "Framework"),
            ("postgresql", "Database"),
            ("docker", "DevOps"),
            ("react", "Frontend"),
        ]
        skill_objects = [Skill(name=name, category=cat) for name, cat in skills_data]
        db.add_all(skill_objects)
        db.commit()

        db.refresh(candidate)
        db.refresh(recruiter_one)
        db.refresh(recruiter_two)

        user_ids = {
            "candidate": candidate.id,
            "recruiter1": recruiter_one.id,
            "recruiter2": recruiter_two.id,
        }

        skill_ids = {s.name: s.id for s in db.query(Skill).all()}

    active_user = {"id": user_ids["recruiter1"]}
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
            "skill_ids": skill_ids,
            "session_factory": TestingSessionLocal,
        }

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_unauthenticated_requests_return_401(job_api):
    client = job_api["client"]
    job_api["auth_enabled"]["enabled"] = False

    assert client.get("/skills").status_code == 401
    assert client.get("/recruiters/me").status_code == 401
    assert client.get("/jobs").status_code == 401
    assert client.post("/jobs", json={}).status_code == 401
    assert client.get("/jobs/mine").status_code == 401


def test_skill_search_and_maximum_result_count(job_api):
    client = job_api["client"]
    # Seed > 50 additional skills to test capping
    with job_api["session_factory"]() as db:
        extra_skills = [
            Skill(name=f"test_skill_{i:03d}", category="Test")
            for i in range(60)
        ]
        db.add_all(extra_skills)
        db.commit()

    # Default list capped at 50
    res = client.get("/skills")
    assert res.status_code == 200
    skills = res.json()
    assert len(skills) == 50
    # Deterministic alphabetical ordering
    names = [s["name"] for s in skills]
    assert names == sorted(names)

    # Substring search (case-insensitive)
    search_res = client.get("/skills?q=PYTHON")
    assert search_res.status_code == 200
    items = search_res.json()
    assert len(items) == 1
    assert items[0]["name"] == "python"
    assert items[0]["category"] == "Programming Language"
    assert "created_at" not in items[0]


def test_recruiter_profile_creation_and_update(job_api):
    client = job_api["client"]
    job_api["active_user"]["id"] = job_api["user_ids"]["recruiter1"]

    # Missing profile returns 200 cleanly with null values
    get_res = client.get("/recruiters/me")
    assert get_res.status_code == 200
    profile = get_res.json()
    assert profile["company_name"] is None
    assert profile["user_id"] == job_api["user_ids"]["recruiter1"]

    # Reject empty or whitespace company_name
    bad_res = client.put("/recruiters/me", json={"company_name": "   "})
    assert bad_res.status_code == 422

    # Successful creation
    put_res = client.put("/recruiters/me", json={"company_name": "Acme Corp"})
    assert put_res.status_code == 200
    assert put_res.json()["company_name"] == "Acme Corp"
    assert put_res.json()["id"] is not None

    # Subsequent GET returns profile
    get_res2 = client.get("/recruiters/me")
    assert get_res2.status_code == 200
    assert get_res2.json()["company_name"] == "Acme Corp"

    # Candidate forbidden from accessing recruiter profile
    job_api["active_user"]["id"] = job_api["user_ids"]["candidate"]
    assert client.get("/recruiters/me").status_code == 403


def test_job_creation_with_required_and_preferred_skills(job_api):
    client = job_api["client"]
    job_api["active_user"]["id"] = job_api["user_ids"]["recruiter1"]

    # Give recruiter a company name
    client.put("/recruiters/me", json={"company_name": "Tech Corp"})

    skills = job_api["skill_ids"]
    payload = {
        "title": "Backend Engineer",
        "description": "Build high-scale REST APIs.",
        "min_experience_years": 3,
        "education": "Bachelor's Degree",
        "skills": [
            {"skill_id": skills["python"], "importance": "required"},
            {"skill_id": skills["fastapi"], "importance": "preferred"},
        ],
    }

    res = client.post("/jobs", json=payload)
    assert res.status_code == 201, res.text
    job_data = res.json()
    assert job_data["title"] == "Backend Engineer"
    assert job_data["status"] == "open"
    assert job_data["company_name"] == "Tech Corp"
    assert len(job_data["skills"]) == 2

    # Verify audit log
    with job_api["session_factory"]() as db:
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == job_api["user_ids"]["recruiter1"],
                AuditLog.action == "JOB_CREATED",
            )
            .first()
        )
        assert audit is not None
        assert audit.entity_id == job_data["id"]


def test_job_creation_without_required_skill_fails(job_api):
    client = job_api["client"]
    job_api["active_user"]["id"] = job_api["user_ids"]["recruiter1"]
    skills = job_api["skill_ids"]

    payload = {
        "title": "Backend Engineer",
        "description": "Job with only preferred skills.",
        "min_experience_years": 2,
        "skills": [
            {"skill_id": skills["python"], "importance": "preferred"},
        ],
    }

    res = client.post("/jobs", json=payload)
    assert res.status_code == 422


def test_job_creation_with_invalid_skill_id_fails(job_api):
    client = job_api["client"]
    job_api["active_user"]["id"] = job_api["user_ids"]["recruiter1"]

    payload = {
        "title": "Backend Engineer",
        "description": "Job with nonexistent skill ID.",
        "min_experience_years": 1,
        "skills": [
            {"skill_id": 99999, "importance": "required"},
        ],
    }

    res = client.post("/jobs", json=payload)
    assert res.status_code == 400
    assert "skill IDs do not exist" in res.json()["detail"]


def test_job_creation_with_duplicate_skill_ids_fails(job_api):
    client = job_api["client"]
    job_api["active_user"]["id"] = job_api["user_ids"]["recruiter1"]
    skills = job_api["skill_ids"]

    payload = {
        "title": "Backend Engineer",
        "description": "Job with duplicate skills.",
        "min_experience_years": 1,
        "skills": [
            {"skill_id": skills["python"], "importance": "required"},
            {"skill_id": skills["python"], "importance": "preferred"},
        ],
    }

    res = client.post("/jobs", json=payload)
    assert res.status_code == 422


def test_candidate_cannot_create_jobs(job_api):
    client = job_api["client"]
    job_api["active_user"]["id"] = job_api["user_ids"]["candidate"]
    skills = job_api["skill_ids"]

    res = client.post(
        "/jobs",
        json={
            "title": "Candidate Job",
            "description": "Trying to post as candidate",
            "min_experience_years": 1,
            "skills": [{"skill_id": skills["python"], "importance": "required"}],
        },
    )
    assert res.status_code == 403


def test_recruiter_can_edit_own_job(job_api):
    client = job_api["client"]
    job_api["active_user"]["id"] = job_api["user_ids"]["recruiter1"]
    skills = job_api["skill_ids"]

    create_res = client.post(
        "/jobs",
        json={
            "title": "Original Title",
            "description": "Original description",
            "min_experience_years": 1,
            "skills": [{"skill_id": skills["python"], "importance": "required"}],
        },
    )
    job_id = create_res.json()["id"]

    # Update job
    update_res = client.put(
        f"/jobs/{job_id}",
        json={
            "title": "Updated Title",
            "description": "Updated description",
            "min_experience_years": 5,
            "skills": [
                {"skill_id": skills["fastapi"], "importance": "required"},
                {"skill_id": skills["docker"], "importance": "preferred"},
            ],
        },
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["title"] == "Updated Title"
    assert updated["min_experience_years"] == 5
    assert len(updated["skills"]) == 2

    with job_api["session_factory"]() as db:
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == job_api["user_ids"]["recruiter1"],
                AuditLog.action == "JOB_UPDATED",
            )
            .first()
        )
        assert audit is not None


def test_another_recruiter_cannot_edit_or_view_private_job(job_api):
    client = job_api["client"]
    job_api["active_user"]["id"] = job_api["user_ids"]["recruiter1"]
    skills = job_api["skill_ids"]

    create_res = client.post(
        "/jobs",
        json={
            "title": "Recruiter 1 Job",
            "description": "Confidential role",
            "min_experience_years": 2,
            "skills": [{"skill_id": skills["python"], "importance": "required"}],
        },
    )
    job_id = create_res.json()["id"]

    # Switch to recruiter 2
    job_api["active_user"]["id"] = job_api["user_ids"]["recruiter2"]

    # Recruiter 2 cannot view
    assert client.get(f"/jobs/{job_id}").status_code == 404

    # Recruiter 2 cannot edit
    assert client.put(
        f"/jobs/{job_id}",
        json={
            "title": "Hacked Title",
            "description": "Hacked description",
            "min_experience_years": 2,
            "skills": [{"skill_id": skills["python"], "importance": "required"}],
        },
    ).status_code == 404

    # Recruiter 2 cannot change status
    assert client.patch(
        f"/jobs/{job_id}/status",
        json={"status": "closed"},
    ).status_code == 404


def test_candidate_job_browsing_returns_open_jobs_only(job_api):
    client = job_api["client"]
    job_api["active_user"]["id"] = job_api["user_ids"]["recruiter1"]
    skills = job_api["skill_ids"]

    # Recruiter creates an open job
    job1_res = client.post(
        "/jobs",
        json={
            "title": "Open Python Role",
            "description": "Exciting opening",
            "min_experience_years": 2,
            "skills": [{"skill_id": skills["python"], "importance": "required"}],
        },
    )
    job1_id = job1_res.json()["id"]

    # Recruiter creates another job and closes it
    job2_res = client.post(
        "/jobs",
        json={
            "title": "Closed Python Role",
            "description": "This role is closed",
            "min_experience_years": 2,
            "skills": [{"skill_id": skills["python"], "importance": "required"}],
        },
    )
    job2_id = job2_res.json()["id"]
    client.patch(f"/jobs/{job2_id}/status", json={"status": "closed"})

    # Switch to candidate
    job_api["active_user"]["id"] = job_api["user_ids"]["candidate"]

    # Candidate browses jobs
    browse_res = client.get("/jobs")
    assert browse_res.status_code == 200
    data = browse_res.json()
    job_ids = [j["id"] for j in data["items"]]
    assert job1_id in job_ids
    assert job2_id not in job_ids

    # Candidate cannot view closed job directly (returns 404)
    assert client.get(f"/jobs/{job2_id}").status_code == 404

    # Candidate can view open job directly
    open_res = client.get(f"/jobs/{job1_id}")
    assert open_res.status_code == 200
    assert open_res.json()["title"] == "Open Python Role"
    assert "email" not in str(open_res.json())

    # Title search
    search_res = client.get("/jobs?q=Nonexistent")
    assert search_res.status_code == 200
    assert len(search_res.json()["items"]) == 0


def test_recruiter_can_view_own_closed_job_and_list_mine(job_api):
    client = job_api["client"]
    job_api["active_user"]["id"] = job_api["user_ids"]["recruiter1"]
    skills = job_api["skill_ids"]

    create_res = client.post(
        "/jobs",
        json={
            "title": "Role to close",
            "description": "Closing shortly",
            "min_experience_years": 1,
            "skills": [{"skill_id": skills["python"], "importance": "required"}],
        },
    )
    job_id = create_res.json()["id"]

    # Close job
    patch_res = client.patch(f"/jobs/{job_id}/status", json={"status": "closed"})
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "closed"

    # Recruiter can still view own closed job
    get_res = client.get(f"/jobs/{job_id}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "closed"

    # List own jobs
    mine_res = client.get("/jobs/mine")
    assert mine_res.status_code == 200
    mine_ids = [j["id"] for j in mine_res.json()]
    assert job_id in mine_ids
