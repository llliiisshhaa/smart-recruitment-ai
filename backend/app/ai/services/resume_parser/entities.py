"""
Entity extraction module for resume parsing.
Extracts contact information, education, experience, projects, certifications,
languages, and achievements using regular expressions, heuristics, and spaCy NER.

PRIVACY DECISION:
Sensitive demographic attributes (gender, date of birth, age, marital status,
religion, nationality, caste, photographs) are strictly excluded from extraction
and structured models to prevent bias and comply with fair recruitment principles.
"""

import re
from typing import Any, Dict, List, Optional

from app.ai.services.resume_parser.nlp import get_spacy_nlp

# Common non-name words that might appear in header lines
TITLE_STOPWORDS = {
    "resume",
    "curriculum",
    "vitae",
    "cv",
    "profile",
    "summary",
    "contact",
    "engineer",
    "developer",
    "manager",
    "analyst",
    "scientist",
    "consultant",
    "intern",
    "designer",
    "architect",
    "fresher",
    "student",
    "portfolio",
    "page",
}

# Recognized spoken/natural languages (excluding programming languages)
SPOKEN_LANGUAGES = {
    "english",
    "hindi",
    "spanish",
    "french",
    "german",
    "mandarin",
    "chinese",
    "japanese",
    "russian",
    "arabic",
    "bengali",
    "marathi",
    "telugu",
    "tamil",
    "urdu",
    "gujarati",
    "kannada",
    "malayalam",
    "odia",
    "punjabi",
    "portuguese",
    "italian",
}

# Common degree patterns
DEGREE_REGEX = re.compile(
    r"\b("
    r"B\.?E\.?|B\.?Tech\.?|Bachelor\s+of\s+Technology|Bachelor\s+of\s+Engineering|"
    r"M\.?E\.?|M\.?Tech\.?|Master\s+of\s+Technology|Master\s+of\s+Engineering|"
    r"B\.?Sc\.?|B\.?S\.?|Bachelor\s+of\s+Science|"
    r"M\.?Sc\.?|M\.?S\.?|Master\s+of\s+Science|"
    r"BCA|Bachelor\s+of\s+Computer\s+Applications|"
    r"MCA|Master\s+of\s+Computer\s+Applications|"
    r"MBA|Master\s+of\s+Business\s+Administration|"
    r"BBA|Bachelor\s+of\s+Business\s+Administration|"
    r"Ph\.?D\.?|Doctor\s+of\s+Philosophy|"
    r"Diploma|Associate\s+Degree"
    r")\b",
    re.IGNORECASE,
)

INSTITUTION_KEYWORDS = re.compile(
    r"\b(University|Institute|College|School|Academy|Campus|Polytechnic|IIT|NIT|BITS|IIIT)\b",
    re.IGNORECASE,
)

CGPA_REGEX = re.compile(
    r"\b(?:CGPA|GPA|Score|Grade|Percentage)[\s:]*([0-9]+(?:\.[0-9]+)?(?:\s*/\s*[0-9]+)?%?)\b",
    re.IGNORECASE,
)

YEAR_REGEX = re.compile(r"\b(19\d{2}|20\d{2})\b")

DATE_RANGE_REGEX = re.compile(
    r"\b("
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"[\s,]+(?:19\d{2}|20\d{2})"
    r"|"
    r"(?:19\d{2}|20\d{2})"
    r")"
    r"\s*(?:-|–|—|to)\s*"
    r"("
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"[\s,]+(?:19\d{2}|20\d{2})"
    r"|"
    r"(?:19\d{2}|20\d{2})"
    r"|"
    r"Present|Current|Ongoing"
    r")\b",
    re.IGNORECASE,
)


def extract_email(text: str) -> Optional[str]:
    """Extract standard email address, stripping trailing punctuation."""
    match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b", text)
    if match:
        return match.group(0).rstrip(".,;:")
    return None


def extract_phone(text: str) -> Optional[str]:
    """
    Extract Indian (+91) or international phone numbers safely.
    Rejects short numeric codes, years, and zip codes.
    """
    # Matches optional country code, brackets, hyphens, spaces, and 10-14 digits
    matches = re.finditer(
        r"(?:(?:\+|00)\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?)?\d{3,5}[\s.-]?\d{4,5}\b",
        text,
    )
    for match in matches:
        raw = match.group(0).strip()
        # Count actual digits
        digits = re.sub(r"\D", "", raw)
        if 10 <= len(digits) <= 15:
            # Exclude obvious year ranges like 20202024
            if not (len(digits) == 8 and (digits.startswith("19") or digits.startswith("20"))):
                return raw.rstrip(".,;:")
    return None


