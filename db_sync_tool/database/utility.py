#!/usr/bin/env python3

"""
Utility script
"""

import datetime
import re
import os
import secrets
import base64
from db_sync_tool.utility import mode, system, helper, output
from db_sync_tool.utility.security import sanitize_table_name  # noqa: F401 (re-export)
from db_sync_tool.utility.exceptions import ConfigError, DbSyncError

database_dump_file_name: str | None = None

# Track MySQL config files for cleanup (client -> path)
_mysql_config_files: dict[str, str] = {}


class DatabaseSystem:
    MYSQL = 'MySQL'
    MARIADB = 'MariaDB'


def create_mysql_config_file(client: str) -> str:
    """
    Create a secure temporary MySQL config file with credentials.
    This prevents passwords from appearing in process lists (ps aux).

    :param client: String client identifier ('origin' or 'target')
    :return: String path to the config file
    """
    global _mysql_config_files

    cfg = system.get_typed_config()
    client_cfg = cfg.get_client(client)

    # Verify database config exists
    if not client_cfg.db.name and not client_cfg.db.user:
        raise ConfigError(f"Database configuration not found for client: {client}")

    db_config = client_cfg.db

    # Build config file content
    # Passwords must be quoted to handle special chars like # ; $ etc.
    # Inside double quotes, escape \ and "
    escaped_password = db_config.password.replace('\\', '\\\\').replace('"', '\\"')
    config_content = "[client]\n"
    config_content += f"user={db_config.user}\n"
    config_content += f'password="{escaped_password}"\n'
    if db_config.host:
        config_content += f"host={db_config.host}\n"
    if db_config.port:
        config_content += f"port={db_config.port}\n"

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
        result = result.strip() if result else ''
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


def get_mysql_config_path(client: str) -> str:
    """
    Get the MySQL config file path for a client, creating it if necessary.

    :param client: String client identifier
    :return: String path to the config file
    """
    if client not in _mysql_config_files:
        create_mysql_config_file(client)
    return _mysql_config_files[client]


def cleanup_mysql_config_files() -> None:
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


