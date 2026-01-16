#!/usr/bin/env python3

"""
TYPO3 script
"""

import json
import sys

from db_sync_tool.utility import mode, system, helper, output


def check_configuration(client):
    """
    Checking remote TYPO3 database configuration
    :param client: String
    :return:
    """
    _path = system.config[client]['path']

    if 'LocalConfiguration' in _path:
        stdout = mode.run_command(
            helper.get_command(client, 'php') + ' -r "echo json_encode(include \'' +
            system.config[client][
                'path'] + '\');"',
            client,
            True
        )
        if not stdout:
            raise RuntimeError('Failed to read TYPO3 configuration')

        _db_config = parse_database_credentials(json.loads(stdout)['DB'])
    elif '.env' in _path:
        # Try to parse settings from .env file
        if 'db' not in system.config[client]:
            system.config[client]['db'] = {}

        _db_config = {
            'name': get_database_setting_from_env(client, system.config[client]['db'].get('name', 'TYPO3_CONF_VARS__DB__Connections__Default__dbname'), system.config[client]['path']),
            'host': get_database_setting_from_env(client, system.config[client]['db'].get('host', 'TYPO3_CONF_VARS__DB__Connections__Default__host'), system.config[client]['path']),
            'password': get_database_setting_from_env(client, system.config[client]['db'].get('password', 'TYPO3_CONF_VARS__DB__Connections__Default__password'), system.config[client]['path']),
            'port': get_database_setting_from_env(client, system.config[client]['db'].get('port', 'TYPO3_CONF_VARS__DB__Connections__Default__port'), system.config[client]['path'])
            if get_database_setting_from_env(client, system.config[client]['db'].get('port', 'TYPO3_CONF_VARS__DB__Connections__Default__port'), system.config[client]['path']) != '' else 3306,
            'user': get_database_setting_from_env(client, system.config[client]['db'].get('user', 'TYPO3_CONF_VARS__DB__Connections__Default__user'), system.config[client]['path']),
        }
    elif 'AdditionalConfiguration.php' in _path:
        # Try to parse settings from AdditionalConfiguration.php file
        _db_config = {
            'name': get_database_setting_from_additional_configuration(client, 'dbname', system.config[client]['path']),
            'host': get_database_setting_from_additional_configuration(client, 'host', system.config[client]['path']),
            'password': get_database_setting_from_additional_configuration(client, 'password', system.config[client]['path']),
            'port': get_database_setting_from_additional_configuration(client, 'port', system.config[client]['path'])
            if get_database_setting_from_additional_configuration(client, 'port',
                                    system.config[client]['path']) != '' else 3306,
            'user': get_database_setting_from_additional_configuration(client, 'user', system.config[client]['path']),
        }
    else:
        sys.exit(
            output.message(
                output.Subject.ERROR,
                f'Can\'t extract database information from given path {system.config[client]["path"]}. Can only extract settings from the following files: LocalConfiguration.php, AdditionalConfiguration.php, .env',
                False
            )
        )

    system.config[client]['db'] = helper.clean_db_config(_db_config)


def parse_database_credentials(db_credentials):
    """
    Parsing database credentials to needed format
    :param db_credentials: Dictionary
    :return: Dictionary
    """
    #
    # Distinguish between database config scheme of TYPO3 v8+ and TYPO3 v7-
    #
    if 'Connections' in db_credentials:
        _db_config = db_credentials['Connections']['Default']
        _db_config['name'] = _db_config['dbname']
    else:
        _db_config = db_credentials
        _db_config['user'] = _db_config['username']
        _db_config['name'] = _db_config['database']

    if 'port' not in _db_config:
        _db_config['port'] = 3306

    return _db_config


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
