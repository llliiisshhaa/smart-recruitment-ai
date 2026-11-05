"""
Custom exceptions for resume parsing service.
"""


class ResumeParserError(Exception):
    """Base exception for all resume parser operations."""
    pass


class FileNotFoundError(ResumeParserError):
    """Raised when the resume file does not exist on disk."""
    pass


class UnsupportedFileTypeError(ResumeParserError):
    """Raised when the document extension/format is not supported."""
    pass


class PageLimitExceededError(ResumeParserError):
    """Raised when a PDF document exceeds the maximum permitted page limit."""
    pass


class NoExtractableTextError(ResumeParserError):
    """Raised when a document contains no extractable text layer (e.g. image-only PDF or empty file)."""
    pass


class CorruptFileError(ResumeParserError):
    """Raised when a document is damaged, malformed, or cannot be read."""
    pass

