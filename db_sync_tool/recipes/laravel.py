#!/usr/bin/env python3

"""
Laravel script
"""
from db_sync_tool.utility import mode, system, helper


def check_configuration(client):
    """
    Checking remote Laravel database configuration
    :param client: String
    :return:
    """
    _path = system.config[client]['path']

    system.config[client]['db'] = helper.clean_db_config({
        'name': get_database_parameter(client, 'DB_DATABASE', _path),
        'host': get_database_parameter(client, 'DB_HOST', _path),
        'password': get_database_parameter(client, 'DB_PASSWORD', _path),
        'port': get_database_parameter(client, 'DB_PORT', _path),
        'user': get_database_parameter(client, 'DB_USERNAME', _path),
    })


def get_database_parameter(client, name, file):
    """
    Parsing a single database variable from the .env file
    https://gist.github.com/judy2k/7656bfe3b322d669ef75364a46327836
    :param client: String
    :param name: String
    :param file: String
    :return:
    """
    return mode.run_command(
        helper.get_command(client, 'grep') + f' {name} {file} | cut -d \'=\' -f2',
        client,
        True
    ).replace('\n', '')
