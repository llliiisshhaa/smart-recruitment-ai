"""
Job Description Analyzer package.
Provides rule-based attribute extraction, importance suggestion, and fairness auditing
for recruiter job descriptions without calling external LLMs.
"""

from app.ai.services.job_analyzer.analyzer import (
    ANALYZER_VERSION,
    analyze_job_description,
)

__all__ = [
    "ANALYZER_VERSION",
    "analyze_job_description",
]
