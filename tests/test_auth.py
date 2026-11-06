"""
Comprehensive Authentication & Authorization Test Suite.
Validates registration input validation, password security, JWT lifecycle,
Role-Based Access Control (RBAC), and compliance audit trails.
"""

from app.core.security import create_access_token, decode_access_token
from app.models.audit import AuditLog
from app.models.user import CandidateProfile, RecruiterProfile, User


# ==============================================================================
# 1. Registration & Input Validation Tests
# ==============================================================================


def test_successful_register_candidate(client, db):
    """
    Verify that a candidate can register with valid credentials,
    email is normalized to lowercase, password hash is securely stored,
    and a matching CandidateProfile row is initialized.
    """
    payload = {
        "email": "Candidate.New@Example.COM",
        "password": "SecurePassword123!",
        "full_name": "Jane Candidate",
        "role": "candidate",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == "candidate.new@example.com"
    assert data["full_name"] == "Jane Candidate"
    assert data["role"] == "candidate"
    assert data["is_active"] is True
    assert "password" not in data
    assert "password_hash" not in data

    # Verify candidate profile was automatically created
    user_id = data["id"]
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    assert profile is not None
    assert profile.user_id == user_id


def test_successful_register_recruiter(client, db):
    """
    Verify that a recruiter can register and an empty RecruiterProfile row is created.
    """
    payload = {
        "email": "recruiter.new@example.com",
        "password": "SecurePassword123!",
        "full_name": "John Recruiter",
        "role": "recruiter",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["role"] == "recruiter"

    # Verify recruiter profile was automatically created
    user_id = data["id"]
    profile = db.query(RecruiterProfile).filter(RecruiterProfile.user_id == user_id).first()
    assert profile is not None
    assert profile.user_id == user_id


def test_duplicate_email_rejected_with_409(client):
    """
    Verify that registering an already registered email (case-insensitive) returns 409 Conflict.
    """
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "First User",
        "role": "candidate",
    }
    first_resp = client.post("/auth/register", json=payload)
    assert first_resp.status_code == 201

    # Attempt to register with uppercase email
    duplicate_payload = {
        "email": "DUPLICATE@EXAMPLE.COM",
        "password": "AnotherPassword123!",
        "full_name": "Second User",
        "role": "candidate",
    }
    second_resp = client.post("/auth/register", json=duplicate_payload)
    assert second_resp.status_code == 409
    assert second_resp.json()["detail"] == "Email is already registered"


def test_weak_password_rejected(client):
    """
    Verify that passwords < 8 chars, without letters, or without digits are rejected with 422.
    """
    base_payload = {
        "email": "test.password@example.com",
        "full_name": "Test User",
        "role": "candidate",
    }

    # Too short (< 8 chars)
    resp_short = client.post(
        "/auth/register",
        json={**base_payload, "password": "Ab1!"},
    )
    assert resp_short.status_code == 422

    # No letters (digits only)
    resp_no_letters = client.post(
        "/auth/register",
        json={**base_payload, "password": "12345678!"},
    )
    assert resp_no_letters.status_code == 422

    # No digits (letters only)
    resp_no_digits = client.post(
        "/auth/register",
        json={**base_payload, "password": "PasswordOnly!"},
    )
    assert resp_no_digits.status_code == 422


def test_role_admin_rejected_on_public_registration(client):
    """
    Verify that attempting to self-register as an admin is rejected with 422 or 403.
    """
    payload = {
        "email": "hacker.admin@example.com",
        "password": "HackerPassword123!",
        "full_name": "Rogue Admin",
        "role": "admin",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code in (403, 422)


def test_empty_full_name_rejected(client):
    """
    Verify that empty or whitespace-only full_name is rejected with 422.
    """
    payload = {
        "email": "empty.name@example.com",
        "password": "Password123!",
        "full_name": "   ",
        "role": "candidate",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422


# ==============================================================================
# 2. Login & Authentication Tests
# ==============================================================================


def test_successful_login_returns_token(client, candidate_user):
    """
    Verify that valid credentials return a JWT token with sub, role, and exp claims.
    """
    login_payload = {
        "email": candidate_user.email,
        "password": "Candidate123!",
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Decode and inspect token payload
    payload = decode_access_token(data["access_token"])
    assert payload["sub"] == str(candidate_user.id)
    assert payload["role"] == "candidate"
    assert "exp" in payload


def test_wrong_password_returns_401_generic_message(client, candidate_user):
    """
    Verify that wrong password returns 401 with generic 'Invalid email or password'.
    """
    login_payload = {
        "email": candidate_user.email,
        "password": "WrongPassword999!",
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_unknown_email_returns_401_generic_message(client):
    """
    Verify that non-existent email returns identical generic 401 message to prevent account enumeration.
    """
    login_payload = {
        "email": "nonexistent.user@example.com",
        "password": "SomePassword123!",
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_inactive_user_cannot_login(client, db):
    """
    Verify that soft-disabled or inactive accounts cannot log in (returns 403).
    """
    from app.core.security import hash_password

    inactive_user = User(
        email="inactive@example.com",
        password_hash=hash_password("Inactive123!"),
        full_name="Inactive User",
        role="candidate",
        is_active=False,
    )
    db.add(inactive_user)
    db.commit()

    response = client.post(
        "/auth/login",
        json={"email": "inactive@example.com", "password": "Inactive123!"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "User account is inactive"


# ==============================================================================
# 3. /auth/me & Token Validation Tests
# ==============================================================================


def test_get_me_with_valid_token(client, candidate_headers, candidate_user):
    """
    Verify that GET /auth/me returns the authenticated user's profile with a valid token.
    """
    response = client.get("/auth/me", headers=candidate_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == candidate_user.id
    assert data["email"] == candidate_user.email
    assert data["role"] == "candidate"


def test_get_me_without_token_returns_401(client):
    """
    Verify that accessing /auth/me without an Authorization header returns 401 and WWW-Authenticate header.
    """
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert "Bearer" in response.headers["WWW-Authenticate"]


def test_get_me_with_expired_token_returns_401(client, candidate_user):
    """
    Verify that an expired token returns 401 with WWW-Authenticate: Bearer.
    """
    expired_token = create_access_token(
        user_id=candidate_user.id,
        role=candidate_user.role,
        expires_minutes=-10,  # Negative expiry creates expired token
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert "Bearer" in response.headers["WWW-Authenticate"]


def test_get_me_with_tampered_token_returns_401(client, candidate_headers):
    """
    Verify that a signature-tampered or corrupt token returns 401 with WWW-Authenticate: Bearer.
    """
    tampered_headers = {"Authorization": candidate_headers["Authorization"] + "tampered_suffix"}
    response = client.get("/auth/me", headers=tampered_headers)

    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert "Bearer" in response.headers["WWW-Authenticate"]


# ==============================================================================
# 4. Role-Based Access Control (RBAC) Tests
# ==============================================================================


def test_candidate_calling_recruiter_endpoint_returns_403(client, candidate_headers):
    """
    Verify that a candidate calling the recruiter-only endpoint receives 403 Forbidden.
    """
    response = client.get("/auth/recruiter-only", headers=candidate_headers)
    assert response.status_code == 403


def test_candidate_calling_admin_endpoint_returns_403(client, candidate_headers):
    """
    Verify that a candidate calling the admin-only endpoint receives 403 Forbidden.
    """
    response = client.get("/auth/admin-only", headers=candidate_headers)
    assert response.status_code == 403


def test_recruiter_calling_recruiter_endpoint_returns_200(client, recruiter_headers, recruiter_user):
    """
    Verify that a recruiter calling the recruiter-only endpoint succeeds (200 OK).
    """
    response = client.get("/auth/recruiter-only", headers=recruiter_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Welcome recruiter"
    assert data["user_id"] == recruiter_user.id


def test_admin_calling_admin_endpoint_returns_200(client, admin_headers, admin_user):
    """
    Verify that an admin calling the admin-only endpoint succeeds (200 OK).
    """
    response = client.get("/auth/admin-only", headers=admin_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Welcome admin"
    assert data["user_id"] == admin_user.id


# ==============================================================================
# 5. Audit Logging Tests
# ==============================================================================


def test_audit_rows_created_for_register_and_login(client, db):
    """
    Verify that USER_REGISTERED, LOGIN_SUCCESS, and LOGIN_FAILED actions
    are recorded in the audit_logs table, and that LOGIN_FAILED stores the attempted email
    without ever storing passwords.
    """
    # 1. Register
    reg_payload = {
        "email": "audit.test@example.com",
        "password": "Password123!",
        "full_name": "Audit Test",
        "role": "candidate",
    }
    reg_resp = client.post("/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    user_id = reg_resp.json()["id"]

    # Verify USER_REGISTERED audit log
    reg_log = db.query(AuditLog).filter(
        AuditLog.action == "USER_REGISTERED",
        AuditLog.entity_id == user_id,
    ).first()
    assert reg_log is not None
    assert reg_log.user_id == user_id
    assert reg_log.details["email"] == "audit.test@example.com"

    # 2. Login Failed
    client.post("/auth/login", json={"email": "audit.test@example.com", "password": "WrongPassword!"})
    failed_log = db.query(AuditLog).filter(
        AuditLog.action == "LOGIN_FAILED",
    ).order_by(AuditLog.id.desc()).first()
    assert failed_log is not None
    assert failed_log.details["attempted_email"] == "audit.test@example.com"
    # Ensure password is NEVER in details
    assert "password" not in str(failed_log.details).lower()

    # 3. Login Success
    client.post("/auth/login", json={"email": "audit.test@example.com", "password": "Password123!"})
    success_log = db.query(AuditLog).filter(
        AuditLog.action == "LOGIN_SUCCESS",
        AuditLog.entity_id == user_id,
    ).first()
    assert success_log is not None
    assert success_log.user_id == user_id
    assert success_log.details["email"] == "audit.test@example.com"


# ==============================================================================
# 6. Password Security & Sanitization Tests
# ==============================================================================


def test_response_and_database_never_contain_plaintext_password(client, db):
    """
    Verify that passwords are never returned in responses and stored only as secure hashes.
    """
    raw_password = "SuperSecretPassword123!"
    reg_payload = {
        "email": "secret.check@example.com",
        "password": raw_password,
        "full_name": "Secret User",
        "role": "candidate",
    }
    reg_resp = client.post("/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201

    reg_data = reg_resp.json()
    assert "password" not in reg_data
    assert "password_hash" not in reg_data
    assert raw_password not in str(reg_data)

    # Check database record
    user = db.query(User).filter(User.email == "secret.check@example.com").first()
    assert user is not None
    assert user.password_hash != raw_password
    assert raw_password not in user.password_hash
    assert user.password_hash.startswith("$argon2")

    # Check login response
    login_resp = client.post(
        "/auth/login",
        json={"email": "secret.check@example.com", "password": raw_password},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert raw_password not in str(login_data)
