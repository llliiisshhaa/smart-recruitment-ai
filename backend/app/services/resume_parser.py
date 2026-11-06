"""
Consolidated resume parser service interface.
Delegates to the canonical app.ai.services.resume_parser package, preserving
backward compatibility for existing callers of extract_text_from_pdf.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from app.ai.services.resume_parser import extract_text, parse_resume
from app.ai.services.resume_parser.exceptions import (
    CorruptFileError,
    FileNotFoundError as ParserFileNotFoundError,
    NoExtractableTextError,
    PageLimitExceededError,
    ResumeParserError,
    UnsupportedFileTypeError,
)


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF resume. Preserved for backward compatibility.
    Delegates to the unified extraction engine.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")
    return extract_text(path)


__all__ = [
    "extract_text_from_pdf",
    "extract_text",
    "parse_resume",
    "ResumeParserError",
    "ParserFileNotFoundError",
    "UnsupportedFileTypeError",
    "PageLimitExceededError",
    "NoExtractableTextError",
    "CorruptFileError",
]
