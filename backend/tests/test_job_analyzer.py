"""
Tests for Stage 9: Rule-based Job Description Analyzer.
Covers skill extraction with cue importance, experience/education extraction,
responsibilities parsing, fairness auditing, and the POST /jobs/analyze endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import AuditLog, Job, JobSkill, Skill, User
from app.ai.services.job_analyzer.analyzer import analyze_job_description
from app.ai.services.job_analyzer.fairness import scan_fairness_warnings
from app.ai.services.job_analyzer.requirements import (
    extract_education_level,
    extract_min_experience,
)
from app.ai.services.job_analyzer.responsibilities import extract_responsibilities
from app.ai.services.job_analyzer.skills import extract_job_skills


@pytest.fixture
def analyzer_db(tmp_path, monkeypatch):
    """
    Isolated in-memory database with test users and seeded skill taxonomy.
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
        # Create candidate and recruiter users
        candidate = User(
            email="candidate@test.example",
            password_hash="test-hash",
            full_name="Test Candidate",
            role="candidate",
            is_active=True,
        )
        recruiter = User(
            email="recruiter@test.example",
            password_hash="test-hash",
            full_name="Test Recruiter",
            role="recruiter",
            is_active=True,
        )
        db.add_all([candidate, recruiter])
        db.commit()

        # Seed real taxonomy skills
        skills_data = [
            ("python", "Programming Languages"),
            ("sql", "Databases"),
            ("javascript", "Programming Languages"),
            ("typescript", "Programming Languages"),
            ("postgresql", "Databases"),
            ("machine learning", "AI & Data"),
            ("c++", "Programming Languages"),
            ("c#", "Programming Languages"),
            ("node.js", "Frameworks & Libraries"),
            ("java", "Programming Languages"),
            ("docker", "DevOps"),
            ("fastapi", "Frameworks & Libraries"),
            ("react", "Frontend"),
        ]
        db.add_all([Skill(name=name, category=cat) for name, cat in skills_data])
        db.commit()

        db.refresh(candidate)
        db.refresh(recruiter)

        user_ids = {
            "candidate": candidate.id,
            "recruiter": recruiter.id,
        }

    active_user = {"id": user_ids["recruiter"]}
    auth_enabled = {"enabled": True}

    def override_get_db():
        with TestingSessionLocal() as db:
            yield db

    def override_get_current_user(db=__import__("fastapi").Depends(override_get_db)):
        if not auth_enabled["enabled"] or active_user["id"] is None:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        u = db.query(User).filter(User.id == active_user["id"]).first()
        if not u:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return u

    app.dependency_overrides[get_db] = override_get_db
    from app.core.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)

    yield {
        "client": client,
        "engine": engine,
        "SessionLocal": TestingSessionLocal,
        "users": user_ids,
        "active_user": active_user,
        "auth_enabled": auth_enabled,
    }

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


# ==============================================================================
# Unit Tests: Skill Extraction & Importance Cues
# ==============================================================================

def test_job_skills_realistic_description(analyzer_db):
    """Verify that a realistic description extracts skills with evidence and importance."""
    with analyzer_db["SessionLocal"]() as db:
        title = "Senior Backend Engineer"
        desc = (
            "We are looking for a Senior Engineer. "
            "You must be proficient in Python and have hands-on experience with FastAPI. "
            "Experience with Docker and PostgreSQL is preferred."
        )
        skills = extract_job_skills(db, title, desc)
        skill_map = {s["name"]: s for s in skills}

        assert "python" in skill_map
        assert skill_map["python"]["suggested_importance"] == "required"
        assert "proficient in Python" in skill_map["python"]["evidence_text"]

        assert "fastapi" in skill_map
        assert skill_map["fastapi"]["suggested_importance"] == "required"

        assert "docker" in skill_map
        assert skill_map["docker"]["suggested_importance"] == "preferred"

        assert "postgresql" in skill_map
        assert skill_map["postgresql"]["suggested_importance"] == "preferred"


def test_job_skills_required_vs_preferred_cue_rule(analyzer_db):
    """
    Test the specific cue rule:
    'must have Python, SQL preferred' => Python required and SQL preferred.
    """
    with analyzer_db["SessionLocal"]() as db:
        skills = extract_job_skills(db, "", "must have Python, SQL preferred")
        skill_map = {s["name"]: s for s in skills}

        assert "python" in skill_map
        assert skill_map["python"]["suggested_importance"] == "required"

        assert "sql" in skill_map
        assert skill_map["sql"]["suggested_importance"] == "preferred"


def test_job_skills_alias_mapping(analyzer_db):
    """Verify that skill aliases (JS, Postgres, ML) map to canonical skills."""
    with analyzer_db["SessionLocal"]() as db:
        desc = "Our stack relies on JS, Postgres, and ML pipelines."
        skills = extract_job_skills(db, "", desc)
        names = {s["name"] for s in skills}

        assert "javascript" in names  # from 'JS'
        assert "postgresql" in names  # from 'Postgres'
        assert "machine learning" in names  # from 'ML'


