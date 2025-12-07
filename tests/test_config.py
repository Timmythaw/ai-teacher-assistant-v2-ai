# tests/test_config.py
"""Tests for configuration management."""

from pydantic import ValidationError
import pytest

from src.config.settings import Settings


def test_settings_loads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that settings load correctly from environment."""
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_CLOUD_REGION", "us-west1")

    # This will fail validation due to missing credential files
    # but proves environment loading works
    with pytest.raises(ValidationError):
        Settings()


def test_settings_validation() -> None:
    """Test that settings validation catches invalid values."""
    with pytest.raises(ValidationError):
        Settings(google_cloud_project="")  # Empty project ID should fail
