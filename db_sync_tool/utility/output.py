#!/usr/bin/env python3

"""
Output script
"""
import time
from yaspin import yaspin
from db_sync_tool.utility import log, mode, system


class CliFormat:
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
    INFO = CliFormat.GREEN + '[INFO]' + CliFormat.ENDC
    LOCAL = CliFormat.BEIGE + '[LOCAL]' + CliFormat.ENDC
    TARGET = CliFormat.BLUE + '[TARGET]' + CliFormat.ENDC
    ORIGIN = CliFormat.PURPLE + '[ORIGIN]' + CliFormat.ENDC
    ERROR = CliFormat.RED + '[ERROR]' + CliFormat.ENDC
    WARNING = CliFormat.YELLOW + '[WARNING]' + CliFormat.ENDC
    DEBUG = CliFormat.BLACK + '[DEBUG]' + CliFormat.ENDC


def message(header, message, do_print=True, do_log=False, debug=False, verbose_only=False):
    """
    Formatting a message for print or log
    :param header: String
    :param message: String
    :param do_print: Boolean
    :param do_log: Boolean
    :param debug: Boolean
    :param verbose_only: Boolean
    :return: String message
    """
    # Logging if explicitly forced or verbose option is active
    if do_log or system.config['verbose']:
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
        # @ToDo: Can this be done better? Dynamic functions?
        if debug:
            log.get_logger().debug(_message)
        elif header == Subject.WARNING:
            log.get_logger().warning(_message)
        elif header == Subject.ERROR:
            log.get_logger().error(_message)
        else:
            log.get_logger().info(_message)

    # Formatting message if mute option is inactive
    if (system.config['mute'] and header == Subject.ERROR) or (not system.config['mute']):
        if do_print:
            if not verbose_only or (verbose_only and system.config['verbose']):
                _message = header + extend_output_by_sync_mode(header, debug) + ' ' + message
                with yaspin(text=_message, color="yellow", side="right") as spinner:
                    spinner.ok("\b\b")
        else:
            return header + extend_output_by_sync_mode(header, debug) + ' ' + message


def extend_output_by_sync_mode(header, debug=False):
    """
    Extending the output by a client information (LOCAL|REMOTE)
    :param header: String
    :return: String message
    """
    _sync_mode = mode.get_sync_mode()
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
    Converting the client to the according subject
    :param host: String
    :return: String subject
    """
    if host == mode.Client.ORIGIN:
        return Subject.ORIGIN
    elif host == mode.Client.TARGET:
        return Subject.TARGET
    elif host == mode.Client.LOCAL:
        return Subject.LOCAL


def subject_to_host(subject):
    """
    Converting the subject to the according host
    :param subject: String
    :return: String host
    """
    if subject == Subject.ORIGIN:
        return mode.Client.ORIGIN
    elif subject == Subject.TARGET:
        return mode.Client.TARGET
    elif subject == Subject.LOCAL:
        return mode.Client.LOCAL


def remove_multiple_elements_from_string(elements, string):
    """
    Removing multiple elements from a string
    :param elements: List
    :param string: String
    :return: String string
    """
    for element in elements:
        if element in string:
            string = string.replace(element, '')
    return string

