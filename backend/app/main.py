"""
Main FastAPI application entrypoint for Smart Recruitment System.
Configures CORS, database dependencies, and base endpoints such as /health.
"""

import logging
from typing import Dict
from fastapi import FastAPI, Depends, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.api.auth import router as auth_router
from app.api.routes.resume import router as resume_router
from app.api.routes.candidate import router as candidate_router
from app.api.routes.skills import router as skills_router
from app.api.routes.recruiters import router as recruiters_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.applications import router as applications_router

# Configure logger
logger = logging.getLogger("uvicorn.error")

# Initialize FastAPI application
app = FastAPI(
    title="Smart Recruitment System API",
    description="AI Virtual Interview Platform backend API",
    version="0.1.0",
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Ensure no internal server errors leak stack traces to callers.
    Rethrows Starlette/FastAPI HTTP exceptions and validation errors so their
    custom codes and headers are preserved.
    """
    if isinstance(exc, (StarletteHTTPException, RequestValidationError)):
        raise exc

    logger.error("Unhandled internal server error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred"},
    )

# Configure CORS using origin from config (not hardcoded)
# Support the specified frontend origin (e.g., http://localhost:5173)
origins = [
    settings.FRONTEND_ORIGIN.rstrip("/"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication routes
app.include_router(auth_router)

# Resume routes
app.include_router(resume_router)

# Candidate routes
app.include_router(candidate_router)

# Skills routes
app.include_router(skills_router)

# Recruiter routes
app.include_router(recruiters_router)

# Jobs routes
app.include_router(jobs_router)

# Applications routes
app.include_router(applications_router)


@app.get("/", tags=["Root"])
def read_root() -> Dict[str, str]:
    """
    Root greeting endpoint to easily verify the server is running.
    """
    return {"message": "Welcome to the Smart Recruitment System API"}


@app.get(
    "/health",
    tags=["Monitoring"],
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, str],
)
def health_check(db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Health check endpoint that verifies API server status and checks
    database connectivity by executing a lightweight query (`SELECT 1`).

    Does not crash if the database is unreachable or down, gracefully
    returning 'unavailable' for the database key.

    Returns:
        {"status": "ok", "database": "connected" | "unavailable"}
    """
    database_status = "unavailable"
    try:
        # Run a trivial query to verify that the database is reachable
        result = db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            database_status = "connected"
    except Exception as exc:
        # Log warning but do NOT crash the /health endpoint
        logger.warning("Database connectivity check failed: %s", exc)
        database_status = "unavailable"

    return {
        "status": "ok",
        "database": database_status,
    }
