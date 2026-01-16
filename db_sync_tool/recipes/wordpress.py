#!/usr/bin/env python3

"""
Wordpress script
"""

from db_sync_tool.utility import mode, system, helper


def check_configuration(client):
    """
    Checking WordPress database configuration
    :param client: String
    :return:
    """
    cfg = system.get_typed_config()
    _path = cfg.get_client(client).path

    _db_config = {
        'name': get_database_setting(client, 'DB_NAME', _path),
        'host': get_database_setting(client, 'DB_HOST', _path),
        'password': get_database_setting(client, 'DB_PASSWORD', _path),
        'port': get_database_setting(client, 'DB_PORT', _path)
        if get_database_setting(client, 'DB_PORT', _path) != '' else 3306,
        'user': get_database_setting(client, 'DB_USER', _path),
    }

    system.set_database_config(client, helper.clean_db_config(_db_config))


def get_database_setting(client, name, file):
    """
    Parsing a single database variable from the wp-config.php file
    https://stackoverflow.com/questions/63493645/extract-database-name-from-a-wp-config-php-file
    :param client: String
    :param name: String
    :param file: String
    :return:
    """
    result = mode.run_command(
        helper.get_command(client, 'sed') +
        f' -n "s/define( *\'{name}\', *\'\([^\']*\)\'.*/\\1/p" {file}',
        client,
        True
    )
    return result.replace('\n', '') if result else ''
