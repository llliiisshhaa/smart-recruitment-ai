"""
Fairness and anti-bias scanner for job postings.
Flags potentially discriminatory phrasing regarding age, gender, marital status,
or nationality using a configurable word list, and provides neutral alternatives.
"""

import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

BIASED_TERMS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "biased_terms.json"


def load_biased_terms() -> List[Dict[str, str]]:
    """Load biased term definitions from JSON storage."""
    if BIASED_TERMS_PATH.is_file():
        try:
            with open(BIASED_TERMS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.warning("Could not load biased terms from %s: %s", BIASED_TERMS_PATH, exc)
    return []


def _build_fairness_patterns() -> List[Tuple[Dict[str, str], re.Pattern]]:
    """
    Build compiled word-boundary regular expressions for biased terms.
    Sorted descending by term length to ensure compound phrases match before single words.
    """
    raw_terms = load_biased_terms()
    sorted_terms = sorted(raw_terms, key=lambda t: len(t.get("term", "")), reverse=True)

    compiled: List[Tuple[Dict[str, str], re.Pattern]] = []
    for item in sorted_terms:
        term = item.get("term", "").strip()
        if not term:
            continue
        escaped = re.escape(term)
        pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
        compiled.append((item, pattern))

    return compiled


_COMPILED_PATTERNS = None


def get_fairness_patterns() -> List[Tuple[Dict[str, str], re.Pattern]]:
    """Cached accessor for compiled fairness patterns."""
    global _COMPILED_PATTERNS
    if _COMPILED_PATTERNS is None:
        _COMPILED_PATTERNS = _build_fairness_patterns()
    return _COMPILED_PATTERNS


def scan_fairness_warnings(text: str) -> List[Dict[str, str]]:
    """
    Scan job text for potentially biased or discriminatory language.

    Args:
        text: Combined job title and description.

    Returns:
        List of warning dictionaries:
        - matched_phrase: The exact text matched in the input.
        - category: Classification (age, gender, marital_status, nationality).
        - suggested_rewrite: Inclusive recommendation.
    """
    if not text or not text.strip():
        return []

    patterns = get_fairness_patterns()
    warnings: List[Dict[str, str]] = []
    seen_matches = set()

    for item, pattern in patterns:
        for match in pattern.finditer(text):
            matched_str = match.group(0)
            key = (matched_str.lower(), item.get("category", ""))
            if key not in seen_matches:
                seen_matches.add(key)
                warnings.append({
                    "matched_phrase": matched_str,
                    "category": item.get("category", "general"),
                    "suggested_rewrite": item.get("suggested_rewrite", "Use neutral terminology."),
                })

    return warnings
