#!/usr/bin/env python3

"""
Utility script
"""

import sys
import datetime
import re
import tempfile
import os
import secrets
import base64
from db_sync_tool.utility import mode, system, helper, output

database_dump_file_name = None

# Track MySQL config files for cleanup (client -> path)
_mysql_config_files = {}


class DatabaseSystem:
    MYSQL = 'MySQL'
    MARIADB = 'MariaDB'


def sanitize_table_name(table):
    """
    Validate and sanitize a table name to prevent SQL injection.
    MySQL table names can contain alphanumeric chars, underscores, and dollar signs.
    They can also contain hyphens and dots in quoted identifiers.

    :param table: String table name
    :return: String sanitized and backtick-quoted table name
    :raises ValueError: If table name contains invalid characters
    """
    if not table:
        raise ValueError("Table name cannot be empty")

    # Allow alphanumeric, underscore, hyphen, dot, dollar sign
    # These are valid MySQL identifier characters
    if not re.match(r'^[a-zA-Z0-9_$.-]+$', table):
        raise ValueError(f"Invalid table name: {table}")

    # Return backtick-quoted identifier (safe for MySQL)
    return f"`{table}`"


def create_mysql_config_file(client):
    """
    Create a secure temporary MySQL config file with credentials.
    This prevents passwords from appearing in process lists (ps aux).

    :param client: String client identifier ('origin' or 'target')
    :return: String path to the config file
    """
    global _mysql_config_files

    # Verify database config exists
    if client not in system.config or 'db' not in system.config[client]:
        raise ValueError(f"Database configuration not found for client: {client}")

    db_config = system.config[client]['db']

    # Build config file content
    config_content = "[client]\n"
    config_content += f"user={db_config.get('user', '')}\n"
    config_content += f"password={db_config.get('password', '')}\n"
    if 'host' in db_config:
        config_content += f"host={db_config['host']}\n"
    if 'port' in db_config:
        config_content += f"port={db_config['port']}\n"
    # Disable SSL by default (can be overridden in config)
    if db_config.get('ssl', False) is False:
        config_content += "ssl=0\n"

    random_suffix = secrets.token_hex(8)
    config_path = f"/tmp/.my_{random_suffix}.cnf"

    if mode.is_remote(client):
        # For remote clients, create config file on remote system
        # Using base64 encoding to safely handle special characters in passwords
        encoded_content = base64.b64encode(config_content.encode()).decode()
        # Use force_output=True to ensure command completes before proceeding
        result = mode.run_command(
            f"echo '{encoded_content}' | base64 -d > {config_path} && chmod 600 {config_path} && echo 'OK'",
            client,
            force_output=True,
            skip_dry_run=True
        )
        if result != 'OK':
            output.message(
                output.Subject.WARNING,
                f'Failed to create MySQL config file on remote: {result}',
                True
            )
    else:
        # For local clients, write directly
        with open(config_path, 'w') as f:
            f.write(config_content)
        os.chmod(config_path, 0o600)

    _mysql_config_files[client] = config_path
    return config_path


def get_mysql_config_path(client):
    """
    Get the MySQL config file path for a client, creating it if necessary.

    :param client: String client identifier
    :return: String path to the config file
    """
    if client not in _mysql_config_files:
        create_mysql_config_file(client)
    return _mysql_config_files[client]


def cleanup_mysql_config_files():
    """
    Remove all temporary MySQL config files.
    Should be called during cleanup phase.
    """
    global _mysql_config_files

    for client, config_path in _mysql_config_files.items():
        try:
            if mode.is_remote(client):
                mode.run_command(
                    f"rm -f {config_path}",
                    client,
                    allow_fail=True,
                    skip_dry_run=True
                )
            else:
                if os.path.exists(config_path):
                    os.remove(config_path)
        except Exception:
            # Silently ignore cleanup errors
            pass

    _mysql_config_files = {}


def run_database_command(client, command, force_database_name=False):
    """
    Run a database command using the "mysql -e" command
    :param client: String
    :param command: String database command
    :param force_database_name: Bool forces the database name
    :return:
    """
    _database_name = ''
    if force_database_name:
        _database_name = ' ' + helper.quote_shell_arg(system.config[client]['db']['name'])

    # Escape the SQL command for shell (double quotes inside need escaping)
    _safe_command = command.replace('\\', '\\\\').replace('"', '\\"')

    return mode.run_command(
        helper.get_command(client, 'mysql') + ' ' + generate_mysql_credentials(
            client) + _database_name + ' -e "' + _safe_command + '"',
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
    Truncate specified tables before import
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
                        _safe_table = sanitize_table_name(_wildcard_table)
                        _sql_command = f'TRUNCATE TABLE {_safe_table}'
                        run_database_command(mode.Client.TARGET, _sql_command, True)
            else:
                # Check if table exists before truncating (MariaDB doesn't support IF EXISTS)
                _existing_tables = get_database_tables_like(mode.Client.TARGET, _table)
                if _existing_tables:
                    _safe_table = sanitize_table_name(_table)
                    _sql_command = f'TRUNCATE TABLE {_safe_table}'
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
    :param ignore_tables: List
    :param table: String
    :return: List
    """
    # Validate table name to prevent injection
    _safe_table = sanitize_table_name(table)
    # Remove backticks for mysqldump --ignore-table option (it doesn't use them)
    _table_name = _safe_table.strip('`')
    _db_name = system.config['origin']['db']['name']
    ignore_tables.append(f'--ignore-table={_db_name}.{_table_name}')
    return ignore_tables


def get_database_tables_like(client, name):
    """
    Get database table names like the given name
    :param client: String
    :param name: String pattern (may contain % wildcard)
    :return: List of table names or None
    """
    _dbname = system.config[client]['db']['name']
    # Escape single quotes in the pattern to prevent SQL injection
    _safe_pattern = name.replace("'", "''")
    _tables = run_database_command(client, f'SHOW TABLES FROM `{_dbname}` LIKE \'{_safe_pattern}\';').strip()
    if _tables != '':
        return _tables.split('\n')[1:]
    return None


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
        # Validate table name to prevent injection
        _safe_table = sanitize_table_name(_table.strip())
        # Use backtick-quoted name for shell command
        _result += _safe_table + ' '
    return _result


def generate_mysql_credentials(client, force_password=True):
    """
    Generate the needed database credential information for the mysql command.
    Uses --defaults-file to prevent passwords from appearing in process lists.

    :param client: String client identifier
    :param force_password: Bool (kept for backwards compatibility, now always uses secure method)
    :return: String MySQL credentials argument
    """
    try:
        config_path = get_mysql_config_path(client)
        # Note: --defaults-file must NOT have quotes around the path
        # mysqldump/mysql parse this option specially
        credentials = f"--defaults-file={config_path}"

        if system.config.get('verbose', False):
            output.message(
                output.host_to_subject(client),
                f'Using secure credentials file: {config_path}',
                verbose_only=True
            )

        return credentials
    except Exception as e:
        # Fallback to legacy method if config file creation fails
        output.message(
            output.Subject.WARNING,
            f'Falling back to legacy credentials (config file failed: {e})',
            True
        )
        return _generate_mysql_credentials_legacy(client, force_password)


def _generate_mysql_credentials_legacy(client, force_password=True):
    """
    Legacy method: Generate MySQL credentials as command line arguments.
    WARNING: This exposes passwords in process lists!

    :param client: String client identifier
    :param force_password: Bool
    :return: String MySQL credentials arguments
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

