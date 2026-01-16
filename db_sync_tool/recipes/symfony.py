#!/usr/bin/env python3

"""
Symfony script
"""

from db_sync_tool.utility import mode, system, helper
from db_sync_tool.utility.exceptions import ParsingError
from db_sync_tool.recipes.parsing import (  # noqa: F401 (re-export)
    parse_symfony_database_url,
)


def check_configuration(client):
    """
    Checking remote Symfony database configuration
    :param client: String
    :return:
    """
    cfg = system.get_typed_config()
    _path = cfg.get_client(client).path

    # Check for symfony 2.8
    if 'parameters.yml' in _path:
        _db_config = {
            'name': get_database_parameter(client, 'database_name', _path),
            'host': get_database_parameter(client, 'database_host', _path),
            'password': get_database_parameter(client, 'database_password', _path),
            'port': get_database_parameter(client, 'database_port', _path),
            'user': get_database_parameter(client, 'database_user', _path),
        }
    # Using for symfony >=3.4
    else:
        stdout = mode.run_command(
            helper.get_command(client, 'grep') + ' -v "^#" ' + _path +
            ' | ' + helper.get_command(client, 'grep') + ' DATABASE_URL',
            client,
            True
        )
        _db_config = parse_database_credentials(stdout)

    system.set_database_config(client, helper.clean_db_config(_db_config))


def parse_database_credentials(db_credentials):
    """
    Parsing database credentials to needed format
    :param db_credentials: Dictionary
    :return: Dictionary
    """
    try:
        return parse_symfony_database_url(db_credentials)
    except (ValueError, ParsingError):
        raise ParsingError('Mismatch of expected database credentials') from None


def get_database_parameter(client, name, file):
    """
    Parsing a single database variable from the parameters.yml file
    hhttps://unix.stackexchange.com/questions/84922/extract-a-part-of-one-line-from-a-file-with-sed
    :param client: String
    :param name: String
    :param file: String
    :return:
    """
    result = mode.run_command(
        helper.get_command(client, 'sed') + f' -n -e \'/{name}/ s/.*\\: *//p\' {file}',
        client,
        True
    )
    return result.replace('\n', '') if result else ''
