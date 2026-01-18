#!/usr/bin/env python3

"""
Structured Logging Configuration.

This module provides a unified logging infrastructure with:
- Subject-aware logging (ORIGIN, TARGET, LOCAL)
- Rich console output (interactive mode)
- Structured JSON logging (machine-readable)
- File logging with configurable formats

Usage:
    from db_sync_tool.utility.logging_config import get_sync_logger, init_logging

    # Initialize logging (once at startup)
    init_logging(verbose=1, log_file="/path/to/log", json_logging=True)

    # Get a subject-specific logger
    logger = get_sync_logger("origin")
    logger.info("Creating database dump", extra={"remote": True})

    # Or use the default logger
    from db_sync_tool.utility.logging_config import logger
    logger.info("General message")
"""

from __future__ import annotations

import json
import logging
import sys
import time
from collections.abc import MutableMapping
from dataclasses import dataclass
from enum import Enum
from typing import Any


class Subject(str, Enum):
    """Log message subjects indicating the source/context of the operation."""
    ORIGIN = "ORIGIN"
    TARGET = "TARGET"
    LOCAL = "LOCAL"
    INFO = "INFO"

    def __str__(self) -> str:
        """Return the value for string conversion (StrEnum behavior)."""
        return self.value


class SyncLogRecord(logging.LogRecord):
    """Extended LogRecord with sync-specific fields."""

    subject: str
    remote: bool

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Set defaults for custom fields
        if not hasattr(self, 'subject'):
            self.subject = Subject.INFO.value
        if not hasattr(self, 'remote'):
            self.remote = False


# Note: We don't modify the LogRecord factory globally anymore
# because Python 3.13+ is stricter about overwriting attributes.
# Instead, we rely on the SyncLoggerAdapter to add the extra fields
# and formatters use getattr() with defaults.


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    verbose: int = 0  # 0=normal, 1=verbose (-v), 2=debug (-vv)
    mute: bool = False
    log_file: str | None = None
    json_logging: bool = False


class SyncFormatter(logging.Formatter):
    """Custom formatter for sync tool logs with subject prefix."""

    LEVEL_COLORS = {
        logging.DEBUG: "\033[90m",     # Gray
        logging.INFO: "\033[92m",      # Green
        logging.WARNING: "\033[93m",   # Yellow
        logging.ERROR: "\033[91m",     # Red
        logging.CRITICAL: "\033[91m",  # Red bold
    }

    SUBJECT_COLORS = {
        "ORIGIN": "\033[95m",   # Magenta
        "TARGET": "\033[94m",   # Blue
        "LOCAL": "\033[96m",    # Cyan
        "INFO": "\033[92m",     # Green
    }

    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True, show_timestamp: bool = False):
        super().__init__()
        self.use_colors = use_colors
        self.show_timestamp = show_timestamp

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with subject prefix and optional colors."""
        subject = getattr(record, 'subject', 'INFO')
        remote = getattr(record, 'remote', False)

        # Build prefix
        if subject in ("ORIGIN", "TARGET"):
            location = "REMOTE" if remote else "LOCAL"
            prefix = f"[{subject}][{location}]"
        else:
            prefix = f"[{subject}]"

        # Build message
        if self.use_colors and sys.stdout.isatty():
            subject_color = self.SUBJECT_COLORS.get(subject, self.RESET)
            level_color = self.LEVEL_COLORS.get(record.levelno, self.RESET)

            if record.levelno >= logging.WARNING:
                prefix_str = f"{level_color}{prefix}{self.RESET}"
            else:
                prefix_str = f"{subject_color}{prefix}{self.RESET}"

            message = f"{prefix_str} {record.getMessage()}"
        else:
            message = f"{prefix} {record.getMessage()}"

        # Add timestamp if requested
        if self.show_timestamp:
            timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
            message = f"{timestamp} - {message}"

        return message


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(record.created)),
            "level": record.levelname,
            "subject": getattr(record, 'subject', 'INFO'),
            "remote": getattr(record, 'remote', False),
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class RichHandler(logging.Handler):
    """
    Handler that integrates with Rich console for beautiful output.

    Falls back to plain text if Rich is not available.
    """

    def __init__(self, level: int = logging.NOTSET, mute: bool = False):
        super().__init__(level)
        self.mute = mute
        self._console: Any = None
        self._escape: Any = None
        self._init_rich()

    def _init_rich(self) -> None:
        """Initialize Rich console if available."""
        try:
            from rich.console import Console
            from rich.markup import escape
            from rich.theme import Theme

            theme = Theme({
                "info": "cyan",
                "success": "green",
                "warning": "yellow",
                "error": "red bold",
                "origin": "magenta",
                "target": "blue",
                "local": "cyan",
                "debug": "dim",
            })
            self._console = Console(theme=theme)
            self._escape = escape
        except ImportError:
            pass

    def _get_style(self, subject: str, level: int) -> str:
        """Get Rich style based on subject and level."""
        if level >= logging.ERROR:
            return "error"
        if level >= logging.WARNING:
            return "warning"
        return subject.lower() if subject.lower() in ("origin", "target", "local") else "info"

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record."""
        if self.mute and record.levelno < logging.ERROR:
            return

        try:
            subject = getattr(record, 'subject', 'INFO')
            remote = getattr(record, 'remote', False)
            message = record.getMessage()

            # Build prefix
            if subject in ("ORIGIN", "TARGET"):
                location = "REMOTE" if remote else "LOCAL"
                prefix = f"[{subject}][{location}]"
            else:
                prefix = f"[{subject}]"

            if self._console and self._escape:
                style = self._get_style(subject, record.levelno)
                esc = self._escape

                # Format with Rich
                if record.levelno >= logging.ERROR:
                    self._console.print(f"[{style}]{esc(prefix)} {esc(message)}[/{style}]")
                elif record.levelno >= logging.WARNING:
                    self._console.print(f"[{style}]{esc(prefix)} {esc(message)}[/{style}]")
                else:
                    self._console.print(f"[{style}]{esc(prefix)}[/{style}] {esc(message)}")
            else:
                # Fallback to plain formatter
                formatter = SyncFormatter(use_colors=True)
                print(formatter.format(record))

        except Exception:
            self.handleError(record)


