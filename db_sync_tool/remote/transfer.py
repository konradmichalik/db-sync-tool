#!/usr/bin/env python3

"""
Transfer script
"""

import sys
from db_sync_tool.utility import mode, system, helper, output
from db_sync_tool.database import utility as database_utility
from db_sync_tool.remote import utility, client, rsync


def transfer_origin_database_dump():
    """
    Transfer the origin database dump files
    :return:
    """
    if not mode.is_import():
        if mode.get_sync_mode() == mode.SyncMode.RECEIVER:
            get_origin_database_dump(helper.get_dump_dir(mode.Client.TARGET))
            system.check_target_configuration()
        elif mode.get_sync_mode() == mode.SyncMode.SENDER:
            system.check_target_configuration()
            put_origin_database_dump(helper.get_dump_dir(mode.Client.ORIGIN))
            utility.remove_origin_database_dump()
        elif mode.get_sync_mode() == mode.SyncMode.PROXY:
            helper.create_local_temporary_data_dir()
            get_origin_database_dump(system.default_local_sync_path)
            system.check_target_configuration()
            put_origin_database_dump(system.default_local_sync_path)
        elif mode.get_sync_mode() == mode.SyncMode.SYNC_REMOTE or mode.get_sync_mode() == mode.SyncMode.SYNC_LOCAL:
            system.check_target_configuration()
        elif system.config['is_same_client']:
            utility.remove_origin_database_dump(True)
    else:
        system.check_target_configuration()


def get_origin_database_dump(target_path):
    """
    Downloading the origin database dump files
    :param target_path: String
    :return:
    """
    output.message(
        output.Subject.ORIGIN,
        'Downloading database dump',
        True
    )
    if mode.get_sync_mode() != mode.SyncMode.PROXY:
        helper.check_and_create_dump_dir(mode.Client.TARGET, target_path)

    if not system.config['dry_run']:
        _remotepath = helper.get_dump_dir(mode.Client.ORIGIN) + database_utility.database_dump_file_name + '.tar.gz'
        _localpath = target_path

        if system.config['use_rsync']:
            rsync.run_rsync_command(
                remote_client=mode.Client.ORIGIN,
                origin_path=_remotepath,
                target_path=_localpath,
                origin_ssh=system.config[mode.Client.ORIGIN]['user'] + '@' + system.config[mode.Client.ORIGIN]['host']
            )
        else:
            #
            # Download speed problems
            # https://github.com/paramiko/paramiko/issues/60
            #
            sftp = get_sftp_client(client.ssh_client_origin)
            sftp.get(helper.get_dump_dir(mode.Client.ORIGIN) + database_utility.database_dump_file_name + '.tar.gz',
                     target_path + database_utility.database_dump_file_name + '.tar.gz', download_status)
            sftp.close()
            if not system.config['mute']:
                print('')

    utility.remove_origin_database_dump()


def _transfer_status(sent, size, direction, subject_override=None):
    """
    Print transfer progress status.

    :param sent: Bytes transferred
    :param size: Total bytes
    :param direction: 'downloaded' or 'uploaded'
    :param subject_override: Optional subject prefix override
    """
    if system.config['mute']:
        return

    sent_mb = round(float(sent) / 1024 / 1024, 1)
    size_mb = round(float(size) / 1024 / 1024, 1)

    if subject_override:
        subject = subject_override
    elif direction == 'downloaded':
        subject = output.Subject.ORIGIN + output.CliFormat.BLACK + '[REMOTE]' + output.CliFormat.ENDC
    elif mode.get_sync_mode() == mode.SyncMode.PROXY:
        subject = output.Subject.LOCAL
    else:
        subject = output.Subject.ORIGIN + output.CliFormat.BLACK + '[LOCAL]' + output.CliFormat.ENDC

    sys.stdout.write(f"{subject} Status: {sent_mb} MB of {size_mb} MB {direction}")
    sys.stdout.write('\r')


def download_status(sent, size):
    """
    Callback for SFTP download progress.

    :param sent: Bytes transferred
    :param size: Total bytes
    """
    _transfer_status(sent, size, 'downloaded')


def put_origin_database_dump(origin_path):
    """
    Uploading the origin database dump file
    :param origin_path: String
    :return:
    """
    if mode.get_sync_mode() == mode.SyncMode.PROXY:
        _subject = output.Subject.LOCAL
    else:
        _subject = output.Subject.ORIGIN

    output.message(
        _subject,
        'Uploading database dump',
        True
    )
    helper.check_and_create_dump_dir(mode.Client.TARGET, helper.get_dump_dir(mode.Client.TARGET))

    if not system.config['dry_run']:
        _localpath = origin_path + database_utility.database_dump_file_name + '.tar.gz'
        _remotepath = helper.get_dump_dir(mode.Client.TARGET) + '/'

        if system.config['use_rsync']:
            rsync.run_rsync_command(
                remote_client=mode.Client.TARGET,
                origin_path=_localpath,
                target_path=_remotepath,
                target_ssh=system.config[mode.Client.TARGET]['user'] + '@' + system.config[mode.Client.TARGET]['host']
            )
        else:
            #
            # Download speed problems
            # https://github.com/paramiko/paramiko/issues/60
            #
            sftp = get_sftp_client(client.ssh_client_target)
            sftp.put(origin_path + database_utility.database_dump_file_name + '.tar.gz',
                     helper.get_dump_dir(mode.Client.TARGET) + database_utility.database_dump_file_name + '.tar.gz',
                     upload_status)
            sftp.close()
            if not system.config['mute']:
                print('')



def upload_status(sent, size):
    """
    Callback for SFTP upload progress.

    :param sent: Bytes transferred
    :param size: Total bytes
    """
    _transfer_status(sent, size, 'uploaded')


def get_sftp_client(ssh_client):
    """

    :param ssh_client:
    :return:
    """
    sftp = ssh_client.open_sftp()
    sftp.get_channel().settimeout(client.default_timeout)
    return sftp

