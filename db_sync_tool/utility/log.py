#!/usr/bin/env python3

"""
Logging module.

This module provides backward-compatible logging functions while delegating
to the new structured logging infrastructure in logging_config.py.

For new code, prefer using:
    from db_sync_tool.utility.logging_config import get_sync_logger, init_logging
"""

from __future__ import annotations

import logging

# Global logger instance (lazy initialization)
_logger: logging.Logger | None = None
_initialized: bool = False


def init_logger() -> None:
    """
    Initialize the logger instance.

    This function integrates with the new logging_config module for
    structured logging support while maintaining backward compatibility.
    """
    global _logger, _initialized

    if _initialized:
        return

    # Import here to avoid circular imports
    from db_sync_tool.utility import system
    from db_sync_tool.utility.logging_config import init_logging

    cfg = system.get_typed_config()

    # Initialize the new logging infrastructure
    _logger = init_logging(
        verbose=1 if cfg.verbose else 0,
        mute=cfg.mute,
        log_file=cfg.log_file,
        json_logging=cfg.json_log,
    )
    _initialized = True


def get_logger() -> logging.Logger:
    """
    Return the logger instance.

    Returns:
        Configured logger instance
    """
    global _logger, _initialized

    if _logger is None or not _initialized:
        init_logger()

    return _logger  # type: ignore[return-value]


def reset_logger() -> None:
    """Reset the logger (for testing)."""
    global _logger, _initialized

    from db_sync_tool.utility.logging_config import reset_logging

    reset_logging()
    _logger = None
    _initialized = False
