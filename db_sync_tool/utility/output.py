#!/usr/bin/env python3

"""
Output script

This module provides the legacy output interface using Rich.
For new code, prefer using the console module directly.
"""
from db_sync_tool.utility import log, mode, system
from db_sync_tool.utility.console import get_output_manager


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


# Mapping from Subject constants to subject strings for new OutputManager
_SUBJECT_MAP = {
    Subject.INFO: "INFO",
    Subject.LOCAL: "LOCAL",
    Subject.TARGET: "TARGET",
    Subject.ORIGIN: "ORIGIN",
    Subject.ERROR: "ERROR",
    Subject.WARNING: "WARNING",
    Subject.DEBUG: "DEBUG",
}


def message(header, message, do_print=True, do_log=False, debug=False, verbose_only=False):
    """
    Formatting a message for print or log.

    This function maintains backward compatibility while delegating
    to the new Rich-based OutputManager.

    :param header: Subject prefix (e.g., Subject.ORIGIN)
    :param message: Message text
    :param do_print: Whether to print to console
    :param do_log: Whether to log the message
    :param debug: Whether this is a debug message
    :param verbose_only: Only show in verbose mode
    :return: String message if do_print is False
    """
    cfg = system.get_typed_config()
    output_manager = get_output_manager()

    # Logging if explicitly forced or verbose option is active
    if do_log or cfg.verbose:
        _message = remove_multiple_elements_from_string([CliFormat.BEIGE,
                                                         CliFormat.PURPLE,
                                                         CliFormat.BLUE,
                                                         CliFormat.YELLOW,
                                                         CliFormat.GREEN,
                                                         CliFormat.RED,
                                                         CliFormat.BLACK,
                                                         CliFormat.ENDC,
                                                         CliFormat.BOLD,
                                                         CliFormat.UNDERLINE], message)
        if debug:
            log.get_logger().debug(_message)
        elif header == Subject.WARNING:
            log.get_logger().warning(_message)
        elif header == Subject.ERROR:
            log.get_logger().error(_message)
        else:
            log.get_logger().info(_message)

    # Formatting message if mute option is inactive
    if (cfg.mute and header == Subject.ERROR) or (not cfg.mute):
        if do_print:
            if not verbose_only or (verbose_only and cfg.verbose):
                # Determine subject and remote status
                subject_str = _SUBJECT_MAP.get(header, "INFO")
                is_remote = _is_remote_for_header(header)

                # Strip ANSI codes from message before passing to OutputManager
                clean_message = remove_multiple_elements_from_string([
                    CliFormat.BEIGE, CliFormat.PURPLE, CliFormat.BLUE,
                    CliFormat.YELLOW, CliFormat.GREEN, CliFormat.RED,
                    CliFormat.BLACK, CliFormat.ENDC, CliFormat.BOLD,
                    CliFormat.UNDERLINE
                ], message)

                # Use new OutputManager
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
        else:
            return header + extend_output_by_sync_mode(header, debug) + ' ' + message


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
