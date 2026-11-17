"""
Skill extraction and importance suggestion module for job descriptions.
Reuses the shared resume parser skill matcher, alias dictionary, and evidence extraction logic.
Heuristically suggests whether each extracted skill is 'required' or 'preferred' based on
surrounding syntactic cues.

Importance Rule:
- Suggests "required" when the evidence sentence contains required cues:
  ('must', 'required', 'mandatory', 'essential', 'proficient', 'strong knowledge', 'hands-on').
- Suggests "preferred" when the evidence sentence contains preferred cues:
  ('preferred', 'nice to have', 'a plus', 'good to have', 'bonus', 'desirable', 'familiarity').
- If no cues are present in the sentence, defaults to "required".
- If both required and preferred cues appear in the sentence, clause boundaries (e.g. commas,
  semicolons) are evaluated first; otherwise, "preferred" wins only when the preferred cue
  is nearest (by character distance) to the skill mention.
"""

import re
from typing import Any, Dict, List, Literal, Optional, Tuple
from sqlalchemy.orm import Session

from app.ai.services.resume_parser.skills import (
    DEFAULT_CANONICAL_SKILLS,
    _extract_sentence_containing_match,
    build_term_patterns,
)
from app.models.resume import Skill

# Cue word sets
REQUIRED_CUES = [
    "must",
    "required",
    "mandatory",
    "essential",
    "proficient",
    "strong knowledge",
    "hands-on",
    "hands on",
    "require",
    "requirements",
]

PREFERRED_CUES = [
    "preferred",
    "nice to have",
    "a plus",
    "good to have",
    "bonus",
    "desirable",
    "familiarity",
    "prefer",
    "plus",
]

# Compile patterns for fast boundary-aware cue detection
_REQUIRED_CUE_PATTERNS = [
    (cue, re.compile(rf"\b{re.escape(cue)}\b", re.IGNORECASE))
    for cue in REQUIRED_CUES
]

_PREFERRED_CUE_PATTERNS = [
    (cue, re.compile(rf"\b{re.escape(cue)}\b", re.IGNORECASE))
    for cue in PREFERRED_CUES
]


def determine_suggested_importance(
    sentence: str,
    skill_matched_text: str,
    skill_start_in_sentence: Optional[int] = None,
) -> Literal["required", "preferred"]:
    """
    Determine whether a skill is 'required' or 'preferred' based on cues in the evidence sentence.

    Rule:
    1. Scan the sentence for required and preferred cues.
    2. If no cues appear, default to 'required'.
    3. If only required cues appear, return 'required'.
    4. If only preferred cues appear, return 'preferred'.
    5. If both appear:
       - Measure the distance from the skill to the closest required cue and closest preferred cue.
       - A clause penalty (50 characters) is added if a delimiter (comma, semicolon, period)
         separates the cue from the skill.
       - 'preferred' wins ONLY when the preferred cue is strictly nearest to the skill.
       - Otherwise, 'required' wins.
    """
    if not sentence:
        return "required"

    lower_sentence = sentence.lower()

    # Determine skill position in sentence if not explicitly given
    if skill_start_in_sentence is None or skill_start_in_sentence < 0:
        idx = lower_sentence.find(skill_matched_text.lower())
        skill_start = idx if idx != -1 else 0
        skill_end = skill_start + len(skill_matched_text)
    else:
        skill_start = skill_start_in_sentence
        skill_end = skill_start + len(skill_matched_text)

    # Collect required cue matches
    req_distances: List[float] = []
    for _, pattern in _REQUIRED_CUE_PATTERNS:
        for match in pattern.finditer(sentence):
            cue_start, cue_end = match.start(), match.end()
            if cue_end <= skill_start:
                dist = skill_start - cue_end
                between = sentence[cue_end:skill_start]
            elif cue_start >= skill_end:
                dist = cue_start - skill_end
                between = sentence[skill_end:cue_start]
            else:
                dist = 0
                between = ""

            # Delimiter penalty if a clause boundary separates skill and cue
            if any(p in between for p in [",", ";", "\n"]):
                dist += 50.0

            req_distances.append(dist)

    # Collect preferred cue matches
    pref_distances: List[float] = []
    for _, pattern in _PREFERRED_CUE_PATTERNS:
        for match in pattern.finditer(sentence):
            cue_start, cue_end = match.start(), match.end()
            if cue_end <= skill_start:
                dist = skill_start - cue_end
                between = sentence[cue_end:skill_start]
            elif cue_start >= skill_end:
                dist = cue_start - skill_end
                between = sentence[skill_end:cue_start]
            else:
                dist = 0
                between = ""

            if any(p in between for p in [",", ";", "\n"]):
                dist += 50.0

            pref_distances.append(dist)

    has_req = len(req_distances) > 0
    has_pref = len(pref_distances) > 0

    if not has_req and not has_pref:
        return "required"
    if has_req and not has_pref:
        return "required"
    if has_pref and not has_req:
        return "preferred"

    # Both present: preferred wins ONLY if strictly nearest to the skill
    min_pref = min(pref_distances)
    min_req = min(req_distances)

    if min_pref < min_req:
        return "preferred"
    return "required"