def test_job_skills_punctuation_and_substring_avoidance(analyzer_db):
    """
    C++, C#, and Node.js must match.
    Substrings like 'Java' inside 'JavaScript' must NOT create a false Java match.
    """
    with analyzer_db["SessionLocal"]() as db:
        desc = "We develop in C++, C#, and Node.js. Strong JavaScript skills required."
        skills = extract_job_skills(db, "", desc)
        names = {s["name"] for s in skills}

        assert "c++" in names
        assert "c#" in names
        assert "node.js" in names
        assert "javascript" in names
        # 'Java' is in database taxonomy but should NOT match inside 'JavaScript'
        assert "java" not in names


def test_job_skills_java_and_javascript_developer(analyzer_db):
    """
    Test proving 'Java and JavaScript developer' returns both skills
    without a false Java match inside JavaScript.
    """
    with analyzer_db["SessionLocal"]() as db:
        desc = "Seeking a Java and JavaScript developer for full-stack tasks."
        skills = extract_job_skills(db, "", desc)
        names = [s["name"] for s in skills]

        assert "java" in names
        assert "javascript" in names
        assert len(names) == 2

        # Check evidence text
        skill_map = {s["name"]: s for s in skills}
        assert "Java and JavaScript developer" in skill_map["java"]["evidence_text"]
        assert "Java and JavaScript developer" in skill_map["javascript"]["evidence_text"]


# ==============================================================================
# Unit Tests: Requirements (Experience & Education)
# ==============================================================================

def test_experience_extraction_patterns():
    """Test experience pattern matching across multiple formats."""
    assert extract_min_experience("Requires 3+ years of software development experience") == 3
    assert extract_min_experience("Ideal candidate has 2-4 years of industry experience") == 2
    assert extract_min_experience("Minimum 5 years in backend engineering") == 5
    assert extract_min_experience("At least 3 years working with cloud platforms") == 3
    assert extract_min_experience("We welcome freshers to apply for this entry-level role") == 0
    assert extract_min_experience("Looking for candidates with 0-1 years of experience") == 0
    assert extract_min_experience("Exciting startup looking for passionate coders") is None
    # Experience clamped to 40 max
    assert extract_min_experience("Must have 50+ years of experience") == 40


def test_education_extraction_keywords():
    """Test education degree extraction and priority levels."""
    assert extract_education_level("Candidate must hold a B.Tech or B.E. in Computer Science") == "Bachelor's Degree"
    assert extract_education_level("Requires BCA or B.Sc in IT") == "Bachelor's Degree"
    assert extract_education_level("Requires an MCA or M.Tech degree") == "Master's Degree"
    assert extract_education_level("MBA with technical background preferred") == "Master's Degree"
    assert extract_education_level("Ph.D. in Artificial Intelligence or related discipline") == "PhD / Doctorate"
    assert extract_education_level("Doctorate in Computer Science preferred") == "PhD / Doctorate"
    assert extract_education_level("Self-taught engineer with portfolio") is None


# ==============================================================================
# Unit Tests: Responsibilities Extraction
# ==============================================================================

def test_responsibilities_extraction_with_heading():
    """Extract bullet points under explicit responsibility heading."""
    desc = """
    About the role:
    Fast-paced product environment.

    Key Responsibilities:
    - Architect and maintain REST APIs using FastAPI
    - Design and optimize PostgreSQL database schemas
    - Collaborate with product designers and frontend teams
    - Participate in on-call rotations and deployments

    Qualifications:
    - 3+ years experience
    """
    items = extract_responsibilities(desc)
    assert len(items) == 4
    assert items[0] == "Architect and maintain REST APIs using FastAPI"
    assert items[1] == "Design and optimize PostgreSQL database schemas"
    assert "Qualifications" not in items


def test_responsibilities_extraction_without_heading():
    """Extract bullet points when no explicit heading is provided."""
    desc = """
    We need someone who can:
    * Build scalable cloud infrastructure with Docker
    * Write unit and integration test suites
    * Conduct code reviews with peers
    """
    items = extract_responsibilities(desc)
    assert len(items) == 3
    assert items[0] == "Build scalable cloud infrastructure with Docker"


def test_responsibilities_empty_text():
    """Return empty list when no bullets or duties are found."""
    assert extract_responsibilities("") == []
    assert extract_responsibilities("Join our dynamic team for an exciting journey.") == []


# ==============================================================================
# Unit Tests: Fairness & Anti-Bias Scanner
# ==============================================================================

