#!/usr/bin/env python3
"""
Sync script
"""

import sys
from db_sync_tool.utility import system, helper, info, output
from db_sync_tool.utility.exceptions import DbSyncError
from db_sync_tool.database import process, utility as database_utility
from db_sync_tool.remote import transfer, client as remote_client


class Sync:
    """
    Synchronize a target database from an origin system
    """

    def __init__(self,
                 config_file=None,
                 verbose=False,
                 yes=False,
                 mute=False,
                 dry_run=False,
                 import_file=None,
                 dump_name=None,
                 keep_dump=None,
                 host_file=None,
                 clear=False,
                 force_password=False,
                 use_rsync=False,
                 use_rsync_options=None,
                 reverse=False,
                 config=None,
                 args=None):
        """
        Initialization
        :param config_file:
        :param verbose:
        :param yes:
        :param mute:
        :param dry_run:
        :param import_file:
        :param dump_name:
        :param keep_dump:
        :param host_file:
        :param clear:
        :param force_password:
        :param use_rsync:
        :param use_rsync_options:
        :param reverse:
        :param config:
        :param args:
        """
        if config is None:
            config = {}

        info.print_header(mute, verbose)
        try:
            system.check_args_options(
                config_file,
                verbose,
                yes,
                mute,
                dry_run,
                import_file,
                dump_name,
                keep_dump,
                host_file,
                clear,
                force_password,
                use_rsync,
                use_rsync_options,
                reverse
            )
            system.get_configuration(config, args)
            system.check_authorizations()
            process.create_origin_database_dump()
            transfer.transfer_origin_database_dump()
            process.import_database_dump()
            helper.clean_up()
        except DbSyncError as e:
            output.message(output.Subject.ERROR, str(e), do_print=True)
            sys.exit(1)
        finally:
            # Always clean up sensitive credential files, even on error
            database_utility.cleanup_mysql_config_files()
            remote_client.close_ssh_clients()
        info.print_footer()
