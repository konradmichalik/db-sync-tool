#!/usr/bin/env python3

"""
Main script - supports both argparse (default) and typer CLI.

Set DB_SYNC_TOOL_USE_TYPER=1 to use the typer-based CLI.
"""

import argparse
import os
import sys

# Workaround for ModuleNotFoundError
sys.path.append(os.getcwd())
from db_sync_tool import sync
from db_sync_tool.utility import helper
from db_sync_tool.utility.console import init_output_manager


def main(args=None):
    """
    Main entry point for the command line.

    Uses typer if DB_SYNC_TOOL_USE_TYPER=1 is set, otherwise uses argparse.
    :param args: Optional arguments dict (only used with argparse)
    :return:
    """
    use_typer = os.environ.get("DB_SYNC_TOOL_USE_TYPER", "0") == "1"

    if use_typer:
        from db_sync_tool.cli import run

        run()
    else:
        _main_argparse(args)


def _main_argparse(args=None):
    """
    Original argparse-based main function.
    :param args:
    :return:
    """
    if args is None:
        args = {}

    args = get_arguments(args)

    # Initialize output manager with format settings
    # --quiet flag overrides --output setting
    output_format = "quiet" if args.quiet else args.output
    init_output_manager(
        format=output_format, verbose=args.verbose, mute=args.mute or args.quiet
    )

    sync.Sync(
        config_file=args.config_file,
        verbose=args.verbose,
        yes=args.yes,
        mute=args.mute or args.quiet,
        dry_run=args.dry_run,
        import_file=args.import_file,
        dump_name=args.dump_name,
        keep_dump=args.keep_dump,
        host_file=args.host_file,
        clear=args.clear_database,
        force_password=args.force_password,
        use_rsync=args.use_rsync,
        use_rsync_options=args.use_rsync_options,
        reverse=args.reverse,
        args=args,
    )


