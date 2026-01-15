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
    if mode.is_origin_remote():
        mode.run_command(
            helper.get_command(mode.Client.ORIGIN, 'rm') + ' ' + _file_path,
            mode.Client.ORIGIN
        )
        if not keep_compressed_file:
            mode.run_command(
                helper.get_command(mode.Client.ORIGIN, 'rm') + ' ' + _file_path + '.tar.gz',
                mode.Client.ORIGIN
            )
    else:
        os.remove(_file_path)
        if not keep_compressed_file:
            os.remove(f'{_file_path}.tar.gz')

    if keep_compressed_file:
        if 'keep_dumps' in system.config[mode.Client.ORIGIN]:
            helper.clean_up_dump_dir(mode.Client.ORIGIN,
                                     helper.get_dump_dir(mode.Client.ORIGIN) + '*',
                                     system.config[mode.Client.ORIGIN]['keep_dumps'])

        output.message(
            output.Subject.INFO,
            f'Database dump file is saved to: {_file_path}.tar.gz',
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

        if mode.is_target_remote():
            mode.run_command(
                helper.get_command(mode.Client.TARGET, 'rm') + ' ' + _file_path,
                mode.Client.TARGET
            )
            mode.run_command(
                helper.get_command(mode.Client.TARGET, 'rm') + ' ' + _file_path + '.tar.gz',
                mode.Client.TARGET
            )
        else:
            if os.path.isfile(_file_path):
                os.remove(_file_path)
            if os.path.isfile(f'{_file_path}.tar.gz'):
                os.remove(f'{_file_path}.tar.gz')


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
