#!/usr/bin/env python3

"""
Drupal script
"""

import json
from db_sync_tool.utility import mode, system, helper, output
from db_sync_tool.utility.exceptions import ParsingError
from db_sync_tool.recipes.parsing import (  # noqa: F401 (re-export)
    parse_drupal_drush_credentials,
)


def check_configuration(client):
    """
    Checking Drupal database configuration.
    First tries to parse settings.php directly, falls back to Drush if needed.
    :param client: String
    :return:
    """
    cfg = system.get_typed_config()
    _path = cfg.get_client(client).path

    # Try direct settings.php parsing first
    try:
        _db_config = parse_settings_php(client, _path)
        if _db_config and _db_config.get('name') and _db_config.get('host'):
            output.message(
                output.host_to_subject(client),
                'Parsed database config from settings.php',
                True
            )
            system.set_database_config(client, helper.clean_db_config(_db_config))
            return
    except Exception:
        pass

    # Fall back to Drush
    check_configuration_drush(client)


def check_configuration_drush(client):
    """
    Checking Drupal database configuration with Drush
    :param client: String
    :return:
    """
    cfg = system.get_typed_config()
    _path = cfg.get_client(client).path

    # Check Drush version
    _raw_version = mode.run_command(
        f'{helper.get_command(client, "drush")} status --fields=drush-version --format=string '
        f'-r {_path}',
        client,
        True
    )

    output.message(
        output.host_to_subject(client),
        f'Drush version: {_raw_version}',
        True
    )

    stdout = mode.run_command(
        f'{helper.get_command(client, "drush")} core-status --pipe '
        f'--fields=db-hostname,db-username,db-password,db-name,db-port '
        f'-r {_path}',
        client,
        True
    )
    if not stdout:
        raise ParsingError('Failed to read Drupal configuration via drush')

    _db_config = parse_database_credentials(json.loads(stdout))

    system.set_database_config(client, helper.clean_db_config(_db_config))


def parse_settings_php(client, path):
    """
    Parse database credentials directly from settings.php
    :param client: String
    :param path: String
    :return: Dictionary or None
    """
    _db_config = {
        'name': get_setting_value(client, 'database', path),
        'host': get_setting_value(client, 'host', path),
        'password': get_setting_value(client, 'password', path),
        'port': get_setting_value(client, 'port', path) or 3306,
        'user': get_setting_value(client, 'username', path),
    }

    return _db_config


def get_setting_value(client, key, path):
    """
    Extract a single value from Drupal settings.php
    Handles both 'key' => 'value' and 'key' => "value" formats
    :param client: String
    :param key: String
    :param path: String
    :return: String
    """
    # Try single quotes first, then double quotes
    cmd_result = mode.run_command(
        helper.get_command(client, 'sed') +
        f' -n "s/.*\'{key}\' *=> *[\'\\"]\\([^\'\\"]*\\)[\'\\"].*/\\1/p" {path} | head -1',
        client,
        True
    )
    result = cmd_result.strip() if cmd_result else ''

    # For numeric values like port (without quotes)
    if not result:
        cmd_result = mode.run_command(
            helper.get_command(client, 'sed') +
            f' -n "s/.*\'{key}\' *=> *\\([0-9]*\\).*/\\1/p" {path} | head -1',
            client,
            True
        )
        result = cmd_result.strip() if cmd_result else ''

    return result


def parse_database_credentials(db_credentials):
    """
    Parsing database credentials to needed format
    :param db_credentials: Dictionary
    :return: Dictionary
    """
    return parse_drupal_drush_credentials(db_credentials)
