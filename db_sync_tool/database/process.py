#!/usr/bin/env python3

"""
Process script
"""
import semantic_version

from db_sync_tool.utility import parser, mode, system, helper, output
from db_sync_tool.utility.helper import quote_shell_arg
from db_sync_tool.database import utility as database_utility


def create_origin_database_dump():
    """
    Creating the origin database dump file
    :return:
    """
    if not mode.is_import():
        parser.get_database_configuration(mode.Client.ORIGIN)
        database_utility.generate_database_dump_filename()
        helper.check_and_create_dump_dir(mode.Client.ORIGIN,
                                         helper.get_dump_dir(mode.Client.ORIGIN))

        _dump_file_path = database_utility.get_dump_file_path(mode.Client.ORIGIN)

        _database_version = database_utility.get_database_version(mode.Client.ORIGIN)
        output.message(
            output.Subject.ORIGIN,
            f'Creating database dump {output.CliFormat.BLACK}{_dump_file_path}{output.CliFormat.ENDC}',
            True
        )

        # Performance-optimized mysqldump options:
        # --single-transaction: Consistent snapshot without locks (InnoDB)
        # --quick: Row-by-row streaming instead of buffering in memory
        # --extended-insert: Multi-row INSERTs (30-50% smaller dumps)
        # --no-tablespaces: Skip tablespace info (requires PROCESS privilege in MySQL 8+)
        _mysqldump_options = '--single-transaction --quick --extended-insert --no-tablespaces '

        # Remove --no-tablespaces option for mysql < 5.6
        if _database_version is not None:
            if _database_version[0] == database_utility.DatabaseSystem.MYSQL and \
                    semantic_version.Version(_database_version[1]) < semantic_version.Version('5.6.0'):
                _mysqldump_options = '--single-transaction --quick --extended-insert '

        cfg = system.get_typed_config()

        # Adding additional where clause to sync only selected rows
        if cfg.where != '':
            _mysqldump_options = _mysqldump_options + f'--where=\'{cfg.where}\' '

        # Adding additional mysqldump options
        # see https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html#mysqldump-option-summary
        if cfg.additional_mysqldump_options != '':
            _mysqldump_options = _mysqldump_options + f'{cfg.additional_mysqldump_options} '

        # Run mysql dump command
        # Note: --defaults-file MUST be the first option for MySQL/MariaDB
        _db_name = quote_shell_arg(cfg.origin.db.name)
        _safe_dump_path = quote_shell_arg(_dump_file_path)

        # Get table names and shell-quote them safely (strip backticks first)
        _raw_tables = database_utility.get_database_tables()
        _safe_tables = ''
        if _raw_tables.strip():
            # Split on backtick-quoted names, strip backticks, shell-quote each
            _table_names = [t.strip('`') for t in _raw_tables.split() if t.strip('`')]
            _safe_tables = ' ' + ' '.join(quote_shell_arg(t) for t in _table_names)

        # Stream mysqldump directly to gzip (50% less I/O, 40% faster start)
        _safe_gz_path = quote_shell_arg(_dump_file_path + '.gz')
        mode.run_command(
            helper.get_command(mode.Client.ORIGIN, 'mysqldump') + ' ' +
            database_utility.generate_mysql_credentials(mode.Client.ORIGIN) + ' ' +
            _mysqldump_options + _db_name + ' ' +
            database_utility.generate_ignore_database_tables() +
            _safe_tables +
            ' | ' + helper.get_command(mode.Client.ORIGIN, 'gzip') + ' > ' + _safe_gz_path,
            mode.Client.ORIGIN,
            skip_dry_run=True
        )

        database_utility.check_database_dump(mode.Client.ORIGIN, _dump_file_path + '.gz')
        database_utility.count_tables(mode.Client.ORIGIN, _dump_file_path + '.gz')


def import_database_dump():
    """
    Importing the selected database dump file
    :return:
    """
    cfg = system.get_typed_config()

    # No need to decompress - import_database_dump_file streams .gz directly

    if cfg.clear_database:
        output.message(
            output.Subject.TARGET,
            'Clearing database before import',
            True
        )
        clear_database(mode.Client.TARGET)

    database_utility.truncate_tables()

    if not cfg.keep_dump and not mode.is_dump():

        database_utility.get_database_version(mode.Client.TARGET)

        output.message(
            output.Subject.TARGET,
            'Importing database dump',
            True
        )

        if mode.is_import():
            # External import file (user-provided path)
            _dump_path = cfg.import_file
        else:
            # Internal dump file (always .gz now)
            _dump_path = database_utility.get_dump_gz_path(mode.Client.TARGET)

        if not cfg.yes:
            _host_name = helper.get_ssh_host_name(mode.Client.TARGET, True) if mode.is_remote(
                mode.Client.TARGET) else 'local'

            _input = helper.confirm(
                output.message(
                    output.Subject.TARGET,
                    f'Are you sure, you want to import the dump file into {_host_name} database?',
                    False
                ),
                True
            )

            if not _input: return

        database_utility.check_database_dump(mode.Client.TARGET, _dump_path)

        import_database_dump_file(mode.Client.TARGET, _dump_path)

    if cfg.target.after_dump:
        output.message(
            output.Subject.TARGET,
            f'Importing after_dump file {output.CliFormat.BLACK}{cfg.target.after_dump}{output.CliFormat.ENDC}',
            True
        )
        import_database_dump_file(mode.Client.TARGET, cfg.target.after_dump)

    if cfg.target.post_sql:
        output.message(
            output.Subject.TARGET,
            f'Running addition post sql commands',
            True
        )
        for _sql_command in cfg.target.post_sql:
            database_utility.run_database_command(mode.Client.TARGET, _sql_command, True)


def import_database_dump_file(client, filepath):
    """
    Import a database dump file (supports both .sql and .gz files)
    :param client: String
    :param filepath: String
    :return:
    """
    if not helper.check_file_exists(client, filepath):
        return

    cfg = system.get_typed_config()
    _db_name = quote_shell_arg(cfg.get_client(client).db.name)
    _safe_filepath = quote_shell_arg(filepath)
    _mysql_cmd = (helper.get_command(client, 'mysql') + ' ' +
                  database_utility.generate_mysql_credentials(client) + ' ' + _db_name)

    # Stream .gz files directly to mysql (no intermediate decompression)
    if filepath.endswith('.gz'):
        _cmd = (helper.get_command(client, 'gunzip') + ' -c ' + _safe_filepath +
                ' | ' + _mysql_cmd)
    else:
        _cmd = _mysql_cmd + ' < ' + _safe_filepath

    mode.run_command(_cmd, client, skip_dry_run=True)


def clear_database(client):
    """
    Clearing the database by dropping all tables using pure SQL

    :param client: String
    :return:
    """
    # Get all tables via SQL query
    _tables_result = database_utility.run_database_command(client, 'SHOW TABLES;')
    if not _tables_result or not _tables_result.strip():
        return

    # Parse table names from result (skip header line)
    _lines = _tables_result.strip().split('\n')
    _tables = [line.strip() for line in _lines[1:] if line.strip()]

    if not _tables:
        return

    # Build and execute DROP statements
    statements = [f'DROP TABLE {database_utility.sanitize_table_name(t)}' for t in _tables]
    database_utility.run_sql_batch_with_fk_disabled(client, statements)
