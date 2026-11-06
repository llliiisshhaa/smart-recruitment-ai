from io import BytesIO
import zipfile

import pytest
from fastapi import HTTPException

from app.api.routes.resume import validate_resume_content


def create_docx_bytes():
    """Create a minimal DOCX-like ZIP containing the main document."""
    buffer = BytesIO()

    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "word/document.xml",
            '<?xml version="1.0"?><document></document>',
        )

    return buffer.getvalue()


def test_valid_pdf_signature_is_accepted():
    content = b"%PDF-1.7\nExample PDF content"

    validate_resume_content(content, ".pdf")


def test_invalid_pdf_content_is_rejected():
    content = b"This is not a PDF file."

    with pytest.raises(HTTPException) as exc_info:
        validate_resume_content(content, ".pdf")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "The uploaded file is not a valid PDF."


def test_valid_docx_structure_is_accepted():
    content = create_docx_bytes()

    validate_resume_content(content, ".docx")


def test_docx_without_word_document_is_rejected():
    buffer = BytesIO()

    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("other.txt", "Not a Word document")

    with pytest.raises(HTTPException) as exc_info:
        validate_resume_content(buffer.getvalue(), ".docx")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "The DOCX file does not contain a Word document."
    )


def test_corrupted_docx_is_rejected():
    content = b"PK this is not a valid ZIP archive"

    with pytest.raises(HTTPException) as exc_info:
        validate_resume_content(content, ".docx")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "The uploaded DOCX file is corrupted or invalid."
    )
