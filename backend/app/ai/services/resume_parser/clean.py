"""
Text cleaning and normalization module for extracted resume text.
Preserves technical terms (C++, C#, .NET, Node.js, Next.js, CI/CD) while normalizing whitespace,
line endings, bullet points, hyphenated line wraps, and Unicode artifacts.
"""

import re
import unicodedata


# Bullet characters commonly found in PDFs and Word documents
BULLET_CHARS = [
    "\u2022",  # Bullet •
    "\u2023",  # Triangular bullet ‣
    "\u2043",  # Hyphen bullet ⁃
    "\u2219",  # Bullet operator ∙
    "\u25cb",  # White circle ○
    "\u25cf",  # Black circle ●
    "\u25e6",  # White bullet ◦
    "\u25aa",  # Black small square ▪
    "\u25ab",  # White small square ▫
    "\u25b8",  # Black right-pointing small triangle ▸
    "\u25c6",  # Black diamond ◆
    "\u2713",  # Check mark ✓
    "\u2714",  # Heavy check mark ✔
]

BULLET_REGEX = re.compile(f"[{''.join(re.escape(c) for c in BULLET_CHARS)}]")


def clean_text(text: str) -> str:
    """
    Normalize raw extracted resume text while strictly preserving technical terms.

    Operations:
    1. Standardize line breaks (\r\n -> \n, \r -> \n).
    2. Normalize Unicode spaces and quotes (e.g. \u00a0 to space, curly quotes to straight).
    3. Reconnect words broken by hyphenation at line breaks (e.g. "experi-\\nence" -> "experience").
    4. Normalize bullet points to consistent "- " prefix.
    5. Collapse multiple horizontal spaces and tabs without breaking line breaks.
    6. Eliminate excessive blank lines (max 2 consecutive newlines).
    7. Retain technical symbols (e.g., C++, C#, .NET, CI/CD, Node.js, Next.js).
    """
    if not text:
        return ""

    # 1. Standardize line endings
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Normalize common Unicode characters
    # Non-breaking space
    cleaned = cleaned.replace("\u00a0", " ").replace("\u200b", "")

    # Smart/curly quotes and dashes
    cleaned = (
        cleaned.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2013", "-")
        .replace("\u2014", "-")
    )

    # 3. De-hyphenate words broken across lines (e.g., "develop-\nment" -> "development")
    # Only rejoin lowercase or titlecase word stems, never technical names like CI/CD or hyphenated terms
    cleaned = re.sub(r"([A-Za-z]{2,})-\n([a-z]{2,})", r"\1\2", cleaned)

    # 4. Standardize bullets: replace recognized bullet symbols with "- "
    cleaned = BULLET_REGEX.sub("- ", cleaned)

    # 5. Clean whitespace per line
    lines = []
    for line in cleaned.split("\n"):
        # Replace tabs and multiple consecutive horizontal spaces with a single space
        normalized_line = re.sub(r"[ \t]+", " ", line).strip()
        lines.append(normalized_line)

    rejoined = "\n".join(lines)

    # 6. Collapse excessive empty lines (3 or more newlines become 2)
    rejoined = re.sub(r"\n{3,}", "\n\n", rejoined)

    return rejoined.strip()

