# src/config/__init__.py
"""Configuration management for the application."""

from src.config.settings import Settings, get_settings

__all__ = [
    "Settings",
    "get_settings",
]
