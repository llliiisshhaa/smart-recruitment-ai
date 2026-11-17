"""
Requirement extraction module for job descriptions.
Heuristically extracts suggested minimum years of experience and education level
using deterministic pattern matching.
"""

import re
from typing import Optional


# Experience patterns
# Matches "3+ years", "2-4 years", "minimum 5 years", "at least 3 years", "fresher", etc.
_FRESHER_PATTERN = re.compile(
    r"\b(?:fresher|freshers|entry[\s-]level|0[\s-]1\s*(?:years?|yrs?)|0\s*(?:years?|yrs?))\b",
    re.IGNORECASE,
)

_EXPERIENCE_PATTERNS = [
    # "minimum 5 years", "at least 3 years", "min 2 yrs"
    re.compile(
        r"(?:minimum|at least|min\.?)\s*(?:of\s+)?(\d{1,2})\s*(?:\+|plus)?\s*(?:years?|yrs?)",
        re.IGNORECASE,
    ),
    # "3+ years", "3 + yrs", "5+ years of experience"
    re.compile(
        r"\b(\d{1,2})\s*(?:\+|plus)\s*(?:years?|yrs?)(?:\s+of)?\s*(?:experience)?\b",
        re.IGNORECASE,
    ),
    # "2-4 years", "3 to 5 years", "2 - 5 yrs"
    re.compile(
        r"\b(\d{1,2})\s*(?:-|to)\s*(\d{1,2})\s*(?:years?|yrs?)(?:\s+of)?\s*(?:experience)?\b",
        re.IGNORECASE,
    ),
    # "3 years of experience", "4 yrs experience"
    re.compile(
        r"\b(\d{1,2})\s*(?:years?|yrs?)\s+(?:of\s+)?(?:relevant\s+)?experience\b",
        re.IGNORECASE,
    ),
]

# Education regexes categorized by level
_PHD_PATTERN = re.compile(
    r"\b(?:ph\.?d\.?|doctorate|doctoral)\b",
    re.IGNORECASE,
)

_MASTERS_PATTERN = re.compile(
    r"\b(?:m\.?tech|m\.?c\.?a\.?|m\.?s\.?c\.?|m\.?s\.?|mba|master'?s?(?:\s+degree)?|post[\s-]graduate)\b",
    re.IGNORECASE,
)

_BACHELORS_PATTERN = re.compile(
    r"\b(?:b\.?e\.?|b\.?tech\.?|b\.?c\.?a\.?|b\.?s\.?c\.?|b\.?s\.?|bachelor'?s?(?:\s+degree)?|undergraduate|graduate)\b",
    re.IGNORECASE,
)


def extract_min_experience(text: str) -> Optional[int]:
    """
    Extract suggested minimum years of experience from job text.

    Args:
        text: Combined job title and description text.

    Returns:
        Integer experience in years clamped between 0 and 40, or None if no pattern matched.
    """
    if not text or not text.strip():
        return None

    # Check for freshers / zero-experience cues first
    if _FRESHER_PATTERN.search(text):
        return 0

    for pattern in _EXPERIENCE_PATTERNS:
        match = pattern.search(text)
        if match:
            # First capture group is the numeric years
            raw_val = match.group(1)
            try:
                years = int(raw_val)
                # Clamp between 0 and 40 years
                return max(0, min(40, years))
            except ValueError:
                continue

    return None


def extract_education_level(text: str) -> Optional[str]:
    """
    Extract suggested education degree level from job text.

    Args:
        text: Combined job title and description text.

    Returns:
        Short standardized string (e.g. 'Bachelor\'s Degree', 'Master\'s Degree', 'PhD') or None.
    """
    if not text or not text.strip():
        return None

    # Priority check: Doctorate -> Master's -> Bachelor's
    if _PHD_PATTERN.search(text):
        return "PhD / Doctorate"
    if _MASTERS_PATTERN.search(text):
        return "Master's Degree"
    if _BACHELORS_PATTERN.search(text):
        return "Bachelor's Degree"

    return None
