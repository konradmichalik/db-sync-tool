#!/usr/bin/env python3

"""
TYPO3 script
"""

import json

from db_sync_tool.utility import mode, system, helper
from db_sync_tool.utility.exceptions import ParsingError
from db_sync_tool.recipes.parsing import (  # noqa: F401 (re-export)
    parse_typo3_database_credentials,
)


def check_configuration(client):
    """
    Checking remote TYPO3 database configuration
    :param client: String
    :return:
    """
    cfg = system.get_typed_config()
    client_cfg = cfg.get_client(client)
    _path = client_cfg.path

    if 'LocalConfiguration' in _path:
        stdout = mode.run_command(
            helper.get_command(client, 'php') + ' -r "echo json_encode(include \'' +
            _path + '\');"',
            client,
            True
        )
        if not stdout:
            raise ParsingError('Failed to read TYPO3 configuration')

        _db_config = parse_database_credentials(json.loads(stdout)['DB'])
    elif '.env' in _path:
        # Try to parse settings from .env file
        # db_cfg fields can override default env var names if user provides them
        db_cfg = client_cfg.db
        _db_config = {
            'name': get_database_setting_from_env(client, db_cfg.name or 'TYPO3_CONF_VARS__DB__Connections__Default__dbname', _path),
            'host': get_database_setting_from_env(client, db_cfg.host or 'TYPO3_CONF_VARS__DB__Connections__Default__host', _path),
            'password': get_database_setting_from_env(client, db_cfg.password or 'TYPO3_CONF_VARS__DB__Connections__Default__password', _path),
            'port': get_database_setting_from_env(client, str(db_cfg.port) if db_cfg.port else 'TYPO3_CONF_VARS__DB__Connections__Default__port', _path) or 3306,
            'user': get_database_setting_from_env(client, db_cfg.user or 'TYPO3_CONF_VARS__DB__Connections__Default__user', _path),
        }
    elif 'AdditionalConfiguration.php' in _path:
        # Try to parse settings from AdditionalConfiguration.php file
        _db_config = {
            'name': get_database_setting_from_additional_configuration(client, 'dbname', _path),
            'host': get_database_setting_from_additional_configuration(client, 'host', _path),
            'password': get_database_setting_from_additional_configuration(client, 'password', _path),
            'port': get_database_setting_from_additional_configuration(client, 'port', _path)
            if get_database_setting_from_additional_configuration(client, 'port', _path) != '' else 3306,
            'user': get_database_setting_from_additional_configuration(client, 'user', _path),
        }
    else:
        raise ParsingError(
            f'Can\'t extract database information from given path {_path}. '
            f'Can only extract settings from the following files: LocalConfiguration.php, '
            f'AdditionalConfiguration.php, .env'
        )

    system.set_database_config(client, helper.clean_db_config(_db_config))


def parse_database_credentials(db_credentials):
    """
    Parsing database credentials to needed format
    :param db_credentials: Dictionary
    :return: Dictionary
    """
    return parse_typo3_database_credentials(db_credentials)


def get_database_setting_from_additional_configuration(client, name, file):
    """
    Get database setting try to regex from AdditionalConfiguration
    sed -nE "s/'dbname'.*=>.*'(.*)'.*$/\1/p" /var/www/html/tests/files/www1/AdditionalConfiguration.php
    :param client: String
    :param name: String
    :param file: String
    :return:
    """
    return helper.run_sed_command(client, f'"s/\'{name}\'.*=>.*\'(.*)\'.*$/\\1/p" {file}')

def get_database_setting_from_env(client, name, file):
    """
    Get database setting try to regex from .env
    sed -nE "s/TYPO3_CONF_VARS__DB__Connections__Default__host=(.*).*$/\1/p" /var/www/html/tests/files/www1/typo3.env
    :param client: String
    :param name: String
    :param file: String
    :return:
    """
    return helper.run_sed_command(client, f'"s/{name}=(.*).*$/\\1/p" {file}')
