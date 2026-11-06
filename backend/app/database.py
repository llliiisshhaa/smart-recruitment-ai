"""
Database configuration and session management using SQLAlchemy.
Provides the engine, SessionLocal factory, Base class for models,
and a get_db dependency for FastAPI routes.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

# Normalize postgresql:// to postgresql+psycopg2:// if needed,
# ensuring seamless compatibility with psycopg2-binary
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

# Create database engine
# pool_pre_ping=True tests connections for liveness before vending them from the pool
engine = create_engine(
    database_url,
    pool_pre_ping=True,
)

# SessionLocal class: each instance will be a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class which future database models will inherit from
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session per request.
    Ensures that the database session is always closed after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
