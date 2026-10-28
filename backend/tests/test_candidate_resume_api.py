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
from app.models import AuditLog, User


@pytest.fixture
def api(tmp_path, monkeypatch):
    """
    Create an isolated API test environment.

    - Uses an in-memory SQLite database.
    - Creates separate candidate and recruiter accounts.
    - Stores uploaded files in a temporary directory.
    - Does not access the development PostgreSQL database.
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

    # Importing app.models registers all model classes.
    Base.metadata.create_all(bind=engine)

    # Use temporary storage and a 1 MB upload limit for testing.
    upload_directory = tmp_path / "test_uploads"
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload_directory))
    monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 1)

    with TestingSessionLocal() as db:
        candidate_one = User(
            email="candidate1@test.example",
            password_hash="test-only-hash",
            full_name="Candidate One",
            role="candidate",
            is_active=True,
        )

        candidate_two = User(
            email="candidate2@test.example",
            password_hash="test-only-hash",
            full_name="Candidate Two",
            role="candidate",
            is_active=True,
        )

        recruiter = User(
            email="recruiter@test.example",
            password_hash="test-only-hash",
            full_name="Test Recruiter",
            role="recruiter",
            is_active=True,
        )

        db.add_all([candidate_one, candidate_two, recruiter])
        db.commit()

        db.refresh(candidate_one)
        db.refresh(candidate_two)
        db.refresh(recruiter)

        user_ids = {
            "candidate1": candidate_one.id,
            "candidate2": candidate_two.id,
            "recruiter": recruiter.id,
        }

    # Change this value to simulate another authenticated user.
    active_user = {"id": user_ids["candidate1"]}

    def override_get_db():
        with TestingSessionLocal() as db:
            yield db

    def override_get_current_user(db=__import__("fastapi").Depends(override_get_db)):
        return db.query(User).filter(
            User.id == active_user["id"]
        ).first()

    # Override authentication and database dependencies for API requests.
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as client:
        yield {
            "client": client,
            "active_user": active_user,
            "user_ids": user_ids,
            "session_factory": TestingSessionLocal,
            "upload_directory": upload_directory,
        }

    # Always clean up dependency overrides and the test database.
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def give_consent(client):
    response = client.post("/candidates/me/consent")
    assert response.status_code == 200, response.text
    return response.json()


def upload_test_pdf(client, filename="resume.pdf", content=None):
    """Upload a small PDF-like test payload."""

    if content is None:
        content = b"%PDF-1.7\nTest resume content\n%%EOF"

    return client.post(
        "/resumes",
        files={
            "file": (
                filename,
                content,
                "application/pdf",
            )
        },
    )


def test_candidate_profile_can_be_created_and_updated(api):
    client = api["client"]

    # A profile should be created when the candidate first requests it.
    response = client.get("/candidates/me")

    assert response.status_code == 200, response.text
    profile = response.json()
    assert profile["user_id"] == api["user_ids"]["candidate1"]

    # Update candidate profile information.
    response = client.put(
        "/candidates/me",
        json={
            "phone": "9876543210",
            "headline": "Aspiring Software Engineer",
            "location": "Bengaluru",
        },
    )

    assert response.status_code == 200, response.text

    updated_profile = response.json()
    assert updated_profile["phone"] == "9876543210"
    assert updated_profile["headline"] == "Aspiring Software Engineer"
    assert updated_profile["location"] == "Bengaluru"


def test_consent_is_recorded_only_once(api):
    client = api["client"]

    first_response = client.post("/candidates/me/consent")
    assert first_response.status_code == 200, first_response.text

    first_timestamp = first_response.json()["consent_given_at"]
    assert first_timestamp is not None

    # Giving consent again must not replace the original timestamp.
    second_response = client.post("/candidates/me/consent")
    assert second_response.status_code == 200, second_response.text

    second_timestamp = second_response.json()["consent_given_at"]
    assert second_timestamp == first_timestamp

    # Only one consent audit event should be recorded.
    with api["session_factory"]() as db:
        consent_events = (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == api["user_ids"]["candidate1"],
                AuditLog.action == "CONSENT_GIVEN",
            )
            .count()
        )

    assert consent_events == 1


def test_resume_upload_is_rejected_without_consent(api):
    client = api["client"]

    response = upload_test_pdf(client)

    assert response.status_code == 403


def test_candidate_can_upload_list_download_and_delete_resume(api):
    client = api["client"]

    give_consent(client)

    # Upload a resume.
    upload_response = upload_test_pdf(client)

    assert upload_response.status_code == 201, upload_response.text

    uploaded_resume = upload_response.json()
    resume_id = uploaded_resume["id"]

    assert uploaded_resume["parse_status"] == "pending"
    assert uploaded_resume["candidate_id"] == api["user_ids"]["candidate1"]

    # Verify the resume appears in the candidate's list.
    list_response = client.get("/resumes")

    assert list_response.status_code == 200, list_response.text
    assert any(
        resume["id"] == resume_id
        for resume in list_response.json()
    )

    # Verify the candidate can view resume details.
    detail_response = client.get(f"/resumes/{resume_id}")

    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["id"] == resume_id

    # Verify the candidate can download the uploaded file.
    download_response = client.get(
        f"/resumes/{resume_id}/download"
    )

    assert download_response.status_code == 200
    assert download_response.content.startswith(b"%PDF-")

    # Verify the stored file exists before deletion.
    with api["session_factory"]() as db:
        resume = db.query(
            __import__("app.models.resume", fromlist=["Resume"]).Resume
        ).filter_by(id=resume_id).first()

        assert resume is not None
        stored_file = Path(resume.file_path)

    assert stored_file.exists()

    # Delete the candidate's own resume.
    delete_response = client.delete(f"/resumes/{resume_id}")

    assert delete_response.status_code == 204

    # Verify it no longer appears in the list.
    list_after_delete = client.get("/resumes")

    assert list_after_delete.status_code == 200
    assert all(
        resume["id"] != resume_id
        for resume in list_after_delete.json()
    )

    # Verify details and downloads are no longer accessible.
    assert client.get(f"/resumes/{resume_id}").status_code == 404
    assert client.get(
        f"/resumes/{resume_id}/download"
    ).status_code == 404

    # Verify the physical file was removed.
    assert not stored_file.exists()


def test_candidate_cannot_access_another_candidates_resume(api):
    client = api["client"]

    give_consent(client)

    upload_response = upload_test_pdf(client)
    assert upload_response.status_code == 201, upload_response.text

    resume_id = upload_response.json()["id"]

    # Switch the simulated authenticated user to Candidate Two.
    api["active_user"]["id"] = api["user_ids"]["candidate2"]

    # Another candidate must not be able to access or delete the resume.
    assert client.get(f"/resumes/{resume_id}").status_code == 404

    assert client.get(
        f"/resumes/{resume_id}/download"
    ).status_code == 404

    assert client.delete(f"/resumes/{resume_id}").status_code == 404

    # The original owner must still be able to access the resume.
    api["active_user"]["id"] = api["user_ids"]["candidate1"]

    assert client.get(f"/resumes/{resume_id}").status_code == 200


def test_invalid_resume_extension_is_rejected(api):
    client = api["client"]

    give_consent(client)

    response = upload_test_pdf(
        client,
        filename="resume.txt",
        content=b"This is a text file, not a resume PDF.",
    )

    assert response.status_code == 400


def test_invalid_pdf_content_is_rejected_by_upload_endpoint(api):
    client = api["client"]

    give_consent(client)

    response = upload_test_pdf(
        client,
        filename="fake_resume.pdf",
        content=b"This is not actually a PDF file.",
    )

    assert response.status_code == 400


def test_oversized_resume_is_rejected(api):
    client = api["client"]

    give_consent(client)

    # The test upload limit is 1 MB.
    oversized_content = b"%PDF-1.7\n" + (
        b"A" * (1024 * 1024 + 100)
    )

    response = upload_test_pdf(
        client,
        filename="large_resume.pdf",
        content=oversized_content,
    )

    assert response.status_code == 413


def test_candidate_cannot_upload_more_than_five_resumes(api):
    client = api["client"]

    give_consent(client)

    # Upload the permitted five resumes.
    for index in range(5):
        response = upload_test_pdf(
            client,
            filename=f"resume_{index + 1}.pdf",
        )

        assert response.status_code == 201, response.text

    # The sixth upload must be rejected.
    response = upload_test_pdf(
        client,
        filename="resume_6.pdf",
    )

    assert response.status_code == 400


def test_recruiter_cannot_access_candidate_profile(api):
    client = api["client"]

    api["active_user"]["id"] = api["user_ids"]["recruiter"]

    response = client.get("/candidates/me")

    assert response.status_code == 403