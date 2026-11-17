"""
Job Description Analyzer orchestrator.
Coordinates skill extraction with importance heuristics, experience/education extraction,
responsibility parsing, and fairness auditing into a single deterministic rule-based analysis.
"""

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.ai.services.job_analyzer.fairness import scan_fairness_warnings
from app.ai.services.job_analyzer.requirements import (
    extract_education_level,
    extract_min_experience,
)
from app.ai.services.job_analyzer.responsibilities import extract_responsibilities
from app.ai.services.job_analyzer.skills import extract_job_skills

ANALYZER_VERSION = "1.0.0"


def analyze_job_description(
    db: Optional[Session],
    title: Optional[str] = "",
    description: Optional[str] = "",
) -> Dict[str, Any]:
    """
    Analyze job description text and suggest structured attributes.

    Args:
        db: SQLAlchemy database session to access skill taxonomy.
        title: Job posting title.
        description: Job posting description and specifications.

    Returns:
        Structured suggestions dictionary:
        - skills: List of detected skills with evidence and suggested importance.
        - min_experience_years: Suggested minimum experience in years (clamped 0-40) or None.
        - education: Suggested education degree level string or None.
        - responsibilities: List of extracted responsibility bullet points (up to 10).
        - fairness_warnings: List of potentially biased phrasing with neutral suggestions.
        - meta: Dictionary containing version and heuristic disclaimer notes.
    """
    safe_title = str(title or "").strip()
    safe_desc = str(description or "").strip()
    combined_text = f"{safe_title}\n{safe_desc}" if safe_title else safe_desc

    try:
        skills = extract_job_skills(db, safe_title, safe_desc)
    except Exception:
        skills = []

    try:
        min_experience_years = extract_min_experience(combined_text)
    except Exception:
        min_experience_years = None

    try:
        education = extract_education_level(combined_text)
    except Exception:
        education = None

    try:
        responsibilities = extract_responsibilities(safe_desc)
    except Exception:
        responsibilities = []

    try:
        fairness_warnings = scan_fairness_warnings(combined_text)
    except Exception:
        fairness_warnings = []

    return {
        "skills": skills,
        "min_experience_years": min_experience_years,
        "education": education,
        "responsibilities": responsibilities,
        "fairness_warnings": fairness_warnings,
        "meta": {
            "analyzer_version": ANALYZER_VERSION,
            "notes": "Rule-based heuristic suggestions. Review before applying to job posting.",
        },
    }
