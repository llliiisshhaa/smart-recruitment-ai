"""
Resume parser orchestrator.
Coordinates document text extraction, text cleaning, section detection,
entity extraction, and canonical skill matching into a unified, deterministic schema.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from app.ai.services.resume_parser.clean import clean_text
from app.ai.services.resume_parser.entities import (
    extract_achievements,
    extract_certifications,
    extract_contacts,
    extract_education,
    extract_experience,
    extract_languages,
    extract_projects,
)
from app.ai.services.resume_parser.extract import extract_text
from app.ai.services.resume_parser.sections import extract_sections
from app.ai.services.resume_parser.skills import extract_skills

PARSER_VERSION = "1.0.0"


def parse_resume(
    path: Union[str, Path],
    canonical_skills: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Parse a resume document (PDF or DOCX) into structured data.

    Args:
        path: Filesystem path to the stored document.
        canonical_skills: Optional authoritative skill names from database.

    Returns:
        Structured dictionary matching the required schema:
        - contact
        - education
        - skills
        - projects
        - experience
        - certifications
        - languages
        - achievements
        - meta
        - _raw_text (internal cleaned text for database persistence)
    """
    # 1. Extract raw document text
    raw_document_text = extract_text(path)

    # 2. Clean and normalize text
    cleaned_document_text = clean_text(raw_document_text)

    # 3. Detect sections and preserve header
    sections = extract_sections(cleaned_document_text)
    header_text = sections.get("header", "")

    # 4. Extract entities across sections
    contacts = extract_contacts(header_text, cleaned_document_text)

    # Education: prioritize 'education' section, then fallback to search in full text
    education = extract_education(sections.get("education", ""))

    # Experience & internships
    exp_text = sections.get("experience", "")
    internships_text = sections.get("internships", "")
    combined_exp = (exp_text + "\n" + internships_text).strip()
    experience = extract_experience(combined_exp)

    # Projects
    projects = extract_projects(sections.get("projects", ""))

    # Certifications
    certifications = extract_certifications(sections.get("certifications", ""))

    # Languages
    languages = extract_languages(sections.get("languages", ""))

    # Achievements
    achievements = extract_achievements(sections.get("achievements", ""))

    # 5. Extract canonical skills and evidence
    skills = extract_skills(sections, canonical_skills)

    # 6. Collect metadata and diagnostic warnings
    warnings: List[str] = []
    if not contacts.get("email"):
        warnings.append("No contact email address identified.")
    if not contacts.get("phone"):
        warnings.append("No phone number identified.")
    if not education:
        warnings.append("No education credentials detected.")
    if not skills:
        warnings.append("No matching technical skills identified from taxonomy.")

    sections_found = [sec for sec in sections.keys() if sec != "header"]

    return {
        "contact": contacts,
        "education": education,
        "skills": skills,
        "projects": projects,
        "experience": experience,
        "certifications": certifications,
        "languages": languages,
        "achievements": achievements,
        "meta": {
            "parser_version": PARSER_VERSION,
            "sections_found": sections_found,
            "warnings": warnings,
        },
        "_raw_text": cleaned_document_text,
    }