class SyncLoggerAdapter(logging.LoggerAdapter):  # type: ignore[type-arg]
    """
    Logger adapter that automatically adds subject context.

    Usage:
        logger = SyncLoggerAdapter(logging.getLogger("db_sync_tool"), subject="ORIGIN")
        logger.info("Creating dump", extra={"remote": True})
    """

    extra: dict[str, Any]  # Override type to be mutable dict

    def __init__(self, logger: logging.Logger, subject: str = "INFO", remote: bool = False):
        super().__init__(logger, {"subject": subject, "remote": remote})
        self.subject = subject
        self.default_remote = remote

    def process(
        self, msg: Any, kwargs: MutableMapping[str, Any]
    ) -> tuple[Any, MutableMapping[str, Any]]:
        """Process log message and add subject context."""
        extra = kwargs.get("extra", {})
        if isinstance(extra, dict):
            extra.setdefault("subject", self.subject)
            extra.setdefault("remote", self.default_remote)
            kwargs["extra"] = extra
        return msg, kwargs

# Global logger instances
_root_logger: logging.Logger | None = None
_logging_config: LoggingConfig = LoggingConfig()
_subject_loggers: dict[str, SyncLoggerAdapter] = {}


def init_logging(
    verbose: int = 0,
    mute: bool = False,
    log_file: str | None = None,
    json_logging: bool = False,
    console_output: bool = False,
) -> logging.Logger:
    """
    Initialize the logging system.

    Args:
        verbose: Verbosity level (0=normal, 1=verbose, 2=debug)
        mute: Suppress non-error output
        log_file: Path to log file (optional)
        json_logging: Use JSON format for file logging
        console_output: Add console handler (False when OutputManager handles console)

    Returns:
        Configured root logger
    """
    global _root_logger, _logging_config, _subject_loggers

    _logging_config = LoggingConfig(
        verbose=verbose,
        mute=mute,
        log_file=log_file,
        json_logging=json_logging,
    )

    # Create or get root logger
    _root_logger = logging.getLogger("db_sync_tool")
    _root_logger.handlers.clear()

    # Set level based on verbosity
    if verbose >= 2:
        _root_logger.setLevel(logging.DEBUG)
    elif verbose >= 1:
        _root_logger.setLevel(logging.INFO)
    else:
        _root_logger.setLevel(logging.INFO)

    # Add console handler only if explicitly requested
    # (When OutputManager handles console output, we skip this)
    if console_output:
        console_handler = RichHandler(mute=mute)
        if verbose >= 2:
            console_handler.setLevel(logging.DEBUG)
        else:
            console_handler.setLevel(logging.INFO)
        _root_logger.addHandler(console_handler)

    # Add file handler if log file specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        if json_logging:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(SyncFormatter(use_colors=False, show_timestamp=True))

        _root_logger.addHandler(file_handler)

    # Add NullHandler if no handlers were added (prevents "No handlers" warning)
    if not _root_logger.handlers:
        _root_logger.addHandler(logging.NullHandler())

    # Clear cached subject loggers
    _subject_loggers.clear()

    return _root_logger


def get_sync_logger(
    subject: str | Subject = Subject.INFO,
    remote: bool = False,
) -> SyncLoggerAdapter:
    """
    Get a logger adapter with subject context.

    Args:
        subject: Subject (ORIGIN, TARGET, LOCAL, INFO)
        remote: Whether the operation is remote

    Returns:
        SyncLoggerAdapter with subject context
    """
    global _root_logger, _subject_loggers

    if _root_logger is None:
        init_logging()

    # Normalize subject
    if isinstance(subject, Subject):
        subject_str = subject.value
    else:
        subject_str = subject.upper()

    # Cache key includes remote status
    cache_key = f"{subject_str}:{remote}"

    if cache_key not in _subject_loggers:
        _subject_loggers[cache_key] = SyncLoggerAdapter(
            _root_logger,  # type: ignore[arg-type]
            subject=subject_str,
            remote=remote,
        )

    return _subject_loggers[cache_key]


def reset_logging() -> None:
    """Reset logging configuration (for testing)."""
    global _root_logger, _subject_loggers, _logging_config

    if _root_logger:
        _root_logger.handlers.clear()

    _root_logger = None
    _subject_loggers.clear()
    _logging_config = LoggingConfig()


# Convenience exports
def get_logger() -> logging.Logger:
    """Get the root sync logger."""
    global _root_logger
    if _root_logger is None:
        init_logging()
    return _root_logger  # type: ignore[return-value]


# Default logger for direct import
logger = get_sync_logger()
