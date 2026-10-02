"""
Main FastAPI application entrypoint for Smart Recruitment System.
Configures CORS, database dependencies, and base endpoints such as /health.
"""

import logging
from typing import Dict
from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.api.auth import router as auth_router

# Configure logger
logger = logging.getLogger("uvicorn.error")

# Initialize FastAPI application
app = FastAPI(
    title="Smart Recruitment System API",
    description="AI Virtual Interview Platform backend API",
    version="0.1.0",
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