def extract_linkedin(text: str) -> Optional[str]:
    """Extract and normalize LinkedIn profile URL."""
    match = re.search(
        r"(?:https?://)?(?:[a-zA-Z0-9-]+\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)",
        text,
        re.IGNORECASE,
    )
    if match:
        username = match.group(1).rstrip("/.,;:")
        return f"https://www.linkedin.com/in/{username}"
    return None


def extract_github(text: str) -> Optional[str]:
    """Extract and normalize GitHub profile URL."""
    match = re.search(
        r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_-]+)",
        text,
        re.IGNORECASE,
    )
    if match:
        username = match.group(1).rstrip("/.,;:")
        # Filter out generic GitHub reserved names
        if username.lower() not in {"features", "pricing", "blog", "about", "contact", "join"}:
            return f"https://github.com/{username}"
    return None


def extract_name(header_text: str) -> Optional[str]:
    """
    Suggest candidate name from header text using spaCy NER and positional heuristics.
    Returns None if confidence is insufficient to prevent false name attribution.
    """
    if not header_text or not header_text.strip():
        return None

    lines = [line.strip() for line in header_text.split("\n") if line.strip()]
    if not lines:
        return None

    # Priority 1: Check the first few lines with spaCy NER PERSON
    nlp = get_spacy_nlp()
    if nlp:
        candidate_sample = "\n".join(lines[:4])
        doc = nlp(candidate_sample)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text.strip().replace("\n", " ")
                words = name.split()
                # A realistic name is 2-4 words, contains only letters/periods/hyphens
                if 2 <= len(words) <= 4:
                    if re.match(r"^[A-Za-z\.\-\s]+$", name):
                        # Ensure no stopwords
                        if not any(w.lower() in TITLE_STOPWORDS for w in words):
                            return name

    # Priority 2: Heuristic inspection of the very first line
    first_line = lines[0]
    # Remove honorifics like Mr., Ms., Dr.
    cleaned_line = re.sub(r"^(?:mr\.|ms\.|mrs\.|dr\.)\s+", "", first_line, flags=re.IGNORECASE).strip()
    words = cleaned_line.split()

    if 2 <= len(words) <= 4:
        # Check if line does not contain numbers, emails, URLs, or title keywords
        if (
            re.match(r"^[A-Za-z\.\-\s]+$", cleaned_line)
            and not any(w.lower() in TITLE_STOPWORDS for w in words)
            and "@" not in cleaned_line
            and "http" not in cleaned_line.lower()
        ):
            return cleaned_line

    return None


def extract_contacts(header_text: str, full_text: str) -> Dict[str, Optional[str]]:
    """
    Extract contact details: name, email, phone, linkedin, github.
    """
    return {
        "name": extract_name(header_text),
        "email": extract_email(full_text),
        "phone": extract_phone(full_text),
        "linkedin": extract_linkedin(full_text),
        "github": extract_github(full_text),
    }


def extract_education(education_text: str) -> List[Dict[str, Any]]:
    """
    Extract structured education records from education section text.
    """
    if not education_text or not education_text.strip():
        return []

    records: List[Dict[str, Any]] = []
    lines = [line.strip() for line in education_text.split("\n") if line.strip()]

    # Group lines into education blocks or inspect line-by-line
    current_record: Dict[str, Any] = {
        "degree": None,
        "field_of_study": None,
        "institution": None,
        "start_year": None,
        "end_year": None,
        "grade": None,
    }

    for line in lines:
        degree_match = DEGREE_REGEX.search(line)
        institution_match = INSTITUTION_KEYWORDS.search(line)
        cgpa_match = CGPA_REGEX.search(line)
        years = YEAR_REGEX.findall(line)

        is_new_entry = False

        if degree_match:
            # If current_record already has a degree, flush it
            if current_record["degree"] is not None:
                records.append(current_record)
                current_record = {
                    "degree": None,
                    "field_of_study": None,
                    "institution": None,
                    "start_year": None,
                    "end_year": None,
                    "grade": None,
                }
            current_record["degree"] = degree_match.group(0).strip()
            # Attempt to extract field of study (e.g. "in Computer Science")
            field_match = re.search(
                r"(?:in|of)\s+([A-Za-z\s]+?)(?:,|-|from|\(|$)",
                line[degree_match.end() :],
                re.IGNORECASE,
            )
            if field_match:
                current_record["field_of_study"] = field_match.group(1).strip()

        if institution_match and not current_record["institution"]:
            current_record["institution"] = line

        if cgpa_match and not current_record["grade"]:
            current_record["grade"] = cgpa_match.group(1).strip()

        if years:
            if len(years) >= 2 and not current_record["start_year"]:
                current_record["start_year"] = int(years[0])
                current_record["end_year"] = int(years[1])
            elif len(years) == 1 and not current_record["end_year"]:
                current_record["end_year"] = int(years[0])

    if current_record["degree"] or current_record["institution"]:
        records.append(current_record)

    return records


