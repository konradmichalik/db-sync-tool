#!/usr/bin/env python3

"""
Symfony script
"""

import re
import sys

from db_sync_tool.utility import mode, system, helper, output


def check_configuration(client):
    """
    Checking remote Symfony database configuration
    :param client: String
    :return:
    """
    _path = system.config[client]['path']

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
            helper.get_command(client, 'grep') + ' -v "^#" ' + system.config[client][
                'path'] + ' | ' + helper.get_command(client, 'grep') + ' DATABASE_URL',
            client,
            True
        )
        _db_config = parse_database_credentials(stdout)

    system.config[client]['db'] = helper.clean_db_config(_db_config)


def parse_database_credentials(db_credentials):
    """
    Parsing database credentials to needed format
    :param db_credentials: Dictionary
    :return: Dictionary
    """
    db_credentials = str(db_credentials).replace('\\n\'','')
    # DATABASE_URL=mysql://db-user:1234@db-host:3306/db-name
    pattern = r'^DATABASE_URL=(?P<db_type>\w+):\/\/(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)\/(?P<name>[^?]+)(?:\?.*)?$'

    match = re.match(pattern, db_credentials)

    if match:
        db_config = match.groupdict()
        return db_config
    else:
        sys.exit(
            output.message(
                output.Subject.ERROR,
                'Mismatch of expected database credentials',
                False
            )
        )


def get_database_parameter(client, name, file):
    """
    Parsing a single database variable from the parameters.yml file
    hhttps://unix.stackexchange.com/questions/84922/extract-a-part-of-one-line-from-a-file-with-sed
    :param client: String
    :param name: String
    :param file: String
    :return:
    """
    return mode.run_command(
        helper.get_command(client, 'sed') + f' -n -e \'/{name}/ s/.*\\: *//p\' {file}',
        client,
        True
    ).replace('\n', '')
