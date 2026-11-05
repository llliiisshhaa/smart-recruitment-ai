"""
Text extraction module for PDF and DOCX documents.
Enforces safety limits (file existence, max 10 pages, no-text detection, corruption handling).
"""

from pathlib import Path
from typing import List, Union
import docx
from docx.table import Table
from docx.text.paragraph import Paragraph
import pdfplumber

from app.ai.services.resume_parser.exceptions import (
    CorruptFileError,
    FileNotFoundError as ParserFileNotFoundError,
    NoExtractableTextError,
    PageLimitExceededError,
    UnsupportedFileTypeError,
)

MAX_PDF_PAGES = 10


def extract_text_from_pdf(path: Path) -> str:
    """
    Extract text content from all pages of a PDF document using pdfplumber.

    Enforces a strict 10-page limit and checks for empty/image-only documents.
    """
    try:
        with pdfplumber.open(path) as pdf:
            # Check page limit before extracting text
            num_pages = len(pdf.pages)
            if num_pages > MAX_PDF_PAGES:
                raise PageLimitExceededError(
                    f"PDF document exceeds the maximum limit of {MAX_PDF_PAGES} pages (found {num_pages} pages)."
                )

            pages_text: List[str] = []
            for page in pdf.pages:
                text = page.extract_text()
                if text and text.strip():
                    pages_text.append(text.strip())

            full_text = "\n\n".join(pages_text).strip()

            if not full_text:
                raise NoExtractableTextError(
                    "The document contains no extractable text. Please ensure the PDF is not an image scan."
                )

            return full_text

    except (PageLimitExceededError, NoExtractableTextError):
        raise
    except Exception as exc:
        raise CorruptFileError(f"Failed to read PDF document: corrupted or unreadable.") from exc


def extract_text_from_docx(path: Path) -> str:
    """
    Extract text from a DOCX document in document order, including paragraphs and tables.
    """
    try:
        doc = docx.Document(str(path))
        lines: List[str] = []

        # Iterate through elements in document order
        for child in doc.element.body:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "p":
                p = Paragraph(child, doc)
                text = p.text.strip()
                if text:
                    lines.append(text)
            elif tag == "tbl":
                tbl = Table(child, doc)
                for row in tbl.rows:
                    row_cells_text = []
                    for cell in row.cells:
                        c_text = cell.text.strip()
                        if c_text and c_text not in row_cells_text:
                            row_cells_text.append(c_text)
                    if row_cells_text:
                        lines.append(" | ".join(row_cells_text))

        full_text = "\n".join(lines).strip()

        if not full_text:
            raise NoExtractableTextError("The document contains no extractable text.")

        return full_text

    except NoExtractableTextError:
        raise
    except Exception as exc:
        raise CorruptFileError("Failed to read DOCX document: corrupted or unreadable.") from exc


def extract_text(file_path: Union[str, Path]) -> str:
    """
    Extract plain text from a supported resume document (PDF or DOCX).

    Args:
        file_path: Filesystem path to the stored document.

    Returns:
        Extracted plain text.

    Raises:
        ParserFileNotFoundError: If the file does not exist.
        UnsupportedFileTypeError: If the format is not .pdf or .docx.
        PageLimitExceededError: If a PDF exceeds 10 pages.
        NoExtractableTextError: If no extractable text was found.
        CorruptFileError: If the document is damaged or unreadable.
    """
    path = Path(file_path)

    if not path.is_file():
        raise ParserFileNotFoundError("Resume file not found.")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    elif suffix == ".docx":
        return extract_text_from_docx(path)
    else:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{suffix}'. Only PDF and DOCX files are allowed."
        )