def run_database_command(client: str, command: str, force_database_name: bool = False) -> str:
    """
    Run a database command using the "mysql -e" command
    :param client: Client identifier
    :param command: Database command
    :param force_database_name: Forces the database name
    :return: Command output
    """
    _database_name = ''
    if force_database_name:
        cfg = system.get_typed_config()
        _database_name = ' ' + helper.quote_shell_arg(cfg.get_client(client).db.name)

    # Escape the SQL command for shell
    # - Backslashes need doubling
    # - Double quotes need escaping
    # - Backticks need escaping (shell command substitution)
    _safe_command = command.replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`')

    result = mode.run_command(
        helper.get_command(client, 'mysql') + ' ' + generate_mysql_credentials(
            client) + _database_name + ' -e "' + _safe_command + '"',
        client, True)
    return result if result else ''


def run_sql_batch_with_fk_disabled(client: str, statements: list[str]) -> None:
    """
    Execute multiple SQL statements in one roundtrip with FK checks disabled.
    DRY helper for batch operations like TRUNCATE or DROP.

    :param client: Client identifier
    :param statements: List of SQL statements (without trailing semicolons)
    """
    if not statements:
        return
    sql = 'SET FOREIGN_KEY_CHECKS = 0; ' + '; '.join(statements) + '; SET FOREIGN_KEY_CHECKS = 1;'
    run_database_command(client, sql, True)


def generate_database_dump_filename() -> None:
    """
    Generate a database dump filename like "_[name]_[date].sql" or using the give filename
    """
    global database_dump_file_name

    cfg = system.get_typed_config()
    if cfg.dump_name == '':
        # _project-db_2022-08-22_12-37.sql
        _now = datetime.datetime.now()
        database_dump_file_name = '_' + cfg.origin.db.name + '_' + _now.strftime(
            "%Y-%m-%d_%H-%M") + '.sql'
    else:
        database_dump_file_name = cfg.dump_name + '.sql'


def truncate_tables() -> None:
    """
    Truncate specified tables before import using batch operation
    """
    cfg = system.get_typed_config()

    if not cfg.truncate_tables:
        return

    output.message(
        output.Subject.TARGET,
        'Truncating tables before import',
        True
    )

    # Collect all tables to truncate (80-90% fewer network roundtrips)
    tables_to_truncate = []
    for _table in cfg.truncate_tables:
        if '*' in _table:
            _wildcard_tables = get_database_tables_like(mode.Client.TARGET,
                                                        _table.replace('*', '%'))
            if _wildcard_tables:
                tables_to_truncate.extend(_wildcard_tables)
        else:
            # Check if table exists (MariaDB doesn't support IF EXISTS)
            _existing_tables = get_database_tables_like(mode.Client.TARGET, _table)
            if _existing_tables:
                tables_to_truncate.append(_table)

    if not tables_to_truncate:
        return

    # Build and execute TRUNCATE statements
    statements = [f'TRUNCATE TABLE {sanitize_table_name(t)}' for t in tables_to_truncate]
    run_sql_batch_with_fk_disabled(mode.Client.TARGET, statements)


def generate_ignore_database_tables() -> str:
    """
    Generate the ignore tables options for the mysqldump command by the given table list
    :return: String of ignore table options
    """
    cfg = system.get_typed_config()

    _ignore_tables: list[str] = []
    if cfg.ignore_tables:
        for table in cfg.ignore_tables:
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


def generate_ignore_database_table(ignore_tables: list[str], table: str) -> list[str]:
    """
    :param ignore_tables: List of ignore table options
    :param table: Table name to add
    :return: Updated list of ignore table options
    """
    cfg = system.get_typed_config()
    # Validate table name to prevent injection
    _safe_table = sanitize_table_name(table)
    # Remove backticks for mysqldump --ignore-table option (it doesn't use them)
    _table_name = _safe_table.strip('`')
    # Validate database name (same rules as table names)
    _safe_db = sanitize_table_name(cfg.origin.db.name)
    _db_name = _safe_db.strip('`')
    ignore_tables.append(f'--ignore-table={_db_name}.{_table_name}')
    return ignore_tables


def get_database_tables_like(client: str, name: str) -> list[str] | None:
    """
    Get database table names like the given name
    :param client: Client identifier
    :param name: Pattern (may contain % wildcard)
    :return: List of table names or None
    """
    cfg = system.get_typed_config()
    _dbname = cfg.get_client(client).db.name
    # Validate database name to prevent SQL injection
    _safe_dbname = sanitize_table_name(_dbname)
    # Escape single quotes in the pattern to prevent SQL injection
    _safe_pattern = name.replace("'", "''")
    _tables = run_database_command(client, f'SHOW TABLES FROM {_safe_dbname} LIKE \'{_safe_pattern}\';').strip()
    if _tables != '':
        return _tables.split('\n')[1:]
    return None


def get_database_tables() -> str:
    """
    Generate specific tables for export
    :return: String of table names
    """
    cfg = system.get_typed_config()
    if cfg.tables == '':
        return ''

    _result = ' '
    _tables = cfg.tables.split(',')
    for _table in _tables:
        # Validate table name to prevent injection
        _safe_table = sanitize_table_name(_table.strip())
        # Use backtick-quoted name for shell command
        _result += _safe_table + ' '
    return _result


def generate_mysql_credentials(client: str, force_password: bool = True) -> str:
    """
    Generate the needed database credential information for the mysql command.
    Uses --defaults-extra-file to prevent passwords from appearing in process lists
    while preserving system MySQL configuration (including SSL settings).

    :param client: Client identifier
    :param force_password: Kept for backwards compatibility, now always uses secure method
    :return: MySQL credentials argument
    """
    try:
        config_path = get_mysql_config_path(client)
        # Note: --defaults-extra-file must NOT have quotes around the path
        # mysqldump/mysql parse this option specially
        # Using --defaults-extra-file (not --defaults-file) preserves system config
        credentials = f"--defaults-extra-file={config_path}"

        cfg = system.get_typed_config()
        if cfg.verbose:
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


