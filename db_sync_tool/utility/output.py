#!/usr/bin/env python3

"""
Output script

This module provides the legacy output interface using Rich and structured logging.
For new code, prefer using the logging_config module directly:

    from db_sync_tool.utility.logging_config import get_sync_logger

    logger = get_sync_logger("origin", remote=True)
    logger.info("Creating database dump")
"""
from __future__ import annotations

from db_sync_tool.utility import mode, system
from db_sync_tool.utility.console import get_output_manager
from db_sync_tool.utility.logging_config import get_sync_logger


class CliFormat:
    """ANSI color codes for CLI formatting (legacy compatibility)."""
    BEIGE = '\033[96m'
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLACK = '\033[90m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Subject:
    """Subject prefixes for messages (legacy compatibility)."""
    INFO = CliFormat.GREEN + '[INFO]' + CliFormat.ENDC
    LOCAL = CliFormat.BEIGE + '[LOCAL]' + CliFormat.ENDC
    TARGET = CliFormat.BLUE + '[TARGET]' + CliFormat.ENDC
    ORIGIN = CliFormat.PURPLE + '[ORIGIN]' + CliFormat.ENDC
    ERROR = CliFormat.RED + '[ERROR]' + CliFormat.ENDC
    WARNING = CliFormat.YELLOW + '[WARNING]' + CliFormat.ENDC
    DEBUG = CliFormat.BLACK + '[DEBUG]' + CliFormat.ENDC


# Mapping from Subject constants to subject strings for structured logging
_SUBJECT_MAP = {
    Subject.INFO: "INFO",
    Subject.LOCAL: "LOCAL",
    Subject.TARGET: "TARGET",
    Subject.ORIGIN: "ORIGIN",
    Subject.ERROR: "INFO",  # Error level handled separately
    Subject.WARNING: "INFO",  # Warning level handled separately
    Subject.DEBUG: "INFO",  # Debug level handled separately
}


def message(
    header: str,
    message: str,
    do_print: bool = True,
    do_log: bool = False,
    debug: bool = False,
    verbose_only: bool = False,
) -> str | None:
    """
    Formatting a message for print or log.

    This function maintains backward compatibility while using structured logging
    and delegating console output to the Rich-based OutputManager.

    Args:
        header: Subject prefix (e.g., Subject.ORIGIN)
        message: Message text
        do_print: Whether to print to console
        do_log: Whether to log the message
        debug: Whether this is a debug message
        verbose_only: Only show in verbose mode

    Returns:
        String message if do_print is False, None otherwise
    """
    cfg = system.get_typed_config()
    output_manager = get_output_manager()

    # Clean ANSI codes from message for logging and structured output
    clean_message = remove_multiple_elements_from_string([
        CliFormat.BEIGE, CliFormat.PURPLE, CliFormat.BLUE,
        CliFormat.YELLOW, CliFormat.GREEN, CliFormat.RED,
        CliFormat.BLACK, CliFormat.ENDC, CliFormat.BOLD,
        CliFormat.UNDERLINE
    ], message)

    # Get subject and remote status for structured logging
    subject_str = _SUBJECT_MAP.get(header, "INFO")
    is_remote = _is_remote_for_header(header)

    # Structured logging if explicitly forced or verbose option is active
    if do_log or cfg.verbose:
        logger = get_sync_logger(subject=subject_str, remote=is_remote)

        if debug:
            logger.debug(clean_message)
        elif header == Subject.WARNING:
            logger.warning(clean_message)
        elif header == Subject.ERROR:
            logger.error(clean_message)
        else:
            logger.info(clean_message)

    # Console output if mute option is inactive
    if (cfg.mute and header == Subject.ERROR) or (not cfg.mute):
        if do_print:
            if not verbose_only or (verbose_only and cfg.verbose):
                # Use new OutputManager for console display
                if header == Subject.ERROR:
                    output_manager.error(clean_message)
                elif header == Subject.WARNING:
                    output_manager.warning(clean_message)
                elif debug:
                    output_manager.debug(clean_message)
                else:
                    # Legacy API: messages are logged after completion
                    # Set up step context for success() to use, then show completed
                    output_manager._setup_step(clean_message, subject=subject_str, remote=is_remote)
                    output_manager.success()
            return None
        else:
            return header + extend_output_by_sync_mode(header, debug) + ' ' + message
    return None


def _is_remote_for_header(header) -> bool:
    """Determine if the operation is remote based on header."""
    if header in (Subject.INFO, Subject.LOCAL, Subject.WARNING, Subject.ERROR):
        return False

    host = subject_to_host(header)
    if host is None:
        return False

    return mode.is_remote(host)


def extend_output_by_sync_mode(header, debug=False):
    """
    Extending the output by a client information (LOCAL|REMOTE).

    :param header: Subject prefix
    :param debug: Whether to include debug tag
    :return: String extension
    """
    _debug = ''

    if debug:
        _debug = Subject.DEBUG

    if header == Subject.INFO or header == Subject.LOCAL or \
            header == Subject.WARNING or header == Subject.ERROR:
        return ''
    else:
        if mode.is_remote(subject_to_host(header)):
            return CliFormat.BLACK + '[REMOTE]' + CliFormat.ENDC + _debug
        else:
            if subject_to_host(header) == mode.Client.LOCAL:
                return _debug
            else:
                return CliFormat.BLACK + '[LOCAL]' + CliFormat.ENDC + _debug


def host_to_subject(host):
    """
    Converting the client to the according subject.

    :param host: Client constant
    :return: Subject prefix
    """
    if host == mode.Client.ORIGIN:
        return Subject.ORIGIN
    elif host == mode.Client.TARGET:
        return Subject.TARGET
    elif host == mode.Client.LOCAL:
        return Subject.LOCAL
    return None


def subject_to_host(subject):
    """
    Converting the subject to the according host.

    :param subject: Subject prefix
    :return: Client constant
    """
    if subject == Subject.ORIGIN:
        return mode.Client.ORIGIN
    elif subject == Subject.TARGET:
        return mode.Client.TARGET
    elif subject == Subject.LOCAL:
        return mode.Client.LOCAL
    return None


def remove_multiple_elements_from_string(elements, string):
    """
    Removing multiple elements from a string.

    :param elements: List of strings to remove
    :param string: Input string
    :return: Cleaned string
    """
    for element in elements:
        if element in string:
            string = string.replace(element, '')
    return string
