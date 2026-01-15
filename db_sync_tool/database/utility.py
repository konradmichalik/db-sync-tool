#!/usr/bin/env python3
# -*- coding: future_fstrings -*-

"""
Utility script
"""

import sys
import datetime
import re
from db_sync_tool.utility import mode, system, helper, output

database_dump_file_name = None


class DatabaseSystem:
    MYSQL = 'MySQL'
    MARIADB = 'MariaDB'


def run_database_command(client, command, force_database_name=False):
    """
    Run a database command using the "mysql -e" command
    :param client: String
    :param command: String database command
    :param force_database_name: Bool forces the database name
    :return:
    """
    _database_name = ' ' + system.config[client]['db']['name'] if force_database_name else ''

    return mode.run_command(
        helper.get_command(client, 'mysql') + ' ' + generate_mysql_credentials(
            client) + _database_name + ' -e "' + command + '"',
        client, True)


def generate_database_dump_filename():
    """
    Generate a database dump filename like "_[name]_[date].sql" or using the give filename
    :return:
    """
    global database_dump_file_name

    if system.config['dump_name'] == '':
        # _project-db_2022-08-22_12-37.sql
        _now = datetime.datetime.now()
        database_dump_file_name = '_' + system.config[mode.Client.ORIGIN]['db']['name'] + '_' + _now.strftime(
            "%Y-%m-%d_%H-%M") + '.sql'
    else:
        database_dump_file_name = system.config['dump_name'] + '.sql'


def truncate_tables():
    """
    Generate the ignore tables options for the mysqldump command by the given table list
    # ToDo: Too much conditional nesting
    :return: String
    """
    # Workaround for config naming
    if 'truncate_table' in system.config:
        system.config['truncate_tables'] = system.config['truncate_table']

    if 'truncate_tables' in system.config:
        output.message(
            output.Subject.TARGET,
            'Truncating tables before import',
            True
        )
        for _table in system.config['truncate_tables']:
            if '*' in _table:
                _wildcard_tables = get_database_tables_like(mode.Client.TARGET,
                                                            _table.replace('*', '%'))
                if _wildcard_tables:
                    for _wildcard_table in _wildcard_tables:
                        _sql_command = f'TRUNCATE TABLE {_wildcard_table}'
                        run_database_command(mode.Client.TARGET, _sql_command, True)
            else:
                # Check if table exists before truncating (MariaDB doesn't support IF EXISTS)
                _existing_tables = get_database_tables_like(mode.Client.TARGET, _table)
                if _existing_tables:
                    _sql_command = f'TRUNCATE TABLE {_table}'
                    run_database_command(mode.Client.TARGET, _sql_command, True)


def generate_ignore_database_tables():
    """
    Generate the ignore tables options for the mysqldump command by the given table list
    # ToDo: Too much conditional nesting
    :return: String
    """
    # Workaround for config naming
    if 'ignore_table' in system.config:
        system.config['ignore_tables'] = system.config['ignore_table']

    _ignore_tables = []
    if 'ignore_tables' in system.config:
        for table in system.config['ignore_tables']:
            if '*' in table:
                _wildcard_tables = get_database_tables_like(mode.Client.ORIGIN,
                                                            table.replace('*', '%'))
                if _wildcard_tables:
                    for wildcard_table in _wildcard_tables:
                        _ignore_tables = generate_ignore_database_table(_ignore_tables,
                                                                        wildcard_table)
            else:
                _ignore_tables = generate_ignore_database_table(_ignore_tables, table)
        return ' '.join(_ignore_tables)
    return ''


def generate_ignore_database_table(ignore_tables, table):
    """
    :param ignore_tables: Dictionary
    :param table: String
    :return: Dictionary
    """
    ignore_tables.append('--ignore-table=' + system.config['origin']['db']['name'] + '.' + table)
    return ignore_tables


def get_database_tables_like(client, name):
    """
    Get database table names like the given name
    :param client: String
    :param name: String
    :return: Dictionary
    """
    _dbname = system.config[client]['db']['name']
    _tables = run_database_command(client, f'SHOW TABLES FROM \`{_dbname}\` LIKE \'{name}\';').strip()
    if _tables != '':
        return _tables.split('\n')[1:]
    return


def get_database_tables():
    """
    Generate specific tables for export
    :return: String
    """
    if system.config['tables'] == '':
        return ''

    _result = ' '
    _tables = system.config['tables'].split(',')
    for _table in _tables:
        _result += '\'' + _table + '\' '
    return _result


def generate_mysql_credentials(client, force_password=True):
    """
    Generate the needed database credential information for the mysql command
    :param client: String
    :param force_password: Bool
    :return:
    """
    _credentials = '-u\'' + system.config[client]['db']['user'] + '\''
    if force_password:
        _credentials += ' -p\'' + system.config[client]['db']['password'] + '\''
    if 'host' in system.config[client]['db']:
        _credentials += ' -h\'' + system.config[client]['db']['host'] + '\''
    if 'port' in system.config[client]['db']:
        _credentials += ' -P\'' + str(system.config[client]['db']['port']) + '\''
    return _credentials


def check_database_dump(client, filepath):
    """
    Checking the last line of the dump file if it contains "-- Dump completed on"
    :param client: String
    :param filepath: String
    :return:
    """
    if system.config['check_dump']:
        _line = mode.run_command(
            helper.get_command(client, 'tail') + ' -n 1 ' + filepath,
            client,
            True,
            skip_dry_run=True
        )

        if not _line:
            return

        if "-- Dump completed on" not in _line:
            sys.exit(
                output.message(
                    output.Subject.ERROR,
                    'Dump file is corrupted',
                    do_print=False
                )
            )
        else:
            output.message(
                output.host_to_subject(client),
                'Dump file is valid',
                verbose_only=True
            )


def count_tables(client, filepath):
    """
    Count the reference string in the database dump file to get the count of all exported tables
    :param client: String
    :param filepath: String
    :return:
    """
    _reference = 'CREATE TABLE'
    _count = mode.run_command(
        f'{helper.get_command(client, "grep")} -ao "{_reference}" {filepath} | wc -l | xargs',
        client,
        True,
        skip_dry_run=True
    )

    if _count:
        output.message(
            output.host_to_subject(client),
            f'{int(_count)} table(s) exported'
        )


def get_database_version(client):
    """
    Check the database version and distinguish between mysql and mariadb
    :param client:
    :return: Tuple<String,String>
    """
    _database_system = None
    _version_number = None
    try:
        _database_version = run_database_command(client, 'SELECT VERSION();').splitlines()[1]
        _database_system = DatabaseSystem.MYSQL

        _version_number = re.search('(\d+\.)?(\d+\.)?(\*|\d+)', _database_version).group()

        if DatabaseSystem.MARIADB.lower() in _database_version.lower():
            _database_system = DatabaseSystem.MARIADB

        output.message(
            output.host_to_subject(client),
            f'Database version: {_database_system} v{_version_number}',
            True
        )
    finally:
        return _database_system, _version_number