def test_fairness_flags_fire_for_biased_wording():
    """Flags fire for discriminatory terms and suggest neutral rewrites."""
    text = (
        "Looking for a young and energetic digital native, unmarried or single candidates only. "
        "Male candidate preferred. Native English speaker and US citizens only."
    )
    warnings = scan_fairness_warnings(text)

    categories = {w["category"] for w in warnings}
    phrases = {w["matched_phrase"].lower() for w in warnings}

    assert "age" in categories
    assert "gender" in categories
    assert "marital_status" in categories
    assert "nationality" in categories

    assert "young and energetic" in phrases
    assert "digital native" in phrases
    assert "unmarried" in phrases
    assert "single candidates only" in phrases
    assert "male candidate" in phrases
    assert "native english speaker" in phrases
    assert "us citizens only" in phrases

    # Verify each warning includes a non-empty suggested rewrite
    for w in warnings:
        assert w["suggested_rewrite"] != ""


def test_fairness_flags_neutral_text_no_false_positives():
    """
    Ensure neutral phrasing produces zero warnings:
    'Bachelor's degree in Computer Science', 'single sign-on',
    'single-page application' and 'mature codebase' must NOT be flagged.
    """
    neutral_text = (
        "Seeking an engineer with a Bachelor's degree in Computer Science. "
        "Must have experience implementing single sign-on (SSO), architecting "
        "single-page applications, and maintaining a mature codebase. "
        "Candidates should be authorized to work locally."
    )
    warnings = scan_fairness_warnings(neutral_text)
    assert warnings == []


# ==============================================================================
# Unit Tests: Analyzer Orchestrator & Odd Input Resiliency
# ==============================================================================

def test_analyze_job_description_odd_inputs(analyzer_db):
    """Never crash on empty strings, non-English text, or symbol-heavy input."""
    with analyzer_db["SessionLocal"]() as db:
        # Empty input
        res1 = analyze_job_description(db, "", "")
        assert res1["skills"] == []
        assert res1["min_experience_years"] is None
        assert res1["responsibilities"] == []

        # Non-English input
        res2 = analyze_job_description(db, "Développeur", "Nous recherchons un ingénieur Python.")
        assert len(res2["skills"]) >= 1
        assert res2["skills"][0]["name"] == "python"

        # Symbol input
        res3 = analyze_job_description(db, "!@#$%", "&&& *** C++ and C# required !!!")
        assert len(res3["skills"]) == 2
        names = {s["name"] for s in res3["skills"]}
        assert "c++" in names
        assert "c#" in names


# ==============================================================================
# API Endpoint Tests: POST /jobs/analyze
# ==============================================================================

def test_analyze_endpoint_recruiter_success(analyzer_db):
    """Recruiter successfully receives rule-based analysis."""
    client = analyzer_db["client"]
    payload = {
        "title": "Backend Python Developer",
        "description": (
            "We are hiring a Python Engineer with 3+ years experience. "
            "Must have strong knowledge of Python and FastAPI. Docker preferred. "
            "Bachelor's degree required.\n"
            "Responsibilities:\n"
            "- Build RESTful services\n"
            "- Monitor production reliability"
        ),
    }
    response = client.post("/jobs/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "skills" in data
    assert len(data["skills"]) >= 2
    assert data["min_experience_years"] == 3
    assert data["education"] == "Bachelor's Degree"
    assert len(data["responsibilities"]) == 2
    assert "meta" in data
    assert data["meta"]["analyzer_version"] == "1.0.0"

    # Verify nothing was saved to Job or JobSkill tables
    with analyzer_db["SessionLocal"]() as db:
        assert db.query(Job).count() == 0
        assert db.query(JobSkill).count() == 0

        # Verify AuditLog row was written
        audit = (
            db.query(AuditLog)
            .filter(AuditLog.action == "JOB_DESCRIPTION_ANALYZED")
            .first()
        )
        assert audit is not None
        assert audit.user_id == analyzer_db["users"]["recruiter"]
        assert "description_length" in audit.details
        # Ensure full text was NOT logged in audit details
        assert "We are hiring" not in str(audit.details)


def test_analyze_endpoint_candidate_forbidden(analyzer_db):
    """Candidate is forbidden (403) from accessing recruiter analyzer endpoint."""
    client = analyzer_db["client"]
    analyzer_db["active_user"]["id"] = analyzer_db["users"]["candidate"]

    payload = {"title": "Dev", "description": "Python developer"}
    response = client.post("/jobs/analyze", json=payload)
    assert response.status_code == 403


def test_analyze_endpoint_no_token_unauthorized(analyzer_db):
    """Unauthenticated requests are rejected (401)."""
    client = analyzer_db["client"]
    analyzer_db["auth_enabled"]["enabled"] = False

    payload = {"title": "Dev", "description": "Python developer"}
    response = client.post("/jobs/analyze", json=payload)
    assert response.status_code == 401


def test_analyze_endpoint_empty_description_rejected(analyzer_db):
    """Empty or whitespace-only description is rejected with 422."""
    client = analyzer_db["client"]
    payload = {"title": "Dev", "description": "   "}
    response = client.post("/jobs/analyze", json=payload)
    assert response.status_code == 422
