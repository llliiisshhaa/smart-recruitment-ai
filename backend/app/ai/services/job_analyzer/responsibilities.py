"""
Responsibilities extraction module for job descriptions.
Extracts up to 10 key responsibilities or duty bullet points from job descriptions
under dedicated headings or bullet structures.
"""

import re
from typing import List

# Headings identifying responsibility sections
_RESPONSIBILITY_HEADINGS = [
    r"responsibilities",
    r"key\s+responsibilities",
    r"what\s+you\s+will\s+do",
    r"what\s+you'll\s+do",
    r"key\s+duties",
    r"duties",
    r"role\s+and\s+responsibilities",
    r"core\s+responsibilities",
    r"day\s+to\s+day",
]

_HEADING_REGEX = re.compile(
    rf"^(?:#+\s*)?(?:{'|'.join(_RESPONSIBILITY_HEADINGS)})[:\s]*$",
    re.IGNORECASE | re.MULTILINE,
)

_BULLET_PREFIX = re.compile(r"^\s*(?:[-*•·–—]|\d+[.)])\s*")


def extract_responsibilities(text: str, max_items: int = 10) -> List[str]:
    """
    Extract key role responsibilities from job description text.

    Args:
        text: Full job description text.
        max_items: Maximum number of responsibility items to return (default: 10).

    Returns:
        List of cleaned responsibility strings (up to max_items).
    """
    if not text or not text.strip():
        return []

    lines = text.splitlines()
    responsibilities: List[str] = []

    # Strategy 1: Check for explicit heading
    heading_idx = -1
    for i, line in enumerate(lines):
        clean_line = line.strip().lower().rstrip(":")
        for h in _RESPONSIBILITY_HEADINGS:
            if re.match(rf"^(?:#+\s*)?{h}$", clean_line):
                heading_idx = i
                break
        if heading_idx != -1:
            break

    if heading_idx != -1:
        # Collect lines under the heading until another heading or double newline
        for line in lines[heading_idx + 1:]:
            trimmed = line.strip()
            if not trimmed:
                continue

            # If line looks like a new section heading, stop
            if re.match(r"^(?:#+\s*)?[A-Z][A-Za-z\s]{3,30}:?$", trimmed) and not _BULLET_PREFIX.match(line):
                break

            cleaned = _BULLET_PREFIX.sub("", trimmed).strip()
            if len(cleaned) >= 10:
                responsibilities.append(cleaned)
                if len(responsibilities) >= max_items:
                    break

    # Strategy 2: If no heading or heading yielded no items, scan for bulleted lines anywhere
    if not responsibilities:
        for line in lines:
            trimmed = line.strip()
            if _BULLET_PREFIX.match(trimmed):
                cleaned = _BULLET_PREFIX.sub("", trimmed).strip()
                if len(cleaned) >= 15:
                    responsibilities.append(cleaned)
                    if len(responsibilities) >= max_items:
                        break

    return responsibilities[:max_items]
