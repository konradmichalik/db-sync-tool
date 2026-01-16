#!/usr/bin/env python3

"""
Pure parsing functions for framework configuration files.

This module contains parsing functions with no dependencies on other project modules,
allowing proper unit testing and code coverage measurement.

Functions here are imported and used by the framework recipe modules.
"""

import re


def parse_symfony_database_url(db_credentials: str) -> dict:
    """
    Parse Symfony DATABASE_URL format into database config dict.

    Format: DATABASE_URL=mysql://user:password@host:port/dbname?options

    :param db_credentials: DATABASE_URL string
    :return: Dictionary with db_type, user, password, host, port, name
    :raises ValueError: If format doesn't match expected pattern
    """
    db_credentials = str(db_credentials).replace('\\n\'', '')
    # DATABASE_URL=mysql://db-user:1234@db-host:3306/db-name
    pattern = r'^DATABASE_URL=(?P<db_type>\w+):\/\/(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)\/(?P<name>[^?]+)(?:\?.*)?$'

    match = re.match(pattern, db_credentials)

    if match:
        return match.groupdict()
    else:
        raise ValueError('Mismatch of expected database credentials')


def parse_drupal_drush_credentials(db_credentials: dict) -> dict:
    """
    Parse Drupal Drush core-status output into database config dict.

    :param db_credentials: Dictionary from Drush JSON output
    :return: Dictionary with name, host, password, port, user
    """
    return {
        'name': db_credentials['db-name'],
        'host': db_credentials['db-hostname'],
        'password': db_credentials['db-password'],
        'port': db_credentials['db-port'],
        'user': db_credentials['db-username'],
    }


def parse_typo3_database_credentials(db_credentials: dict) -> dict:
    """
    Parse TYPO3 LocalConfiguration.php DB array into database config dict.

    Handles both TYPO3 v8+ (Connections/Default) and TYPO3 v7- formats.

    :param db_credentials: Dictionary from LocalConfiguration DB section
    :return: Dictionary with name, host, password, port, user
    """
    # Distinguish between database config scheme of TYPO3 v8+ and TYPO3 v7-
    if 'Connections' in db_credentials:
        _db_config = dict(db_credentials['Connections']['Default'])
        _db_config['name'] = _db_config['dbname']
    else:
        _db_config = dict(db_credentials)
        _db_config['user'] = _db_config['username']
        _db_config['name'] = _db_config['database']

    if 'port' not in _db_config:
        _db_config['port'] = 3306

    return _db_config