def get_arguments(args):
    """
    Parses and returns script arguments
    :param args:
    :return:
    """
    parser = argparse.ArgumentParser(prog='db_sync_tool',
                                     description='A tool for automatic database synchronization from '
                                                 'and to host systems.')
    parser.add_argument('origin',
                        help='Origin database defined in host file',
                        nargs='?',
                        type=str)
    parser.add_argument('target',
                        help='Target database defined in host file',
                        nargs='?',
                        type=str)
    parser.add_argument('-f', '--config-file',
                        help='Path to configuration file',
                        required=False,
                        type=str)
    parser.add_argument('-v', '--verbose',
                        help='Enable verbose output (-v) or debug output (-vv)',
                        required=False,
                        action='count',
                        default=0)
    parser.add_argument('-y', '--yes',
                        help='Skipping user confirmation for database import',
                        required=False,
                        action='store_true')
    parser.add_argument('-m', '--mute',
                        help='Mute console output',
                        required=False,
                        action='store_true')
    parser.add_argument('-dr', '--dry-run',
                        help='Testing process without running database export, transfer or import.',
                        required=False,
                        action='store_true')
    parser.add_argument('-i', '--import-file',
                        help='Import database from a specific file dump',
                        required=False,
                        type=str)
    parser.add_argument('-dn', '--dump-name',
                        help='Set a specific dump file name (default is "_[dbname]_[date]")',
                        required=False,
                        type=str)
    parser.add_argument('-kd', '--keep-dump',
                        help='Skipping target import of the database dump and saving the available dump file in the '
                             'given directory',
                        required=False,
                        type=str)
    parser.add_argument('-o', '--host-file',
                        help='Using an additional hosts file for merging hosts information with the configuration file',
                        required=False,
                        type=str)
    parser.add_argument('-l', '--log-file',
                        help='File path for creating a additional log file',
                        required=False,
                        type=str)
    parser.add_argument('-cd', '--clear-database',
                        help='Dropping all tables before importing a new sync to get a clean database.',
                        required=False,
                        action='store_true')
    parser.add_argument('-ta', '--tables',
                        help='Defining specific tables to export, e.g. --tables=table1,table2',
                        required=False,
                        type=str)
    parser.add_argument('-r', '--reverse',
                        help='Reverse origin and target hosts',
                        required=False,
                        action='store_true')
    parser.add_argument('-t', '--type',
                        help='Defining the framework type [TYPO3, Symfony, Drupal, Wordpress]',
                        required=False,
                        type=str)
    parser.add_argument('-tp', '--target-path',
                        help='File path to target database credential file depending on the framework type',
                        required=False,
                        type=str)
    parser.add_argument('-tn', '--target-name',
                        help='Providing a name for the target system',
                        required=False,
                        type=str)
    parser.add_argument('-th', '--target-host',
                        help='SSH host to target system',
                        required=False,
                        type=str)
    parser.add_argument('-tu', '--target-user',
                        help='SSH user for target system',
                        required=False,
                        type=str)
    parser.add_argument('-tpw', '--target-password',
                        help='SSH password for target system',
                        required=False,
                        type=str)
    parser.add_argument('-tk', '--target-key',
                        help='File path to SSH key for target system',
                        required=False,
                        type=str)
    parser.add_argument('-tpo', '--target-port',
                        help='SSH port for target system',
                        required=False,
                        type=int)
    parser.add_argument('-tdd', '--target-dump-dir',
                        help='Directory path for database dump file on target system',
                        required=False,
                        type=str)
    parser.add_argument('-tkd', '--target-keep-dumps',
                        help='Keep dump file count for target system',
                        required=False,
                        type=int)
    parser.add_argument('-tdn', '--target-db-name',
                        help='Database name for target system',
                        required=False,
                        type=str)
    parser.add_argument('-tdh', '--target-db-host',
                        help='Database host for target system',
                        required=False,
                        type=str)
    parser.add_argument('-tdu', '--target-db-user',
                        help='Database user for target system',
                        required=False,
                        type=str)
    parser.add_argument('-tdpw', '--target-db-password',
                        help='Database password for target system',
                        required=False,
                        type=str)
    parser.add_argument('-tdpo', '--target-db-port',
                        help='Database port for target system',
                        required=False,
                        type=int)
    parser.add_argument('-tad', '--target-after-dump',
                        help='Additional dump file to insert after the regular database import',
                        required=False,
                        type=str)
    parser.add_argument('-op', '--origin-path',
                        help='File path to origin database credential file depending on the framework type',
                        required=False,
                        type=str)
    parser.add_argument('-on', '--origin-name',
                        help='Providing a name for the origin system',
                        required=False,
                        type=str)
    parser.add_argument('-oh', '--origin-host',
                        help='SSH host to origin system',
                        required=False,
                        type=str)
    parser.add_argument('-ou', '--origin-user',
                        help='SSH user for origin system',
                        required=False,
                        type=str)
    parser.add_argument('-opw', '--origin-password',
                        help='SSH password for origin system',
                        required=False,
                        type=str)
    parser.add_argument('-ok', '--origin-key',
                        help='File path to SSH key for origin system',
                        required=False,
                        type=str)
    parser.add_argument('-opo', '--origin-port',
                        help='SSH port for origin system',
                        required=False,
                        type=int)
    parser.add_argument('-odd', '--origin-dump-dir',
                        help='Directory path for database dump file on origin system',
                        required=False,
                        type=str)
    parser.add_argument('-okd', '--origin-keep-dumps',
                        help='Keep dump file count for origin system',
                        required=False,
                        type=int)
    parser.add_argument('-odn', '--origin-db-name',
                        help='Database name for origin system',
                        required=False,
                        type=str)
    parser.add_argument('-odh', '--origin-db-host',
                        help='Database host for origin system',
                        required=False,
                        type=str)
    parser.add_argument('-odu', '--origin-db-user',
                        help='Database user for origin system',
                        required=False,
                        type=str)
    parser.add_argument('-odpw', '--origin-db-password',
                        help='Database password for origin system',
                        required=False,
                        type=str)
    parser.add_argument('-odpo', '--origin-db-port',
                        help='Database port for origin system',
                        required=False,
                        type=int)
    parser.add_argument('-fpw', '--force-password',
                        help='Force password user query',
                        required=False,
                        action='store_true')
    parser.add_argument('-ur', '--use-rsync',
                        help='Use rsync as transfer method',
                        required=False,
                        action='store_true')
    parser.add_argument('-uro', '--use-rsync-options',
                        help='Additional rsync options',
                        required=False,
                        type=str)
    parser.add_argument('-w', '--where',
                        help='Additional where clause for mysql dump to sync only selected rows',
                        required=False,
                        type=str)
    parser.add_argument('-amo', '--additional-mysqldump-options',
                        help='Additional mysqldump options for creating the database dump, e.g. --additional-mysqldump-options="--where="deleted=0"',
                        required=False,
                        type=str)
    parser.add_argument('--output',
                        help='Output format: interactive (default), ci, json, quiet',
                        required=False,
                        choices=['interactive', 'ci', 'json', 'quiet'],
                        default='interactive',
                        type=str)
    parser.add_argument('-q', '--quiet',
                        help='Suppress all output except errors (shorthand for --output=quiet)',
                        required=False,
                        action='store_true')

    return parser.parse_args(helper.dict_to_args(args))


if __name__ == "__main__":
    main()
