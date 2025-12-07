# src/utils/logger.py
"""
Structured logging configuration using structlog.

Provides JSON-formatted logs for production and human-readable logs for development.
"""

import logging
import sys
from typing import Any, cast

import structlog
from structlog.types import EventDict, Processor


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to log entries."""
    event_dict["app"] = "ai-teacher-assistant"
    event_dict["version"] = "0.1.0"
    return event_dict


def setup_logger(log_level: str = "INFO") -> structlog.BoundLogger:
    """
    Configure structured logging with appropriate processors.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured structlog logger instance

    Example:
        >>> logger = setup_logger("INFO")
        >>> logger.info("agent_initialized", agent_name="CurriculumArchitect")
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Determine if we're in development
    is_dev = log_level == "DEBUG"

    # Shared processors
    shared_processors: list[Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_app_context,
    ]

    if is_dev:
        # Development: Human-readable console output
        processors = [*shared_processors, structlog.dev.ConsoleRenderer(colors=True)]
    else:
        # Production: JSON output for log aggregation
        processors = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=cast("Any", processors),
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return cast("structlog.BoundLogger", structlog.get_logger())


# Default logger instance
logger = setup_logger()
