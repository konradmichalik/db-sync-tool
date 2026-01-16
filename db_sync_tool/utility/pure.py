#!/usr/bin/env python3

"""
Pure utility functions with no project dependencies.
"""

import re
from pathlib import Path
from typing import Any


def parse_version(version_output: str | None) -> str | None:
    """
    Parse version out of console output.
    https://stackoverflow.com/a/60730346

    :param version_output: Console output string
    :return: Version string or None
    """
    if not version_output:
        return None
    _version_pattern = r'\d+(=?\.(\d+(=?\.(\d+)*)*)*)*'
    _regex_matcher = re.compile(_version_pattern)
    _version = _regex_matcher.search(version_output)
    if _version:
        return _version.group(0)
    return None


def get_file_from_path(path: str) -> str:
    """
    Trims a path string to retrieve the file.

    :param path: File path
    :return: File name
    """
    return Path(path).name


def remove_surrounding_quotes(s: Any) -> Any:
    """
    Removes the enclosing quotes (single or double),
    if there are quotes at both the beginning and end of the string.

    :param s: The string to be checked
    :return: The string without enclosing quotes, if available
    """
    if isinstance(s, str):
        if s.startswith('"') and s.endswith('"'):
            return s[1:-1]
        elif s.startswith("'") and s.endswith("'"):
            return s[1:-1]
    return s


def clean_db_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Iterates over all entries of a dictionary and removes enclosing
    quotes from the values, if present.

    :param config: The dictionary to be edited
    :return: A new dictionary with adjusted values
    """
    return {key: remove_surrounding_quotes(value) for key, value in config.items()}


def dict_to_args(data: dict[str, Any]) -> list[str] | None:
    """
    Convert a dictionary to an args list.

    :param data: Dictionary to convert
    :return: List of arguments or None if empty
    """
    args = []
    for key, val in data.items():
        if val is True:
            args.append(f'--{key}')
        elif val is not False and val is not None:
            args.extend([f'--{key}', str(val)])
    return args or None


def remove_multiple_elements_from_string(elements: list, string: str) -> str:
    """
    Removes multiple elements from a string.

    :param elements: List of elements to remove
    :param string: Input string
    :return: String with elements removed
    """
    for element in elements:
        string = string.replace(element, '')
    return string
