#!/usr/bin/env python3

"""
Unit tests for the structured logging module.

Tests cover:
- Logger initialization and configuration
- Custom formatters (SyncFormatter, JSONFormatter)
- SyncLoggerAdapter with subject context
- Rich handler integration
- Log level handling
"""

import json
import logging
import sys
import tempfile
from unittest.mock import patch

import pytest

# Import the module under test
from db_sync_tool.utility.logging_config import (
    JSONFormatter,
    LoggingConfig,
    RichHandler,
    Subject,
    SyncFormatter,
    SyncLoggerAdapter,
    get_logger,
    get_sync_logger,
    init_logging,
    reset_logging,
)


@pytest.fixture(autouse=True)
def reset_logging_state():
    """Reset logging state before and after each test."""
    reset_logging()
    yield
    reset_logging()


class TestSubject:
    """Tests for Subject enum."""

    def test_subject_values(self):
        """Test that Subject enum has expected values."""
        assert Subject.ORIGIN.value == "ORIGIN"
        assert Subject.TARGET.value == "TARGET"
        assert Subject.LOCAL.value == "LOCAL"
        assert Subject.INFO.value == "INFO"

    def test_subject_is_string_enum(self):
        """Test that Subject can be compared to strings."""
        # Subject inherits from str, so it can be compared directly
        assert Subject.ORIGIN == "ORIGIN"
        assert Subject.ORIGIN.value == "ORIGIN"
        # Can be used in string operations
        assert "ORIGIN" in Subject.ORIGIN


class TestLoggingConfig:
    """Tests for LoggingConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = LoggingConfig()
        assert config.verbose == 0
        assert config.mute is False
        assert config.log_file is None
        assert config.json_logging is False

    def test_custom_values(self):
        """Test custom configuration values."""
        config = LoggingConfig(verbose=2, mute=True, log_file="/tmp/test.log", json_logging=True)
        assert config.verbose == 2
        assert config.mute is True
        assert config.log_file == "/tmp/test.log"
        assert config.json_logging is True


class TestSyncFormatter:
    """Tests for SyncFormatter."""

    def test_format_basic_message(self):
        """Test basic message formatting."""
        formatter = SyncFormatter(use_colors=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.subject = "INFO"
        record.remote = False

        result = formatter.format(record)
        assert "[INFO]" in result
        assert "Test message" in result

    def test_format_origin_remote(self):
        """Test formatting origin remote message."""
        formatter = SyncFormatter(use_colors=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Creating dump",
            args=(),
            exc_info=None,
        )
        record.subject = "ORIGIN"
        record.remote = True

        result = formatter.format(record)
        assert "[ORIGIN][REMOTE]" in result
        assert "Creating dump" in result

    def test_format_target_local(self):
        """Test formatting target local message."""
        formatter = SyncFormatter(use_colors=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Importing dump",
            args=(),
            exc_info=None,
        )
        record.subject = "TARGET"
        record.remote = False

        result = formatter.format(record)
        assert "[TARGET][LOCAL]" in result
        assert "Importing dump" in result

    def test_format_with_timestamp(self):
        """Test formatting with timestamp."""
        formatter = SyncFormatter(use_colors=False, show_timestamp=True)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.subject = "INFO"
        record.remote = False

        result = formatter.format(record)
        # Should contain timestamp pattern
        assert " - [INFO]" in result


class TestJSONFormatter:
    """Tests for JSONFormatter."""

    def test_format_basic_message(self):
        """Test basic JSON formatting."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.subject = "ORIGIN"
        record.remote = True

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["subject"] == "ORIGIN"
        assert data["remote"] is True
        assert data["message"] == "Test message"
        assert data["line"] == 42
        assert "timestamp" in data

    def test_format_warning_message(self):
        """Test JSON formatting for warning."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Warning message",
            args=(),
            exc_info=None,
        )
        record.subject = "INFO"
        record.remote = False

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "WARNING"
        assert data["message"] == "Warning message"

    def test_format_with_exception(self):
        """Test JSON formatting with exception info."""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        record.subject = "INFO"
        record.remote = False

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "ERROR"
        assert "exception" in data
        assert "ValueError" in data["exception"]


class TestRichHandler:
    """Tests for RichHandler."""

    def test_handler_creation(self):
        """Test handler creation."""
        handler = RichHandler()
        assert handler.level == logging.NOTSET
        assert handler.mute is False

    def test_handler_with_mute(self):
        """Test handler with mute option."""
        handler = RichHandler(mute=True)
        assert handler.mute is True

    def test_emit_muted_info(self):
        """Test that INFO messages are suppressed when muted."""
        handler = RichHandler(mute=True)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.subject = "INFO"
        record.remote = False

        # Should not raise or print
        handler.emit(record)

    def test_emit_error_even_when_muted(self):
        """Test that ERROR messages are shown even when muted."""
        handler = RichHandler(mute=True)

        with patch.object(handler, '_console', None):
            with patch('builtins.print') as mock_print:
                record = logging.LogRecord(
                    name="test",
                    level=logging.ERROR,
                    pathname="test.py",
                    lineno=1,
                    msg="Error message",
                    args=(),
                    exc_info=None,
                )
                record.subject = "INFO"
                record.remote = False

                handler.emit(record)
                mock_print.assert_called()


class TestSyncLoggerAdapter:
    """Tests for SyncLoggerAdapter."""

    def test_adapter_creation(self):
        """Test adapter creation with subject."""
        logger = logging.getLogger("test_adapter")
        adapter = SyncLoggerAdapter(logger, subject="ORIGIN", remote=True)

        assert adapter.subject == "ORIGIN"
        assert adapter.default_remote is True

    def test_process_adds_subject(self):
        """Test that process adds subject to extra."""
        logger = logging.getLogger("test_process")
        adapter = SyncLoggerAdapter(logger, subject="TARGET")

        msg, kwargs = adapter.process("Test message", {})

        assert kwargs["extra"]["subject"] == "TARGET"

    def test_process_preserves_existing_extra(self):
        """Test that process preserves existing extra data."""
        logger = logging.getLogger("test_preserve")
        adapter = SyncLoggerAdapter(logger, subject="ORIGIN")

        msg, kwargs = adapter.process("Test message", {"extra": {"custom": "value"}})

        assert kwargs["extra"]["subject"] == "ORIGIN"
        assert kwargs["extra"]["custom"] == "value"

    def test_set_remote(self):
        """Test setting remote flag."""
        logger = logging.getLogger("test_remote")
        adapter = SyncLoggerAdapter(logger, subject="ORIGIN", remote=False)

        assert adapter.default_remote is False

        adapter.set_remote(True)

        assert adapter.default_remote is True
        assert adapter.extra["remote"] is True


class TestInitLogging:
    """Tests for init_logging function."""

    def test_basic_initialization(self):
        """Test basic logging initialization."""
        logger = init_logging()

        assert logger is not None
        assert logger.name == "db_sync_tool"
        # Without console_output or log_file, should have NullHandler
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.NullHandler)

    def test_with_console_output(self):
        """Test logging with console output enabled."""
        logger = init_logging(console_output=True)

        assert logger is not None
        # Should have console handler
        assert len(logger.handlers) >= 1
        assert isinstance(logger.handlers[0], RichHandler)

    def test_verbose_level(self):
        """Test verbose level setting."""
        logger = init_logging(verbose=2)

        assert logger.level == logging.DEBUG

    def test_with_file_handler(self):
        """Test logging with file handler."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            log_file = f.name

        logger = init_logging(log_file=log_file)

        # Should have only file handler (no console by default)
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1

    def test_with_file_and_console(self):
        """Test logging with both file and console handlers."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            log_file = f.name

        logger = init_logging(log_file=log_file, console_output=True)

        # Should have console + file handler
        assert len(logger.handlers) == 2

        # Test that file handler is present
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1

    def test_with_json_logging(self):
        """Test logging with JSON format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            log_file = f.name

        logger = init_logging(log_file=log_file, json_logging=True)

        # Find file handler and check formatter
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1
        assert isinstance(file_handlers[0].formatter, JSONFormatter)


