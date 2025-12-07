"""
Application settings loaded from environment variables.

Uses Pydantic Settings for type-safe configuration management.
All settings are loaded from .env file or environment variables.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with validation.

    Attributes:
        google_cloud_project: GCP project ID
        google_cloud_region: GCP region for Vertex AI
        google_application_credentials: Path to service account key (Vertex AI)
        google_oauth_credentials: Path to OAuth credentials (Workspace)
        orchestrator_model: Model for orchestrator agent
        specialist_model: Model for specialist agents
        log_level: Logging level
        environment: Deployment environment
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields
    )

    # Google Cloud Configuration
    google_cloud_project: str = Field(
        ...,
        alias="GOOGLE_CLOUD_PROJECT",
        description="Google Cloud Project ID",
        min_length=1,
    )
    google_cloud_region: str = Field(
        default="us-central1",
        description="GCP region for Vertex AI resources",
    )

    # Authentication Paths
    google_application_credentials: Path = Field(
        default=Path("vertex-key.json"),
        description="Path to service account key for Vertex AI",
    )
    google_oauth_credentials: Path = Field(
        default=Path("credentials.json"),
        description="Path to OAuth 2.0 credentials for Workspace APIs",
    )

    # Model Configuration
    orchestrator_model: str = Field(
        default="gemini-2.0-flash-exp",
        description="Model ID for orchestrator agent (Gemini Pro recommended)",
    )
    specialist_model: str = Field(
        default="gemini-2.0-flash-exp",
        description="Model ID for specialist agents (Gemini Flash recommended)",
    )

    # Data Layer
    vertex_ai_search_datastore_id: str | None = Field(
        default=None,
        description="Vertex AI Search datastore ID for curriculum documents",
    )
    bigquery_dataset_id: str | None = Field(
        default=None,
        description="BigQuery dataset ID for student records",
    )

    # Application Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment",
    )

    @field_validator("google_application_credentials", "google_oauth_credentials")
    @classmethod
    def validate_credential_paths(cls, v: Path) -> Path:
        """Validate that credential files exist."""
        if not v.exists():
            raise ValueError(f"Credential file not found: {v}")
        return v

    @field_validator("google_cloud_project")
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        """Validate GCP project ID format."""
        if not v or len(v) < 6:
            raise ValueError("Invalid Google Cloud Project ID")
        return v

    def __repr__(self) -> str:
        """Safe repr that doesn't expose credentials."""
        return (
            f"Settings(project={self.google_cloud_project}, "
            f"region={self.google_cloud_region}, "
            f"environment={self.environment})"
        )


# Singleton instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Get application settings singleton.

    Returns:
        Validated settings instance

    Example:
        >>> settings = get_settings()
        >>> print(settings.google_cloud_project)
        'edu-teacher-assistant-prod'
    """
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings
