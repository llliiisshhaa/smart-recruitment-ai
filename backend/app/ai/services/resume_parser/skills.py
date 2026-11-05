"""
Skill extraction module.
Matches canonical skills and aliases against resume sections, captures supporting
sentence evidence, and determines contextual support (projects/experience usage).
"""

import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Fallback canonical skills taxonomy matching database seed data
DEFAULT_CANONICAL_SKILLS = [
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "ruby", "php", "kotlin", "swift",
    # Frameworks & Libraries
    "react", "vue.js", "angular", "next.js", "node.js", "fastapi", "django",
    "html5", "css3", "tailwind css",
    # Databases & Storage
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    # DevOps, Cloud & OS
    "docker", "kubernetes", "aws", "azure", "git", "ci/cd", "linux",
    # AI & Data
    "machine learning", "deep learning", "natural language processing",
    "data analysis", "pandas",
    # Engineering & Soft Skills
    "system design", "problem solving", "communication", "agile",
]

# Path to alias dictionary
ALIASES_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "skill_aliases.json"


def load_skill_aliases() -> Dict[str, str]:
    """Load skill aliases from JSON file."""
    if ALIASES_PATH.is_file():
        try:
            with open(ALIASES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.warning("Could not load skill aliases from %s: %s", ALIASES_PATH, exc)
    return {}


def _build_skill_pattern(term: str) -> re.Pattern:
    """
    Construct a regular expression pattern for a skill term that handles
    punctuation-heavy terms (C++, C#, .NET, CI/CD, Node.js) and prevents
    false positives in substrings (e.g. 'R' in 'React', 'Go' in 'Good').
    """
    escaped = re.escape(term)

    # Left boundary: start of line or non-alphanumeric boundary
    left = r"(?:(?<=[\s,;:()[\]{}<>/\\|`'\"-])|^)"
    # Right boundary: end of line or non-alphanumeric boundary
    right = r"(?:(?=[\s,;:()[\]{}<>/\\|`'\".\?!-])|$)"

    pattern_str = f"{left}{escaped}{right}"
    return re.compile(pattern_str, re.IGNORECASE)


def _extract_sentence_containing_match(text: str, start_idx: int, end_idx: int) -> str:
    """
    Extract a concise sentence or line excerpt surrounding the matched skill.
    Avoids returning an entire document or multi-paragraph block.
    """
    line_start = text.rfind("\n", 0, start_idx)
    line_start = 0 if line_start == -1 else line_start + 1

    line_end = text.find("\n", end_idx)
    line_end = len(text) if line_end == -1 else line_end

    line_excerpt = text[line_start:line_end].strip()
    cleaned = line_excerpt.lstrip("-*•· ").strip()

    if len(cleaned) <= 250:
        return cleaned

    excerpt_start = max(0, start_idx - 60)
    excerpt_end = min(len(text), end_idx + 60)
    snippet = text[excerpt_start:excerpt_end].replace("\n", " ").strip()
    return f"...{snippet}..."


def extract_skills(
    sections: Dict[str, str],
    canonical_skills: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Identify skills across all resume sections.

    - Resolves aliases to canonical skill names.
    - Captures evidence sentences and section attribution.
    - Sets supported_by_context = True if the skill appears in 'projects' or 'experience'.
    - Deduplicates skills while retaining strongest evidence.
    """
    valid_canonicals: Set[str] = set(s.lower() for s in (canonical_skills or DEFAULT_CANONICAL_SKILLS))
    aliases = load_skill_aliases()

    # Combine canonical skills + aliases into term_to_canonical mapping
    term_to_canonical: Dict[str, str] = {}
    for canon in valid_canonicals:
        term_to_canonical[canon] = canon

    for alias, canon in aliases.items():
        if canon.lower() in valid_canonicals:
            term_to_canonical[alias.lower()] = canon.lower()

    # Sort search terms descending by length so longer multi-word phrases match before substrings
    sorted_terms = sorted(term_to_canonical.keys(), key=lambda t: len(t), reverse=True)
    term_patterns = [(term, term_to_canonical[term], _build_skill_pattern(term)) for term in sorted_terms]

    skill_detections: Dict[str, Dict[str, Any]] = {}
    contextual_sections = {"projects", "experience", "internships"}

    for sec_name, sec_text in sections.items():
        if not sec_text:
            continue

        for term, canonical, pattern in term_patterns:
            match = pattern.search(sec_text)
            if match:
                matched_str = match.group(0).strip()
                evidence = _extract_sentence_containing_match(sec_text, match.start(), match.end())

                if canonical not in skill_detections:
                    skill_detections[canonical] = {
                        "name": canonical,
                        "matched_text": matched_str,
                        "evidence_text": evidence,
                        "section": sec_name,
                        "sections": {sec_name},
                        "context_evidence": evidence if sec_name in contextual_sections else None,
                    }
                else:
                    det = skill_detections[canonical]
                    det["sections"].add(sec_name)
                    # Upgrade evidence if matched in projects/experience
                    if sec_name in contextual_sections and not det["context_evidence"]:
                        det["context_evidence"] = evidence
                        det["evidence_text"] = evidence
                        det["section"] = sec_name
                        det["matched_text"] = matched_str

    results: List[Dict[str, Any]] = []
    for canonical, det in skill_detections.items():
        in_context = any(s in contextual_sections for s in det["sections"])
        results.append({
            "name": canonical,
            "matched_text": det["matched_text"],
            "evidence_text": det["evidence_text"],
            "section": det["section"],
            "supported_by_context": in_context,
        })

    results.sort(key=lambda s: s["name"])
    return results