class TestGetSyncLogger:
    """Tests for get_sync_logger function."""

    def test_get_logger_with_subject(self):
        """Test getting logger with subject."""
        logger = get_sync_logger("ORIGIN")

        assert isinstance(logger, SyncLoggerAdapter)
        assert logger.subject == "ORIGIN"

    def test_get_logger_with_enum(self):
        """Test getting logger with Subject enum."""
        logger = get_sync_logger(Subject.TARGET)

        assert logger.subject == "TARGET"

    def test_get_logger_caching(self):
        """Test that loggers are cached."""
        logger1 = get_sync_logger("ORIGIN", remote=True)
        logger2 = get_sync_logger("ORIGIN", remote=True)

        assert logger1 is logger2

    def test_different_remote_creates_different_logger(self):
        """Test that different remote status creates different logger."""
        logger1 = get_sync_logger("ORIGIN", remote=True)
        logger2 = get_sync_logger("ORIGIN", remote=False)

        assert logger1 is not logger2


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_root_logger(self):
        """Test getting root logger."""
        logger = get_logger()

        assert logger is not None
        assert logger.name == "db_sync_tool"

    def test_get_logger_initializes_if_needed(self):
        """Test that get_logger initializes logging if not done."""
        reset_logging()
        logger = get_logger()

        assert logger is not None


class TestResetLogging:
    """Tests for reset_logging function."""

    def test_reset_clears_state(self):
        """Test that reset clears all state."""
        init_logging()
        logger1 = get_sync_logger("ORIGIN")

        reset_logging()

        # After reset, should get new logger
        logger2 = get_sync_logger("ORIGIN")
        assert logger1 is not logger2


class TestIntegration:
    """Integration tests for the logging system."""

    def test_full_logging_workflow(self):
        """Test complete logging workflow."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            log_file = f.name

        # Initialize with file logging
        init_logging(verbose=1, log_file=log_file)

        # Get subject-specific loggers
        origin_logger = get_sync_logger("ORIGIN", remote=True)
        target_logger = get_sync_logger("TARGET", remote=False)

        # Log messages
        origin_logger.info("Creating database dump")
        target_logger.info("Importing database dump")
        origin_logger.warning("Slow connection detected")

        # Read log file
        with open(log_file, 'r') as f:
            content = f.read()

        assert "Creating database dump" in content
        assert "Importing database dump" in content
        assert "Slow connection detected" in content

    def test_json_logging_workflow(self):
        """Test JSON logging workflow."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            log_file = f.name

        init_logging(log_file=log_file, json_logging=True)

        logger = get_sync_logger("ORIGIN", remote=True)
        logger.info("Test JSON message")

        with open(log_file, 'r') as f:
            line = f.readline()
            data = json.loads(line)

        assert data["message"] == "Test JSON message"
        assert data["subject"] == "ORIGIN"
        assert data["remote"] is True
