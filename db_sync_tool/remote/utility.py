#!/usr/bin/env python3

"""
Utility script
"""

import os
import paramiko
from db_sync_tool.utility import mode, system, helper, output
from db_sync_tool.database import utility as database_utility
from db_sync_tool.remote import client as remote_client


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

    if system.config['dry_run']:
        return

    _file_path = helper.get_dump_dir(mode.Client.ORIGIN) + database_utility.database_dump_file_name
    _gz_path = _file_path + '.gz'

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
        if 'keep_dumps' in system.config[mode.Client.ORIGIN]:
            helper.clean_up_dump_dir(mode.Client.ORIGIN,
                                     helper.get_dump_dir(mode.Client.ORIGIN) + '*',
                                     system.config[mode.Client.ORIGIN]['keep_dumps'])

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
    _file_path = helper.get_dump_dir(mode.Client.TARGET) + database_utility.database_dump_file_name

    #
    # Move dump to specified directory
    #
    if system.config['keep_dump']:
        helper.create_local_temporary_data_dir()
        _keep_dump_path = system.default_local_sync_path + database_utility.database_dump_file_name
        mode.run_command(
            helper.get_command('target',
                               'cp') + ' ' + _file_path + ' ' + _keep_dump_path,
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

        if system.config['dry_run']:
            return

        _gz_path = _file_path + '.gz'
        if mode.is_target_remote():
            # Remove both decompressed .sql and compressed .gz
            mode.run_command(
                helper.get_command(mode.Client.TARGET, 'rm') + ' -f ' + _file_path + ' ' + _gz_path,
                mode.Client.TARGET
            )
        else:
            if os.path.isfile(_file_path):
                os.remove(_file_path)
            if os.path.isfile(_gz_path):
                os.remove(_gz_path)


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
