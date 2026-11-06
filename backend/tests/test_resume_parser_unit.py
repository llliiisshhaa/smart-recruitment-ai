"""
Unit tests for the non-LLM resume parser modules:
- Document extraction (PDF, DOCX, tables, corrupt files, image-only, page limits)
- Text cleaning (whitespace, bullets, hyphenation, special symbols preservation)
- Section detection (headings, variations, ordering, sentences containing keywords)
- Entity extraction (contacts, education, experience, projects, certifications, languages, achievements, privacy)
- Skill extraction (aliases, canonical taxonomy, contextual support, evidence snippets)
"""

from pathlib import Path
import docx
import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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
from app.ai.services.resume_parser.exceptions import (
    CorruptFileError,
    FileNotFoundError as ParserFileNotFoundError,
    NoExtractableTextError,
    PageLimitExceededError,
    UnsupportedFileTypeError,
)
from app.ai.services.resume_parser.extract import extract_text
from app.ai.services.resume_parser.parser import parse_resume
from app.ai.services.resume_parser.sections import extract_sections
from app.ai.services.resume_parser.skills import extract_skills


# ==============================================================================
# A. EXTRACTION TESTS
# ==============================================================================

def test_extract_valid_pdf(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.drawString(100, 750, "John Doe")
    c.drawString(100, 730, "Software Engineer with experience in Python and FastAPI")
    c.save()

    text = extract_text(pdf_path)
    assert "John Doe" in text
    assert "Python and FastAPI" in text


def test_extract_valid_docx(tmp_path):
    docx_path = tmp_path / "sample.docx"
    doc = docx.Document()
    doc.add_paragraph("Jane Smith")
    doc.add_paragraph("Full Stack Developer skilled in React and TypeScript")
    doc.save(str(docx_path))

    text = extract_text(docx_path)
    assert "Jane Smith" in text
    assert "React and TypeScript" in text


def test_extract_docx_with_tables(tmp_path):
    docx_path = tmp_path / "table_sample.docx"
    doc = docx.Document()
    doc.add_paragraph("Academic Background")
    tbl = doc.add_table(rows=2, cols=2)
    tbl.cell(0, 0).text = "B.Tech Computer Science"
    tbl.cell(0, 1).text = "ABC University"
    tbl.cell(1, 0).text = "Year: 2020-2024"
    tbl.cell(1, 1).text = "CGPA: 8.9"
    doc.save(str(docx_path))

    text = extract_text(docx_path)
    assert "Academic Background" in text
    assert "B.Tech Computer Science" in text
    assert "ABC University" in text


def test_extract_empty_docx_raises_no_extractable_text(tmp_path):
    docx_path = tmp_path / "empty.docx"
    doc = docx.Document()
    doc.save(str(docx_path))

    with pytest.raises(NoExtractableTextError) as exc_info:
        extract_text(docx_path)
    assert "no extractable text" in str(exc_info.value).lower()


def test_extract_corrupt_pdf(tmp_path):
    corrupt_pdf = tmp_path / "corrupt.pdf"
    corrupt_pdf.write_bytes(b"%PDF-1.4\nCorrupted binary content that cannot be parsed by pdfplumber")

    with pytest.raises(CorruptFileError):
        extract_text(corrupt_pdf)


def test_extract_corrupt_docx(tmp_path):
    corrupt_docx = tmp_path / "corrupt.docx"
    corrupt_docx.write_bytes(b"PK\x03\x04corrupted zip payload")

    with pytest.raises(CorruptFileError):
        extract_text(corrupt_docx)


def test_extract_image_only_pdf_raises_no_extractable_text(tmp_path):
    pdf_path = tmp_path / "image_only.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    # Draw geometric shapes simulating a scanned bitmap image with no text layer
    c.rect(50, 50, 400, 600, stroke=1, fill=1)
    c.circle(200, 400, 50, stroke=1, fill=1)
    c.save()

    with pytest.raises(NoExtractableTextError) as exc_info:
        extract_text(pdf_path)
    assert "no extractable text" in str(exc_info.value).lower()


def test_extract_pdf_exceeding_page_limit_raises_error(tmp_path):
    pdf_path = tmp_path / "eleven_pages.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    for i in range(11):
        c.drawString(100, 700, f"Page number {i + 1}")
        c.showPage()
    c.save()

    with pytest.raises(PageLimitExceededError) as exc_info:
        extract_text(pdf_path)
    assert "exceeds" in str(exc_info.value).lower()


def test_extract_unsupported_file_type(tmp_path):
    txt_path = tmp_path / "resume.txt"
    txt_path.write_text("Plain text resume")

    with pytest.raises(UnsupportedFileTypeError) as exc_info:
        extract_text(txt_path)
    assert "unsupported" in str(exc_info.value).lower()


def test_extract_missing_file_raises_error(tmp_path):
    missing_path = tmp_path / "non_existent.pdf"

    with pytest.raises(ParserFileNotFoundError) as exc_info:
        extract_text(missing_path)
    assert "not found" in str(exc_info.value).lower()


# ==============================================================================
# B. TEXT CLEANING TESTS
# ==============================================================================

def test_clean_text_normalizes_whitespace_and_line_breaks():
    raw = "Line 1   with    multiple   spaces.\r\n\r\n\r\n\r\nLine 2 after excessive breaks.\t\tTabs here."
    cleaned = clean_text(raw)
    assert "Line 1 with multiple spaces." in cleaned
    assert "\n\n\n" not in cleaned
    assert "Tabs here." in cleaned


def test_clean_text_normalizes_bullets():
    raw = "• Developed REST API\n◦ Implemented authentication\n▪ Built CI/CD pipeline"
    cleaned = clean_text(raw)
    assert "- Developed REST API" in cleaned
    assert "- Implemented authentication" in cleaned
    assert "- Built CI/CD pipeline" in cleaned


def test_clean_text_reconnects_hyphenated_line_breaks():
    raw = "Extensive experi-\nence in microservices archi-\ntecture and imple-\nmentation."
    cleaned = clean_text(raw)
    assert "experience" in cleaned
    assert "architecture" in cleaned
    assert "implementation" in cleaned


def test_clean_text_preserves_special_technical_terms():
    raw = (
        "Experienced in C++, C#, .NET Core, Node.js, Next.js, and CI/CD automation.\n"
        "Contributed to open source on GitHub using JavaScript and TypeScript."
    )
    cleaned = clean_text(raw)
    assert "C++" in cleaned
    assert "C#" in cleaned
    assert ".NET Core" in cleaned
    assert "Node.js" in cleaned
    assert "Next.js" in cleaned
    assert "CI/CD" in cleaned
    assert "GitHub" in cleaned
    assert "JavaScript" in cleaned


# ==============================================================================
# C. SECTION DETECTION TESTS
# ==============================================================================

def test_extract_sections_recognizes_canonical_headings():
    resume_text = """John Doe
john@example.com

SUMMARY
Passionate full stack developer with 3 years experience.

EDUCATION
B.Tech in Computer Science
XYZ Institute of Technology

TECHNICAL SKILLS
Python, JavaScript, React, PostgreSQL

WORK EXPERIENCE
Senior Engineer at Tech Corp
2021 - Present
- Built scalable web APIs.

PROJECTS
Smart Recruitment AI
- Designed deterministic resume parser.

CERTIFICATIONS
AWS Certified Solutions Architect

LANGUAGES
English, Hindi
"""
    sections = extract_sections(resume_text)
    assert "header" in sections
    assert "John Doe" in sections["header"]
    assert "summary" in sections
    assert "education" in sections
    assert "skills" in sections
    assert "experience" in sections
    assert "projects" in sections
    assert "certifications" in sections
    assert "languages" in sections


def test_extract_sections_case_insensitive_and_alternative_headings():
    resume_text = """Profile Header Text

Professional Summary:
Dynamic backend developer.

Educational Qualifications:
Master of Science in Information Technology

Core Competencies:
Docker, Kubernetes, AWS

Professional Background:
Software Developer at Acme
"""
    sections = extract_sections(resume_text)
    assert "summary" in sections
    assert "Dynamic backend developer." in sections["summary"]
    assert "education" in sections
    assert "Master of Science" in sections["education"]
    assert "skills" in sections
    assert "experience" in sections


def test_extract_sections_does_not_false_trigger_on_ordinary_sentences():
    resume_text = """Header Information

SUMMARY
I have extensive technical skills in Python.
During my work experience at Google, I managed several projects.
"""
    sections = extract_sections(resume_text)
    assert "skills" not in sections
    assert "projects" not in sections
    assert "summary" in sections
    assert "I have extensive technical skills in Python." in sections["summary"]


def test_extract_sections_without_headings_preserves_all_text_in_header():
    resume_text = "John Doe\nExperienced Python developer with 5 years in fintech."
    sections = extract_sections(resume_text)
    assert "header" in sections
    assert "John Doe" in sections["header"]
    assert len(sections) == 1


# ==============================================================================
# D. ENTITY EXTRACTION TESTS
# ==============================================================================

def test_extract_contacts_email_phone_urls():
    text = (
        "Alice Smith\n"
        "Email: alice.smith@example.com; Phone: +91 98765 43210.\n"
        "https://www.linkedin.com/in/alicesmith/ and https://github.com/alicesmith"
    )
    contacts = extract_contacts(header_text="Alice Smith", full_text=text)
    assert contacts["name"] == "Alice Smith"
    assert contacts["email"] == "alice.smith@example.com"
    assert "98765" in contacts["phone"]
    assert contacts["linkedin"] == "https://www.linkedin.com/in/alicesmith"
    assert contacts["github"] == "https://github.com/alicesmith"


def test_extract_candidate_name_conservative_fallback():
    # If the header has obvious job titles or no clear name, return None
    contacts = extract_contacts(header_text="Software Engineer Resume", full_text="")
    assert contacts["name"] is None


def test_extract_education_structure():
    edu_text = (
        "Bachelor of Technology in Computer Science\n"
        "Indian Institute of Technology\n"
        "2018 - 2022\n"
        "CGPA: 8.7 / 10"
    )
    records = extract_education(edu_text)
    assert len(records) >= 1
    assert "Bachelor of Technology" in records[0]["degree"]
    assert records[0]["start_year"] == 2018
    assert records[0]["end_year"] == 2022
    assert "8.7" in records[0]["grade"]


def test_extract_experience_structure():
    exp_text = (
        "Software Engineer at Acme Corp\n"
        "Jan 2022 - Present\n"
        "- Developed backend microservices using Python and FastAPI.\n"
        "- Optimized PostgreSQL database queries."
    )
    records = extract_experience(exp_text)
    assert len(records) >= 1
    assert "Jan 2022" in records[0]["start_date"]
    assert "Present" in records[0]["end_date"]
    assert "FastAPI" in records[0]["description"]


def test_extract_projects_structure():
    proj_text = (
        "Smart Recruitment Engine\n"
        "- Designed offline resume parser in Python.\n"
        "- Integrated with FastAPI backend."
    )
    projects = extract_projects(proj_text)
    assert len(projects) >= 1
    assert "Smart Recruitment Engine" in projects[0]["title"]
    assert "FastAPI" in projects[0]["description"]


def test_extract_certifications_and_languages():
    cert_text = "AWS Certified Developer - Amazon Web Services\nCertified Kubernetes Administrator"
    certs = extract_certifications(cert_text)
    assert len(certs) == 2
    assert certs[0]["name"] == "AWS Certified Developer"
    assert certs[0]["issuer"] == "Amazon Web Services"

    lang_text = "English, Hindi, Spanish"
    languages = extract_languages(lang_text)
    assert "English" in languages
    assert "Hindi" in languages
    assert "Spanish" in languages
    # Ensure programming languages are not confused with spoken languages
    assert "Python" not in extract_languages("Python, Java, English")


def test_privacy_restriction_no_prohibited_attributes():
    resume_text = (
        "John Doe\n"
        "Gender: Male, DOB: 01/01/1995, Religion: None, Nationality: Indian\n"
        "Marital Status: Single\n"
        "Skills: Python, React"
    )
    result = parse_resume(tmp_file_with_text(resume_text))
    # Structured schema must not contain demographic keys
    assert "gender" not in result
    assert "dob" not in result
    assert "religion" not in result
    assert "marital_status" not in result
    assert "nationality" not in result


# Helper for tests needing a file path
def tmp_file_with_text(text: str) -> Path:
    import tempfile
    f = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
    f.close()
    p = Path(f.name)
    doc = docx.Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    doc.save(str(p))
    return p


# ==============================================================================
# E. SKILL EXTRACTION TESTS
# ==============================================================================

def test_skill_extraction_aliases_and_case_insensitivity():
    sections = {
        "skills": "Experienced with JS, TS, Postgres, MongoDB, Node JS, and ReactJS.",
    }
    extracted = extract_skills(sections)
    extracted_names = {s["name"] for s in extracted}

    assert "javascript" in extracted_names  # from 'JS'
    assert "typescript" in extracted_names  # from 'TS'
    assert "postgresql" in extracted_names  # from 'Postgres'
    assert "mongodb" in extracted_names     # from 'MongoDB'
    assert "node.js" in extracted_names     # from 'Node JS'
    assert "react" in extracted_names       # from 'ReactJS'


def test_skill_extraction_punctuation_heavy_terms():
    sections = {
        "skills": "Core skills include C++, C#, .NET, CI/CD, Next.js, and Node.js.",
    }
    extracted = extract_skills(sections)
    extracted_names = {s["name"] for s in extracted}

    assert "c++" in extracted_names
    assert "c#" in extracted_names
    assert "ci/cd" in extracted_names
    assert "next.js" in extracted_names
    assert "node.js" in extracted_names


def test_skill_extraction_false_positive_prevention():
    # 'R' or 'Go' or 'C' must not match inside ordinary words
    sections = {
        "summary": "Going forward, our algorithm achieved good results with clear communication.",
    }
    extracted = extract_skills(sections)
    extracted_names = {s["name"] for s in extracted}

    # "Going", "algorithm", "good" should NOT trigger 'go' or 'c'
    assert "go" not in extracted_names
    assert "c" not in extracted_names
    assert "communication" in extracted_names


def test_skill_contextual_support_calculation():
    sections = {
        "skills": "Python, Docker, SQL",
        "projects": "Built an analytics platform using Python and Docker.",
        "experience": "Maintained backend services.",
    }
    extracted = extract_skills(sections)
    skill_map = {s["name"]: s for s in extracted}

    # Python and Docker appear in projects -> supported_by_context = True
    assert skill_map["python"]["supported_by_context"] is True
    assert skill_map["docker"]["supported_by_context"] is True
    # SQL appears ONLY in skills -> supported_by_context = False
    assert skill_map["sql"]["supported_by_context"] is False


def test_skill_evidence_sentence_extracted():
    sections = {
        "projects": "- Developed automated data-processing pipelines using Python 3 and Pandas.",
    }
    extracted = extract_skills(sections)
    python_skill = next(s for s in extracted if s["name"] == "python")

    assert "data-processing pipelines" in python_skill["evidence_text"]
    assert len(python_skill["evidence_text"]) <= 250

