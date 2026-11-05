"""
Unit and integration tests for recruiter statistics endpoint:
GET /recruiters/me/stats
"""

from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_current_user
from app.database import Base, get_db
from app.main import app
from app.models.job import Application, Job, RecruiterReview
from app.models.user import CandidateProfile, RecruiterProfile, User


@pytest.fixture
def stats_api():
    """
    Isolated test environment for recruiter stats endpoint.
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

    base_time = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)

    with TestingSessionLocal() as db:
        # Create users
        recruiter1 = User(
            email="recruiter1@test.example",
            password_hash="hash-rec1",
            full_name="Recruiter One",
            role="recruiter",
            is_active=True,
        )
        recruiter2 = User(
            email="recruiter2@test.example",
            password_hash="hash-rec2",
            full_name="Recruiter Two",
            role="recruiter",
            is_active=True,
        )
        recruiter_empty = User(
            email="empty_recruiter@test.example",
            password_hash="hash-rec-empty",
            full_name="Recruiter Empty",
            role="recruiter",
            is_active=True,
        )
        candidate1 = User(
            email="candidate1@test.example",
            password_hash="hash-cand1",
            full_name="Alice Candidate",
            role="candidate",
            is_active=True,
        )
        candidate2 = User(
            email="candidate2@test.example",
            password_hash="hash-cand2",
            full_name="Bob Candidate",
            role="candidate",
            is_active=True,
        )
        candidate3 = User(
            email="candidate3@test.example",
            password_hash="hash-cand3",
            full_name="Charlie Candidate",
            role="candidate",
            is_active=True,
        )
        candidate4 = User(
            email="candidate4@test.example",
            password_hash="hash-cand4",
            full_name="Diana Candidate",
            role="candidate",
            is_active=True,
        )

        db.add_all([
            recruiter1,
            recruiter2,
            recruiter_empty,
            candidate1,
            candidate2,
            candidate3,
            candidate4,
        ])
        db.commit()

        # Recruiter Profiles
        db.add_all([
            RecruiterProfile(user_id=recruiter1.id, company_name="Company Alpha"),
            RecruiterProfile(user_id=recruiter2.id, company_name="Company Beta"),
            RecruiterProfile(user_id=recruiter_empty.id, company_name="Company Empty"),
            CandidateProfile(user_id=candidate1.id, phone="111-1111", consent_given_at=base_time),
            CandidateProfile(user_id=candidate2.id, phone="222-2222", consent_given_at=base_time),
            CandidateProfile(user_id=candidate3.id, phone="333-3333", consent_given_at=base_time),
            CandidateProfile(user_id=candidate4.id, phone="444-4444", consent_given_at=base_time),
        ])
        db.commit()

        # Jobs for Recruiter 1
        job_r1_open1 = Job(
            recruiter_id=recruiter1.id,
            title="Senior Python Backend Engineer",
            description="Build scalable APIs",
            min_experience_years=4,
            status="open",
            created_at=base_time,
        )
        job_r1_open2 = Job(
            recruiter_id=recruiter1.id,
            title="Frontend React Specialist",
            description="Build modern UIs",
            min_experience_years=3,
            status="open",
            created_at=base_time + timedelta(hours=1),
        )
        job_r1_closed = Job(
            recruiter_id=recruiter1.id,
            title="Legacy Maintenance Dev",
            description="Maintain legacy systems",
            min_experience_years=2,
            status="closed",
            created_at=base_time + timedelta(hours=2),
        )

        # Job for Recruiter 2
        job_r2_open = Job(
            recruiter_id=recruiter2.id,
            title="Data Scientist",
            description="Machine learning and statistics",
            min_experience_years=5,
            status="open",
            created_at=base_time + timedelta(hours=3),
        )

        db.add_all([job_r1_open1, job_r1_open2, job_r1_closed, job_r2_open])
        db.commit()

        # Applications for Recruiter 1's jobs:
        # App 1: Candidate 1 -> Job R1 Open 1 (reviewed: shortlist then reject -> latest is reject)
        app1 = Application(
            candidate_id=candidate1.id,
            job_id=job_r1_open1.id,
            status="reviewed",
            created_at=base_time + timedelta(hours=4),
        )
        # App 2: Candidate 2 -> Job R1 Open 1 (reviewed: hold then shortlist -> latest is shortlist)
        app2 = Application(
            candidate_id=candidate2.id,
            job_id=job_r1_open1.id,
            status="reviewed",
            created_at=base_time + timedelta(hours=5),
        )
        # App 3: Candidate 3 -> Job R1 Closed (reviewed: hold -> latest is hold)
        app3 = Application(
            candidate_id=candidate3.id,
            job_id=job_r1_closed.id,
            status="reviewed",
            created_at=base_time + timedelta(hours=6),
        )
        # App 4: Candidate 4 -> Job R1 Open 1 (not reviewed: status applied)
        app4 = Application(
            candidate_id=candidate4.id,
            job_id=job_r1_open1.id,
            status="applied",
            created_at=base_time + timedelta(hours=7),
        )

        # Note: job_r1_open2 has 0 applications.

        # Applications for Recruiter 2's jobs:
        # App 5: Candidate 1 -> Job R2 Open (reviewed: shortlist)
        app5 = Application(
            candidate_id=candidate1.id,
            job_id=job_r2_open.id,
            status="reviewed",
            created_at=base_time + timedelta(hours=8),
        )
        # App 6: Candidate 2 -> Job R2 Open (status applied)
        app6 = Application(
            candidate_id=candidate2.id,
            job_id=job_r2_open.id,
            status="applied",
            created_at=base_time + timedelta(hours=9),
        )

        db.add_all([app1, app2, app3, app4, app5, app6])
        db.commit()

        # Reviews for Recruiter 1
        # App 1 was shortlisted, then later rejected
        rev1_app1 = RecruiterReview(
            application_id=app1.id,
            recruiter_id=recruiter1.id,
            decision="shortlist",
            notes="Initial shortlist",
            created_at=base_time + timedelta(hours=10),
        )
        rev2_app1 = RecruiterReview(
            application_id=app1.id,
            recruiter_id=recruiter1.id,
            decision="reject",
            notes="Overridden to reject after consideration",
            created_at=base_time + timedelta(hours=11),
        )
        # App 2 was held, then later shortlisted
        rev1_app2 = RecruiterReview(
            application_id=app2.id,
            recruiter_id=recruiter1.id,
            decision="hold",
            notes="Initial hold",
            created_at=base_time + timedelta(hours=12),
        )
        rev2_app2 = RecruiterReview(
            application_id=app2.id,
            recruiter_id=recruiter1.id,
            decision="shortlist",
            notes="Promoted to shortlist",
            created_at=base_time + timedelta(hours=13),
        )
        # App 3 was held
        rev1_app3 = RecruiterReview(
            application_id=app3.id,
            recruiter_id=recruiter1.id,
            decision="hold",
            notes="Candidate on hold",
            created_at=base_time + timedelta(hours=14),
        )

        # Review for Recruiter 2
        rev1_app5 = RecruiterReview(
            application_id=app5.id,
            recruiter_id=recruiter2.id,
            decision="shortlist",
            notes="Recruiter 2 shortlist",
            created_at=base_time + timedelta(hours=15),
        )

        db.add_all([rev1_app1, rev2_app1, rev1_app2, rev2_app2, rev1_app3, rev1_app5])
        db.commit()

        user_ids = {
            "recruiter1": recruiter1.id,
            "recruiter2": recruiter2.id,
            "recruiter_empty": recruiter_empty.id,
            "candidate1": candidate1.id,
        }
        job_ids = {
            "r1_open1": job_r1_open1.id,
            "r1_open2": job_r1_open2.id,
            "r1_closed": job_r1_closed.id,
            "r2_open": job_r2_open.id,
        }

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
            "job_ids": job_ids,
            "session_factory": TestingSessionLocal,
            "base_time": base_time,
        }

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_unauthenticated_stats_returns_401(stats_api):
    """Unauthenticated requests must return HTTP 401."""
    client = stats_api["client"]
    stats_api["auth_enabled"]["enabled"] = False

    resp = client.get("/recruiters/me/stats")
    assert resp.status_code == 401


def test_candidate_access_stats_returns_403(stats_api):
    """Candidate attempting to access recruiter stats must return HTTP 403."""
    client = stats_api["client"]
    stats_api["active_user"]["id"] = stats_api["user_ids"]["candidate1"]

    resp = client.get("/recruiters/me/stats")
    assert resp.status_code == 403


def test_empty_recruiter_stats_returns_zeroes(stats_api):
    """
    Recruiter with no jobs and no applications receives clean zero counts
    and empty lists without error.
    """
    client = stats_api["client"]
    stats_api["active_user"]["id"] = stats_api["user_ids"]["recruiter_empty"]

    resp = client.get("/recruiters/me/stats")
    assert resp.status_code == 200
    data = resp.json()

    assert data["active_jobs"] == 0
    assert data["closed_jobs"] == 0
    assert data["total_applications"] == 0
    assert data["awaiting_review"] == 0
    assert data["shortlisted"] == 0
    assert data["on_hold"] == 0
    assert data["rejected"] == 0
    assert data["applications_per_job"] == []
    assert data["recent_applications"] == []


def test_recruiter_stats_correct_counts_and_isolation(stats_api):
    """
    Verify complete and accurate stats calculation for recruiter1:
    - active_jobs = 2, closed_jobs = 1
    - total_applications = 4
    - awaiting_review = 1 (app4 has status 'applied')
    - shortlisted = 1 (app2 promoted to shortlist)
    - on_hold = 1 (app3 held)
    - rejected = 1 (app1 was shortlist then reject; latest decision override takes effect)
    - applications_per_job includes all jobs with correct counts (including 0 for job_r1_open2)
    - recent_applications has 4 items in reverse chronological order
    - Recruiter 2 data is completely excluded
    """
    client = stats_api["client"]
    stats_api["active_user"]["id"] = stats_api["user_ids"]["recruiter1"]

    resp = client.get("/recruiters/me/stats")
    assert resp.status_code == 200
    data = resp.json()

    assert data["active_jobs"] == 2
    assert data["closed_jobs"] == 1
    assert data["total_applications"] == 4
    assert data["awaiting_review"] == 1
    assert data["shortlisted"] == 1
    assert data["on_hold"] == 1
    assert data["rejected"] == 1

    # Check applications_per_job
    apps_per_job = data["applications_per_job"]
    assert len(apps_per_job) == 3

    # Find by job_id
    counts_map = {item["job_id"]: item for item in apps_per_job}
    assert stats_api["job_ids"]["r1_open1"] in counts_map
    assert stats_api["job_ids"]["r1_open2"] in counts_map
    assert stats_api["job_ids"]["r1_closed"] in counts_map

    assert counts_map[stats_api["job_ids"]["r1_open1"]]["count"] == 3
    assert counts_map[stats_api["job_ids"]["r1_open2"]]["count"] == 0
    assert counts_map[stats_api["job_ids"]["r1_closed"]]["count"] == 1

    # Recruiter 2's job must not be in applications_per_job
    assert stats_api["job_ids"]["r2_open"] not in counts_map

    # Check recent_applications
    recent = data["recent_applications"]
    assert len(recent) == 4

    # App 4 is latest, followed by App 3, App 2, App 1
    assert recent[0]["candidate_name"] == "Diana Candidate"
    assert recent[0]["job_title"] == "Senior Python Backend Engineer"
    assert recent[0]["status"] == "applied"
    assert "applied_at" in recent[0]

    assert recent[1]["candidate_name"] == "Charlie Candidate"
    assert recent[1]["job_title"] == "Legacy Maintenance Dev"
    assert recent[1]["status"] == "reviewed"

    assert recent[2]["candidate_name"] == "Bob Candidate"
    assert recent[3]["candidate_name"] == "Alice Candidate"


def test_recruiter2_stats_isolation(stats_api):
    """
    Verify recruiter2 sees only their own data:
    - active_jobs = 1, closed_jobs = 0
    - total_applications = 2
    - awaiting_review = 1 (app6 has status 'applied')
    - shortlisted = 1 (app5 has review 'shortlist')
    - on_hold = 0
    - rejected = 0
    - applications_per_job has 1 item
    """
    client = stats_api["client"]
    stats_api["active_user"]["id"] = stats_api["user_ids"]["recruiter2"]

    resp = client.get("/recruiters/me/stats")
    assert resp.status_code == 200
    data = resp.json()

    assert data["active_jobs"] == 1
    assert data["closed_jobs"] == 0
    assert data["total_applications"] == 2
    assert data["awaiting_review"] == 1
    assert data["shortlisted"] == 1
    assert data["on_hold"] == 0
    assert data["rejected"] == 0

    assert len(data["applications_per_job"]) == 1
    assert data["applications_per_job"][0]["job_id"] == stats_api["job_ids"]["r2_open"]
    assert data["applications_per_job"][0]["count"] == 2

    assert len(data["recent_applications"]) == 2


def test_recent_applications_capped_at_five(stats_api):
    """
    Verify recent_applications is capped at 5 even when more applications exist.
    """
    TestingSessionLocal = stats_api["session_factory"]
    base_time = stats_api["base_time"]
    rec1_id = stats_api["user_ids"]["recruiter1"]
    job1_id = stats_api["job_ids"]["r1_open1"]

    # Add 4 more candidates and applications to job1
    with TestingSessionLocal() as db:
        new_cands = []
        for i in range(10, 14):
            c = User(
                email=f"extra{i}@test.example",
                password_hash="hash",
                full_name=f"Extra Candidate {i}",
                role="candidate",
                is_active=True,
            )
            new_cands.append(c)
        db.add_all(new_cands)
        db.commit()

        for idx, c in enumerate(new_cands):
            app = Application(
                candidate_id=c.id,
                job_id=job1_id,
                status="applied",
                created_at=base_time + timedelta(days=1, hours=idx),
            )
            db.add(app)
        db.commit()

    client = stats_api["client"]
    stats_api["active_user"]["id"] = rec1_id

    resp = client.get("/recruiters/me/stats")
    assert resp.status_code == 200
    data = resp.json()

    # Total applications is now 4 + 4 = 8
    assert data["total_applications"] == 8
    # recent_applications is capped at 5
    assert len(data["recent_applications"]) == 5

