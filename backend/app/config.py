"""
Configuration module for the Smart Recruitment System backend.
Loads settings from environment variables and .env files using pydantic-settings.
"""

import sys

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings schema.
    Values can be overridden by environment variables or values in a .env file.
    """

    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/smart_recruitment",
        description="PostgreSQL connection string (e.g. postgresql://user:password@localhost:5432/dbname)",
    )

    TEST_DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/smart_recruitment_test",
        description="Separate test PostgreSQL database connection string",
    )

    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production-use-a-strong-random-string",
        description="Secret key for JWT generation and session signing",
    )

    ALGORITHM: str = Field(
        default="HS256",
        description="Algorithm used to sign JWT access tokens",
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="JWT access token lifetime in minutes",
    )

    GEMINI_API_KEY: str = Field(
        default="",
        description="Google Gemini API key for future AI interview & evaluation features",
    )

    FRONTEND_ORIGIN: str = Field(
        default="http://localhost:5173",
        description="Allowed frontend origin for Cross-Origin Resource Sharing (CORS)",
    )

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


def load_settings() -> Settings:
    """
    Instantiate and validate application settings.
    Catches validation errors and prints clear, student-friendly troubleshooting tips.
    """
    try:
        return Settings()
    except ValidationError as exc:
        print("\n" + "=" * 65, file=sys.stderr)
        print("[CONFIG ERROR] Could not load application settings:", file=sys.stderr)

        for error in exc.errors():
            loc = " -> ".join(str(part) for part in error.get("loc", []))
            msg = error.get("msg", "Invalid value")
            print(
                f"  * Variable '{loc}': {msg}",
                file=sys.stderr,
            )

        print(
            "\nTroubleshooting tip: Check your .env file and ensure values match .env.example",
            file=sys.stderr,
        )
        print("=" * 65 + "\n", file=sys.stderr)
        raise exc


# Singleton instance to import throughout the backend
settings = load_settings()