#!/usr/bin/env python3

"""
Process script
"""
import semantic_version

from db_sync_tool.utility import parser, mode, system, helper, output
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

        _dump_file_path = helper.get_dump_dir(
            mode.Client.ORIGIN) + database_utility.database_dump_file_name

        _database_version = database_utility.get_database_version(mode.Client.ORIGIN)
        output.message(
            output.Subject.ORIGIN,
            f'Creating database dump {output.CliFormat.BLACK}{_dump_file_path}{output.CliFormat.ENDC}',
            True
        )

        _mysqldump_options = '--no-tablespaces '
        # Remove --no-tablespaces option for mysql < 5.6
        # @ToDo: Better option handling
        if not _database_version is None:
            if _database_version[0] == database_utility.DatabaseSystem.MYSQL and \
                    semantic_version.Version(_database_version[1]) < semantic_version.Version('5.6.0'):
                _mysqldump_options = ''

        # Adding additional where clause to sync only selected rows
        if system.config['where'] != '':
            _where = system.config['where']
            _mysqldump_options = _mysqldump_options + f'--where=\'{_where}\' '

        # Adding additional mysqldump options
        # see https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html#mysqldump-option-summary
        if system.config['additional_mysqldump_options'] != '':
            _additional = system.config['additional_mysqldump_options']
            _mysqldump_options = _mysqldump_options + f'{_additional} '

        # Run mysql dump command, e.g.
        # mysqldump --no-tablespaces -u'db' -p'db' -h'db1' -P'3306' 'db'  > /tmp/_db_08-10-2021_07-00.sql
        mode.run_command(
            helper.get_command(mode.Client.ORIGIN, 'mysqldump') + ' ' + _mysqldump_options +
            database_utility.generate_mysql_credentials(mode.Client.ORIGIN) + ' \'' +
            system.config[mode.Client.ORIGIN]['db']['name'] + '\' ' +
            database_utility.generate_ignore_database_tables() +
            database_utility.get_database_tables() +
            ' > ' + _dump_file_path,
            mode.Client.ORIGIN,
            skip_dry_run=True
        )

        database_utility.check_database_dump(mode.Client.ORIGIN, _dump_file_path)
        database_utility.count_tables(mode.Client.ORIGIN, _dump_file_path)
        prepare_origin_database_dump()


def import_database_dump():
    """
    Importing the selected database dump file
    :return:
    """
    if not system.config['is_same_client'] and not mode.is_import():
        prepare_target_database_dump()

    if system.config['clear_database']:
        output.message(
            output.Subject.TARGET,
            'Clearing database before import',
            True
        )
        clear_database(mode.Client.TARGET)

    database_utility.truncate_tables()

    if not system.config['keep_dump'] and not mode.is_dump():

        database_utility.get_database_version(mode.Client.TARGET)

        output.message(
            output.Subject.TARGET,
            'Importing database dump',
            True
        )

        if not mode.is_import():
            _dump_path = helper.get_dump_dir(
                mode.Client.TARGET) + database_utility.database_dump_file_name
        else:
            _dump_path = system.config['import']

        if not system.config['yes']:
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

    if 'after_dump' in system.config['target']:
        _after_dump = system.config['target']['after_dump']
        output.message(
            output.Subject.TARGET,
            f'Importing after_dump file {output.CliFormat.BLACK}{_after_dump}{output.CliFormat.ENDC}',
            True
        )
        import_database_dump_file(mode.Client.TARGET, _after_dump)

    if 'post_sql' in system.config['target']:
        output.message(
            output.Subject.TARGET,
            f'Running addition post sql commands',
            True
        )
        for _sql_command in system.config['target']['post_sql']:
            database_utility.run_database_command(mode.Client.TARGET, _sql_command, True)


def import_database_dump_file(client, filepath):
    """
    Import a database dump file
    :param client: String
    :param filepath: String
    :return:
    """
    if helper.check_file_exists(client, filepath):
        mode.run_command(
            helper.get_command(client, 'mysql') + ' ' +
            database_utility.generate_mysql_credentials(client) + ' \'' +
            system.config[client]['db']['name'] + '\' < ' + filepath,
            client,
            skip_dry_run=True
        )


def prepare_origin_database_dump():
    """
    Preparing the origin database dump file by compressing them as .tar.gz
    :return:
    """
    output.message(
        output.Subject.ORIGIN,
        'Compressing database dump',
        True
    )
    mode.run_command(
        helper.get_command(mode.Client.ORIGIN, 'tar') + ' cfvz ' + helper.get_dump_dir(
            mode.Client.ORIGIN) + database_utility.database_dump_file_name + '.tar.gz -C ' +
        helper.get_dump_dir(mode.Client.ORIGIN) + ' ' +
        database_utility.database_dump_file_name + ' > /dev/null',
        mode.Client.ORIGIN,
        skip_dry_run=True
    )


def prepare_target_database_dump():
    """
    Preparing the target database dump by the unpacked .tar.gz file
    :return:
    """
    output.message(output.Subject.TARGET, 'Extracting database dump', True)
    mode.run_command(
        helper.get_command('target', 'tar') + ' xzf ' + helper.get_dump_dir(mode.Client.TARGET) +
        database_utility.database_dump_file_name + '.tar.gz -C ' +
        helper.get_dump_dir(mode.Client.TARGET) + ' > /dev/null',
        mode.Client.TARGET,
        skip_dry_run=True
    )


def clear_database(client):
    """
    Clearing the database by dropping all tables
    https://www.techawaken.com/drop-tables-mysql-database/

    { mysql -hHOSTNAME -uUSERNAME -pPASSWORD -Nse 'show tables' DB_NAME; } |
    ( while read table; do if [ -z ${i+x} ]; then echo 'SET FOREIGN_KEY_CHECKS = 0;'; fi; i=1;
    echo "drop table \`$table\`;"; done;
    echo 'SET FOREIGN_KEY_CHECKS = 1;' ) |
    awk '{print}' ORS=' ' | mysql -hHOSTNAME -uUSERNAME -pPASSWORD DB_NAME;

    :param client: String
    :return:
    """
    mode.run_command(
        '{ ' + helper.get_command(client, 'mysql') + ' ' +
        database_utility.generate_mysql_credentials(client) +
        ' -Nse \'show tables\' \'' +
        system.config[client]['db']['name'] + '\'; }' +
        ' | ( while read table; do if [ -z ${i+x} ]; then echo \'SET FOREIGN_KEY_CHECKS = 0;\'; fi; i=1; ' +
        'echo "drop table \\`$table\\`;"; done; echo \'SET FOREIGN_KEY_CHECKS = 1;\' ) | awk \'{print}\' ORS=' ' | ' +
        ' ' +
        helper.get_command(client, 'mysql') + ' ' +
        database_utility.generate_mysql_credentials(client) + ' ' +
        system.config[client]['db']['name'],
        client,
        skip_dry_run=True
    )
