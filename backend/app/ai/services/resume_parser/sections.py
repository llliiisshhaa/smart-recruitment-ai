"""
Section detection module for resume text.
Identifies canonical sections based on line-level headings while preserving initial text as 'header'.
"""

import re
from typing import Dict, List, Optional, Tuple

# Mapping canonical section keys to recognized heading variations
SECTION_HEADINGS: Dict[str, List[str]] = {
    "summary": [
        "summary",
        "professional summary",
        "executive summary",
        "profile",
        "professional profile",
        "about me",
        "career summary",
        "personal profile",
        "brief profile",
    ],
    "objective": [
        "objective",
        "career objective",
        "professional objective",
        "job objective",
    ],
    "education": [
        "education",
        "academic background",
        "academic qualifications",
        "educational qualifications",
        "academic history",
        "qualifications",
        "education & credentials",
        "education and training",
        "degrees",
    ],
    "skills": [
        "skills",
        "technical skills",
        "core competencies",
        "key skills",
        "skills & competencies",
        "skills & proficiencies",
        "technologies",
        "tech stack",
        "technical strengths",
        "areas of expertise",
        "tools and technologies",
        "tools & technologies",
        "programming skills",
    ],
    "projects": [
        "projects",
        "academic projects",
        "personal projects",
        "key projects",
        "major projects",
        "technical projects",
        "project work",
        "selected projects",
    ],
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
        "professional background",
        "career history",
    ],
    "internships": [
        "internships",
        "internship experience",
        "summer internships",
        "industrial training",
    ],
    "certifications": [
        "certifications",
        "courses",
        "licenses",
        "certificates",
        "certifications & licenses",
        "certifications and licenses",
        "courses & certifications",
        "training & certifications",
        "professional certifications",
    ],
    "languages": [
        "languages",
        "language proficiency",
        "languages known",
        "spoken languages",
    ],
    "achievements": [
        "achievements",
        "awards",
        "honors",
        "accomplishments",
        "honors & awards",
        "honors and awards",
        "awards & achievements",
        "awards and achievements",
        "extracurricular activities",
        "activities and achievements",
    ],
}

# Inverted mapping for O(1) lookup
HEADING_TO_CANONICAL: Dict[str, str] = {}
for canonical, headings in SECTION_HEADINGS.items():
    for h in headings:
        HEADING_TO_CANONICAL[h] = canonical


def _is_heading_line(line: str) -> Optional[str]:
    """
    Check if a single line acts as a section heading.

    Returns the canonical section name if matched, else None.
    Avoids false positives in ordinary sentences.
    """
    stripped = line.strip()
    if not stripped:
        return None

    # Heading lines are concise (typically <= 6 words and <= 50 characters)
    words = stripped.split()
    if len(words) > 6 or len(stripped) > 55:
        return None

    # Remove markdown formatting (#, *, _) and trailing colons or dashes
    cleaned = re.sub(r"^[\#\*\-\_ \t]+", "", stripped)
    cleaned = re.sub(r"[\:\-\*\_\# \t]+$", "", cleaned).strip().lower()

    if not cleaned:
        return None

    # Direct match in canonical heading mapping
    if cleaned in HEADING_TO_CANONICAL:
        return HEADING_TO_CANONICAL[cleaned]

    return None


def extract_sections(text: str) -> Dict[str, str]:
    """
    Split resume text into detected sections and header.

    Returns:
        Dict where keys are canonical section names ('summary', 'skills', etc.)
        and values are the string content of that section.
        Text preceding the first detected heading is stored under 'header'.
    """
    if not text or not text.strip():
        return {}

    lines = text.split("\n")
    sections: Dict[str, List[str]] = {}
    current_section = "header"
    sections[current_section] = []

    for line in lines:
        matched_section = _is_heading_line(line)
        if matched_section:
            current_section = matched_section
            if current_section not in sections:
                sections[current_section] = []
        else:
            sections[current_section].append(line)

    result: Dict[str, str] = {}
    for sec_name, sec_lines in sections.items():
        joined_content = "\n".join(sec_lines).strip()
        if joined_content:
            result[sec_name] = joined_content

    return result

