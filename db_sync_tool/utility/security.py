#!/usr/bin/env python3

"""
Security utility functions.

This module contains pure security functions with minimal dependencies,
making them safe to import without circular import issues.
Only depends on utility/exceptions.py which has no other project dependencies.
"""

import re
import shlex
from typing import Any

from db_sync_tool.utility.exceptions import ValidationError


def quote_shell_arg(arg: Any) -> str:
    """
    Safely quote a string for use as a shell argument.
    Prevents command injection by escaping special characters.

    :param arg: Value to quote (will be converted to string)
    :return: Safely quoted string
    """
    if arg is None:
        return "''"
    return shlex.quote(str(arg))


def sanitize_table_name(table: str) -> str:
    """
    Validate and sanitize a table name to prevent SQL injection.
    MySQL table names can contain alphanumeric chars, underscores, and dollar signs.
    They can also contain hyphens and dots in quoted identifiers.

    :param table: Table name to sanitize
    :return: Backtick-quoted table name
    :raises ValidationError: If table name contains invalid characters
    """
    if not table:
        raise ValidationError("Table name cannot be empty")

    # Allow alphanumeric, underscore, hyphen, dot, dollar sign
    if not re.match(r'^[a-zA-Z0-9_$.-]+$', table):
        raise ValidationError(f"Invalid table name: {table}")

    return f"`{table}`"


def sanitize_command_for_logging(command: str) -> str:
    """
    Remove sensitive information from commands before logging.
    This prevents credentials from appearing in verbose output or logs.

    :param command: Command string to sanitize
    :return: Sanitized command string
    """
    patterns = [
        # MySQL password patterns
        (r"-p'[^']*'", "-p'***'"),
        (r'-p"[^"]*"', '-p"***"'),
        (r"-p[^\s'\"]+", "-p***"),
        # SSHPASS patterns
        (r"SSHPASS='[^']*'", "SSHPASS='***'"),
        (r'SSHPASS="[^"]*"', 'SSHPASS="***"'),
        (r"SSHPASS=[^\s]+", "SSHPASS=***"),
        # MySQL defaults-file (mask path to prevent disclosure)
        (r"--defaults-file=[^\s]+", "--defaults-file=***"),
        # Base64 encoded credentials
        (r"echo '[A-Za-z0-9+/=]{20,}' \| base64", "echo '***' | base64"),
    ]

    sanitized = command
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized)

    return sanitized
