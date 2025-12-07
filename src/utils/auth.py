# src/utils/auth.py
"""
Authentication utilities for Google Cloud and Workspace APIs.

Handles:
- OAuth 2.0 for Workspace APIs (Docs, Forms, Gmail, Drive)
- Service Account for Vertex AI
"""

import os
from pathlib import Path
from typing import Final

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import vertexai

from src.config.settings import Settings
from src.utils.logger import logger

# Workspace API scopes
WORKSPACE_SCOPES: Final[list[str]] = [
    "https://www.googleapis.com/auth/documents",  # Google Docs
    "https://www.googleapis.com/auth/forms.body",  # Google Forms
    "https://www.googleapis.com/auth/drive.file",  # Google Drive (created files)
    "https://www.googleapis.com/auth/gmail.compose",  # Gmail (compose/draft)
]


def authenticate_workspace(settings: Settings) -> Credentials:
    """
    Authenticate user for Google Workspace APIs using OAuth 2.0.

    Flow:
    1. Check for existing token.json
    2. Refresh if expired
    3. Launch browser for new authentication if needed
    4. Save token for future use

    Args:
        settings: Application settings with credential paths

    Returns:
        Valid OAuth2 credentials

    Raises:
        FileNotFoundError: If OAuth credentials file doesn't exist
        Exception: If authentication fails

    Example:
        >>> settings = get_settings()
        >>> creds = authenticate_workspace(settings)
        >>> # Use creds with Workspace APIs
    """
    creds: Credentials | None = None
    token_path = Path("token.json")

    # Load existing token
    if token_path.exists():
        logger.info("Loading existing OAuth token", path=str(token_path))
        creds = Credentials.from_authorized_user_file(str(token_path), WORKSPACE_SCOPES)  # type: ignore[no-untyped-call]

    # Refresh or authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired OAuth token")
            creds.refresh(Request())  # type: ignore[no-untyped-call]
        else:
            if not settings.google_oauth_credentials.exists():
                raise FileNotFoundError(
                    f"OAuth credentials not found at: {settings.google_oauth_credentials}\n"
                    "Download from: https://console.cloud.google.com/apis/credentials"
                )

            logger.info(
                "Starting OAuth flow", credentials_path=str(settings.google_oauth_credentials)
            )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(settings.google_oauth_credentials),
                WORKSPACE_SCOPES,
            )
            # run_local_server returns Credentials (may be broader type, but we cast it)
            new_creds = flow.run_local_server(port=0)
            creds = new_creds
            logger.info("OAuth authentication successful")

        # Save token - creds is guaranteed non-None here
        assert creds is not None
        token_path.write_text(creds.to_json())  # type: ignore[no-untyped-call]
        logger.info("OAuth token saved", path=str(token_path))
    else:
        logger.info("Using valid OAuth token")

    assert creds is not None
    return creds


def initialize_vertex_ai(settings: Settings) -> None:
    """
    Initialize Vertex AI with service account credentials.

    Sets GOOGLE_APPLICATION_CREDENTIALS environment variable and
    initializes the Vertex AI SDK.

    Args:
        settings: Application settings with GCP configuration

    Raises:
        FileNotFoundError: If service account key doesn't exist

    Example:
        >>> settings = get_settings()
        >>> initialize_vertex_ai(settings)
        >>> # Now can use Vertex AI services
    """
    if not settings.google_application_credentials.exists():
        raise FileNotFoundError(
            f"Service account key not found: {settings.google_application_credentials}\n"
            "Create one at: https://console.cloud.google.com/iam-admin/serviceaccounts"
        )

    # Set environment variable for Google Cloud SDK
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(
        settings.google_application_credentials.absolute()
    )

    logger.info(
        "Initializing Vertex AI",
        project=settings.google_cloud_project,
        region=settings.google_cloud_region,
    )

    # Initialize Vertex AI SDK
    vertexai.init(
        project=settings.google_cloud_project,
        location=settings.google_cloud_region,
    )

    logger.info("Vertex AI initialized successfully")