def extract_experience(experience_text: str) -> List[Dict[str, Any]]:
    """
    Extract structured work experience entries.
    """
    if not experience_text or not experience_text.strip():
        return []

    entries: List[Dict[str, Any]] = []
    lines = [line.strip() for line in experience_text.split("\n") if line.strip()]

    current_entry: Optional[Dict[str, Any]] = None

    for line in lines:
        date_match = DATE_RANGE_REGEX.search(line)

        # A date range line often signifies a job position boundary
        if date_match:
            start_d = date_match.group(1).strip()
            end_d = date_match.group(2).strip()

            remainder = line[: date_match.start()] + " " + line[date_match.end() :]
            remainder = re.sub(r"[\s\-\|,]+", " ", remainder).strip()

            if current_entry and current_entry["start_date"] is None and not current_entry["description"]:
                current_entry["start_date"] = start_d
                current_entry["end_date"] = end_d
                if remainder and not current_entry["organization"]:
                    current_entry["organization"] = remainder
            else:
                if current_entry:
                    entries.append(current_entry)

                current_entry = {
                    "title": remainder if remainder else None,
                    "organization": None,
                    "start_date": start_d,
                    "end_date": end_d,
                    "description": "",
                }
        else:
            if current_entry:
                if not current_entry["organization"] and not line.startswith("-") and not line.startswith("*"):
                    current_entry["organization"] = line
                else:
                    cleaned_line = line.lstrip("-* ").strip()
                    if current_entry["description"]:
                        current_entry["description"] += "\n" + cleaned_line
                    else:
                        current_entry["description"] = cleaned_line
            else:
                # First line without date
                current_entry = {
                    "title": line,
                    "organization": None,
                    "start_date": None,
                    "end_date": None,
                    "description": "",
                }

    if current_entry:
        entries.append(current_entry)

    for entry in entries:
        if entry.get("title") and " at " in entry["title"]:
            parts = entry["title"].split(" at ", 1)
            entry["title"] = parts[0].strip()
            if not entry.get("organization"):
                entry["organization"] = parts[1].strip()

    return entries


def extract_projects(projects_text: str) -> List[Dict[str, Any]]:
    """
    Extract projects with titles and descriptions.
    """
    if not projects_text or not projects_text.strip():
        return []

    projects: List[Dict[str, Any]] = []
    lines = [line.strip() for line in projects_text.split("\n") if line.strip()]

    current_project: Optional[Dict[str, Any]] = None

    for line in lines:
        # A heading line without bullet is typically a project title
        if not line.startswith("-") and not line.startswith("*") and len(line.split()) <= 10:
            if current_project:
                projects.append(current_project)
            current_project = {
                "title": line,
                "description": "",
            }
        else:
            if current_project:
                cleaned_line = line.lstrip("-* ").strip()
                if current_project["description"]:
                    current_project["description"] += "\n" + cleaned_line
                else:
                    current_project["description"] = cleaned_line
            else:
                current_project = {
                    "title": line.lstrip("-* ").strip(),
                    "description": "",
                }

    if current_project:
        projects.append(current_project)

    return projects


def extract_certifications(cert_text: str) -> List[Dict[str, Any]]:
    """
    Extract certification items line by line.
    """
    if not cert_text or not cert_text.strip():
        return []

    certifications: List[Dict[str, Any]] = []
    lines = [line.strip() for line in cert_text.split("\n") if line.strip()]

    for line in lines:
        cleaned = line.lstrip("-* ").strip()
        if not cleaned:
            continue

        issuer = None
        name = cleaned

        # Common format: "AWS Solutions Architect - Amazon Web Services"
        if " - " in cleaned:
            parts = cleaned.split(" - ", 1)
            name = parts[0].strip()
            issuer = parts[1].strip()
        elif " by " in cleaned.lower():
            idx = cleaned.lower().index(" by ")
            name = cleaned[:idx].strip()
            issuer = cleaned[idx + 4 :].strip()

        certifications.append({
            "name": name,
            "issuer": issuer,
        })

    return certifications


def extract_languages(languages_text: str) -> List[str]:
    """
    Extract spoken/written languages, excluding programming languages.
    """
    if not languages_text or not languages_text.strip():
        return []

    found_languages: List[str] = []
    tokens = re.split(r"[,;\n/|]+", languages_text.lower())

    for token in tokens:
        clean_tok = re.sub(r"[^a-z]", "", token.strip())
        if clean_tok in SPOKEN_LANGUAGES and clean_tok.capitalize() not in found_languages:
            found_languages.append(clean_tok.capitalize())

    return found_languages


def extract_achievements(achievements_text: str) -> List[str]:
    """
    Extract achievement points from achievements section.
    """
    if not achievements_text or not achievements_text.strip():
        return []

    lines = [line.strip().lstrip("-* ").strip() for line in achievements_text.split("\n") if line.strip()]
    return [l for l in lines if l]