def extract_job_skills(
    db: Optional[Session],
    title: str,
    description: str,
) -> List[Dict[str, Any]]:
    """
    Extract skills from job title and description using the shared taxonomy and matcher.

    Args:
        db: Database session to load authoritative Skill records.
        title: Job posting title.
        description: Job posting description.

    Returns:
        List of dictionaries with:
        - skill_id: int
        - name: str (canonical skill name)
        - category: str (taxonomy category)
        - evidence_text: str (concise sentence containing mention)
        - suggested_importance: 'required' | 'preferred'
    """
    # 1. Load canonical skills from database or fallback
    skill_map: Dict[str, Skill] = {}
    if db is not None:
        try:
            db_skills = db.query(Skill).all()
            for sk in db_skills:
                skill_map[sk.name.lower()] = sk
        except Exception:
            pass

    canonical_skill_names = list(skill_map.keys()) if skill_map else None

    # 2. Build term patterns using shared matcher logic
    term_patterns = build_term_patterns(canonical_skill_names)

    # Combine text for searching (title first, then description)
    sections = [
        ("title", title or ""),
        ("description", description or ""),
    ]

    detected_skills: Dict[str, Dict[str, Any]] = {}

    for sec_name, text in sections:
        if not text or not text.strip():
            continue

        for term, canonical, pattern in term_patterns:
            for match in pattern.finditer(text):
                matched_str = match.group(0).strip()
                evidence = _extract_sentence_containing_match(text, match.start(), match.end())

                # Find skill position within the extracted evidence sentence for distance calculations
                skill_in_ev = evidence.lower().find(matched_str.lower())
                importance = determine_suggested_importance(evidence, matched_str, skill_in_ev)

                # Lookup database skill or build fallback representation
                db_skill = skill_map.get(canonical)
                if db_skill is not None:
                    skill_id = db_skill.id
                    name = db_skill.name
                    category = db_skill.category
                else:
                    skill_id = len(detected_skills) + 1
                    name = canonical
                    category = "Technical"

                # Deduplication logic:
                # If skill already detected, upgrade to 'required' if the new mention is required
                if canonical not in detected_skills:
                    detected_skills[canonical] = {
                        "skill_id": skill_id,
                        "name": name,
                        "category": category,
                        "evidence_text": evidence,
                        "suggested_importance": importance,
                    }
                else:
                    existing = detected_skills[canonical]
                    if existing["suggested_importance"] == "preferred" and importance == "required":
                        existing["suggested_importance"] = "required"
                        existing["evidence_text"] = evidence

    # Return sorted alphabetically by skill name
    results = list(detected_skills.values())
    results.sort(key=lambda s: s["name"].lower())
    return results
