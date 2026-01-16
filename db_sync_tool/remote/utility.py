#!/usr/bin/env python3

"""
Utility script
"""

import os
import paramiko
from db_sync_tool.utility import mode, system, helper, output
from db_sync_tool.database import utility as database_utility


def remove_origin_database_dump(keep_compressed_file=False):
    """
    Removing the origin database dump files
    :param keep_compressed_file: Boolean
    :return:
    """
    output.message(
        output.Subject.ORIGIN,
        'Cleaning up',
        True
    )

    cfg = system.get_typed_config()
    if cfg.dry_run:
        return

    _gz_path = database_utility.get_dump_gz_path(mode.Client.ORIGIN)

    # With streaming compression, only .gz file exists on origin (no separate .sql)
    if not keep_compressed_file:
        if mode.is_origin_remote():
            mode.run_command(
                helper.get_command(mode.Client.ORIGIN, 'rm') + ' ' + _gz_path,
                mode.Client.ORIGIN
            )
        else:
            if os.path.isfile(_gz_path):
                os.remove(_gz_path)

    if keep_compressed_file:
        origin_cfg = cfg.origin
        if origin_cfg.keep_dumps is not None:
            helper.clean_up_dump_dir(mode.Client.ORIGIN,
                                     helper.get_dump_dir(mode.Client.ORIGIN) + '*',
                                     origin_cfg.keep_dumps)

        output.message(
            output.Subject.INFO,
            f'Database dump file is saved to: {_gz_path}',
            True,
            True
        )


def remove_target_database_dump():
    """
    Removing the target database dump files
    :return:
    """
    cfg = system.get_typed_config()
    _file_path = database_utility.get_dump_file_path(mode.Client.TARGET)
    _gz_file_path = database_utility.get_dump_gz_path(mode.Client.TARGET)

    #
    # Move dump to specified directory
    #
    if cfg.keep_dump:
        helper.create_local_temporary_data_dir()
        # Copy the .gz file (streaming compression means only .gz exists)
        # database_dump_file_name is guaranteed to be set at this point
        _dump_name = database_utility.database_dump_file_name or ''
        _keep_dump_path = system.default_local_sync_path + _dump_name + '.gz'
        mode.run_command(
            helper.get_command('target',
                               'cp') + ' ' + _gz_file_path + ' ' + _keep_dump_path,
            mode.Client.TARGET
        )
        output.message(
            output.Subject.INFO,
            f'Database dump file is saved to: {_keep_dump_path}',
            True,
            True
        )

    #
    # Clean up
    #
    if not mode.is_dump() and not mode.is_import():
        output.message(
            output.Subject.TARGET,
            'Cleaning up',
            True
        )

        if cfg.dry_run:
            return

        if mode.is_target_remote():
            # Remove both decompressed .sql and compressed .gz
            mode.run_command(
                helper.get_command(mode.Client.TARGET, 'rm') + ' -f ' + _file_path + ' ' + _gz_file_path,
                mode.Client.TARGET
            )
        else:
            if os.path.isfile(_file_path):
                os.remove(_file_path)
            if os.path.isfile(_gz_file_path):
                os.remove(_gz_file_path)


def check_keys_from_ssh_agent():
    """
    Check if private keys are available from an SSH agent.
    :return:
    """
    agent = paramiko.Agent()
    agent_keys = agent.get_keys()
    if len(agent_keys) == 0:
        return False
    return True