def _generate_mysql_credentials_legacy(client: str, force_password: bool = True) -> str:
    """
    Legacy method: Generate MySQL credentials as command line arguments.
    WARNING: This exposes passwords in process lists!

    :param client: Client identifier
    :param force_password: Include password in credentials
    :return: MySQL credentials arguments
    """
    cfg = system.get_typed_config()
    db_cfg = cfg.get_client(client).db
    _credentials = '-u\'' + db_cfg.user + '\''
    if force_password:
        _credentials += ' -p\'' + db_cfg.password + '\''
    if db_cfg.host:
        _credentials += ' -h\'' + db_cfg.host + '\''
    if db_cfg.port:
        _credentials += ' -P\'' + str(db_cfg.port) + '\''
    return _credentials


def get_dump_file_path(client: str) -> str:
    """
    Get the path to the dump file (without .gz extension).
    DRY helper for consistent path construction.

    :param client: Client identifier
    :return: Path to dump file
    """
    if database_dump_file_name is None:
        raise DbSyncError('database_dump_file_name not initialized')
    return helper.get_dump_dir(client) + database_dump_file_name


def get_dump_gz_path(client: str) -> str:
    """
    Get the path to the compressed dump file (.gz).
    DRY helper for consistent path construction.

    :param client: Client identifier
    :return: Path to compressed dump file
    """
    return get_dump_file_path(client) + '.gz'


def get_dump_cat_command(client: str, filepath: str) -> str:
    """
    Get the appropriate command to read a dump file (handles .gz compression).
    DRY helper for check_database_dump and count_tables.

    :param client: Client identifier
    :param filepath: Path to dump file
    :return: Command prefix for reading the file
    """
    _safe_filepath = helper.quote_shell_arg(filepath)
    if filepath.endswith('.gz'):
        return f'{helper.get_command(client, "gunzip")} -c {_safe_filepath}'
    return f'{helper.get_command(client, "cat")} {_safe_filepath}'


def check_database_dump(client: str, filepath: str) -> None:
    """
    Checking the last line of the dump file if it contains "-- Dump completed on"
    :param client: Client identifier
    :param filepath: Path to dump file
    """
    cfg = system.get_typed_config()
    if not cfg.check_dump:
        return

    _cmd = f'{get_dump_cat_command(client, filepath)} | tail -n 1'
    _line = mode.run_command(_cmd, client, True, skip_dry_run=True)

    if not _line:
        return

    if "-- Dump completed on" not in _line:
        raise DbSyncError('Dump file is corrupted')
    output.message(
        output.host_to_subject(client),
        'Dump file is valid',
        verbose_only=True
    )


def count_tables(client: str, filepath: str) -> None:
    """
    Count the reference string in the database dump file to get the count of all exported tables
    :param client: Client identifier
    :param filepath: Path to dump file
    """
    _reference = 'CREATE TABLE'
    _cmd = f'{get_dump_cat_command(client, filepath)} | grep -ao "{_reference}" | wc -l | xargs'
    _count = mode.run_command(_cmd, client, True, skip_dry_run=True)

    if _count:
        output.message(
            output.host_to_subject(client),
            f'{int(_count)} table(s) exported'
        )


def get_database_version(client: str) -> tuple[str | None, str | None]:
    """
    Check the database version and distinguish between mysql and mariadb
    :param client: Client identifier
    :return: Tuple of (database_system, version_number)
    """
    _database_system = None
    _version_number = None
    try:
        _database_version = run_database_command(client, 'SELECT VERSION();').splitlines()[1]
        _database_system = DatabaseSystem.MYSQL

        _version_match = re.search(r'(\d+\.)?(\d+\.)?(\*|\d+)', _database_version)
        _version_number = _version_match.group() if _version_match else None

        if DatabaseSystem.MARIADB.lower() in _database_version.lower():
            _database_system = DatabaseSystem.MARIADB

        output.message(
            output.host_to_subject(client),
            f'Database version: {_database_system} v{_version_number}',
            True
        )
    finally:
        return _database_system, _version_number

