"""
Pagination utilities for API endpoints.
Provides standardized validation and response containers for paginated queries.
"""

from typing import Generic, List, Tuple, TypeVar
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized envelope for paginated collection responses."""

    items: List[T] = Field(..., description="List of items for the requested page")
    total: int = Field(..., description="Total number of items matching the query")
    limit: int = Field(..., description="Maximum items per page applied")
    offset: int = Field(..., description="Number of items skipped")


def validate_pagination_params(
    limit: int = 20,
    offset: int = 0,
    max_limit: int = 50,
) -> Tuple[int, int]:
    """
    Validate and clamp pagination parameters.

    Args:
        limit: Requested page size. Must be > 0. Clamped to max_limit.
        offset: Requested item offset. Must be >= 0.
        max_limit: Maximum allowed limit value.

    Returns:
        Tuple of (clamped_limit, offset)
    """
    if limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be a positive integer.",
        )

    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offset cannot be negative.",
        )

    clamped_limit = min(limit, max_limit)
    return clamped_limit, offset
