#!/usr/bin/env python3

"""
Mode script
"""

import subprocess
from typing import Any

from db_sync_tool.utility import system, output, helper
from db_sync_tool.utility.exceptions import DbSyncError
from db_sync_tool.utility.security import sanitize_command_for_logging  # noqa: F401 (re-export)
from db_sync_tool.remote import system as remote_system


#
# GLOBALS
#

class Client:
    ORIGIN = 'origin'
    TARGET = 'target'
    LOCAL = 'local'


def _get_client_attr(client: str, key: str) -> Any:
    """
    Get a configuration attribute value for comparison.
    Helper for SyncMode configuration checks.

    :param client: Client identifier ('origin' or 'target')
    :param key: Attribute key
    :return: Attribute value
    """
    cfg = system.get_typed_config()
    client_cfg = cfg.get_client(client)
    if key == 'db':
        # For db comparison, return a tuple of identifying values
        return (client_cfg.db.name, client_cfg.db.host, client_cfg.db.user)
    return getattr(client_cfg, key, '')


def _has_client_attr(client: str, key: str) -> bool:
    """
    Check if a configuration attribute has a non-empty value.
    Helper for SyncMode configuration checks.

    :param client: Client identifier ('origin' or 'target')
    :param key: Attribute key
    :return: True if attribute has a value
    """
    value = _get_client_attr(client, key)
    if key == 'db':
        # db is "available" if name is set
        return value[0] != ''
    return value != '' and value is not None


class SyncMode:
    """
    Sync Mode
    """

    DUMP_LOCAL = 'DUMP_LOCAL'
    DUMP_REMOTE = 'DUMP_REMOTE'
    IMPORT_LOCAL = 'IMPORT_LOCAL'
    IMPORT_REMOTE = 'IMPORT_REMOTE'
    RECEIVER = 'RECEIVER'
    SENDER = 'SENDER'
    PROXY = 'PROXY'
    SYNC_REMOTE = 'SYNC_REMOTE'
    SYNC_LOCAL = 'SYNC_LOCAL'

    @staticmethod
    def is_dump_local() -> bool:
        return SyncMode.is_full_local() and SyncMode.is_same_host() and not SyncMode.is_sync_local()

    @staticmethod
    def is_dump_remote() -> bool:
        return SyncMode.is_full_remote() and SyncMode.is_same_host() and \
               not SyncMode.is_sync_remote()

    @staticmethod
    def is_receiver() -> bool:
        return _has_client_attr(Client.ORIGIN, 'host') and not SyncMode.is_proxy() and \
               not SyncMode.is_sync_remote()

    @staticmethod
    def is_sender() -> bool:
        return _has_client_attr(Client.TARGET, 'host') and not SyncMode.is_proxy() and \
               not SyncMode.is_sync_remote()

    @staticmethod
    def is_proxy() -> bool:
        return SyncMode.is_full_remote()

    @staticmethod
    def is_import_local() -> bool:
        cfg = system.get_typed_config()
        return cfg.import_file != '' and not _has_client_attr(Client.TARGET, 'host')

    @staticmethod
    def is_import_remote() -> bool:
        cfg = system.get_typed_config()
        return cfg.import_file != '' and _has_client_attr(Client.TARGET, 'host')

    @staticmethod
    def is_sync_local() -> bool:
        return SyncMode.is_full_local() and SyncMode.is_same_host() and SyncMode.is_same_sync()

    @staticmethod
    def is_sync_remote() -> bool:
        return SyncMode.is_full_remote() and SyncMode.is_same_host() and SyncMode.is_same_sync()

    @staticmethod
    def is_same_sync() -> bool:
        return ((SyncMode.is_available_configuration('path') and
                 not SyncMode.is_same_configuration('path')) or
               (SyncMode.is_available_configuration('db') and
                not SyncMode.is_same_configuration('db')))

    @staticmethod
    def is_full_remote() -> bool:
        return SyncMode.is_available_configuration('host')

    @staticmethod
    def is_full_local() -> bool:
        return SyncMode.is_unavailable_configuration('host')

    @staticmethod
    def is_same_host() -> bool:
        return SyncMode.is_same_configuration('host') and SyncMode.is_same_configuration('port') and SyncMode.is_same_configuration('user')

    @staticmethod
    def is_available_configuration(key: str) -> bool:
        return _has_client_attr(Client.ORIGIN, key) and _has_client_attr(Client.TARGET, key)

    @staticmethod
    def is_unavailable_configuration(key: str) -> bool:
        return not _has_client_attr(Client.ORIGIN, key) and not _has_client_attr(Client.TARGET, key)

    @staticmethod
    def is_same_configuration(key: str) -> bool:
        return (SyncMode.is_available_configuration(key) and
               _get_client_attr(Client.ORIGIN, key) == _get_client_attr(Client.TARGET, key)) or \
               SyncMode.is_unavailable_configuration(key)


# Default sync mode
sync_mode = SyncMode.RECEIVER


#
# FUNCTIONS
#
def get_sync_mode() -> str:
    """
    Returning the sync mode
    :return: String sync_mode
    """
    return sync_mode


def check_sync_mode() -> None:
    """
    Checking the sync_mode based on the given configuration
    """
    global sync_mode
    _description = ''

    _modes = {
        SyncMode.RECEIVER: '(REMOTE ➔ LOCAL)',
        SyncMode.SENDER: '(LOCAL ➔ REMOTE)',
        SyncMode.PROXY: '(REMOTE ➔ LOCAL ➔ REMOTE)',
        SyncMode.DUMP_LOCAL: '(LOCAL, ONLY EXPORT)',
        SyncMode.DUMP_REMOTE: '(REMOTE, ONLY EXPORT)',
        SyncMode.IMPORT_LOCAL: '(REMOTE, ONLY IMPORT)',
        SyncMode.IMPORT_REMOTE: '(LOCAL, ONLY IMPORT)',
        SyncMode.SYNC_LOCAL: '(LOCAL ➔ LOCAL)',
        SyncMode.SYNC_REMOTE: '(REMOTE ➔ REMOTE)'
    }

    for _mode, _desc in _modes.items():
        if getattr(SyncMode, 'is_' + _mode.lower())():
            sync_mode = _mode
            _description = _desc

    cfg = system.get_typed_config()
    if is_import():
        output.message(
            output.Subject.INFO,
            f'Import file {output.CliFormat.BLACK}{cfg.import_file}{output.CliFormat.ENDC}',
            True
        )

    system.set_is_same_client(SyncMode.is_same_host())

    output.message(
        output.Subject.INFO,
        f'Sync mode: {sync_mode} {output.CliFormat.BLACK}{_description}{output.CliFormat.ENDC}',
        True
    )

    check_for_protection()


def is_remote(client: str) -> bool:
    """
    Check if given client is remote client
    :param client: Client identifier
    :return: Boolean
    """
    return {
        Client.ORIGIN: is_origin_remote,
        Client.TARGET: is_target_remote,
    }.get(client, lambda: False)()


def is_target_remote() -> bool:
    """
    Check if target is remote client
    :return: Boolean
    """
    return sync_mode in (SyncMode.SENDER, SyncMode.PROXY, SyncMode.DUMP_REMOTE,
                         SyncMode.IMPORT_REMOTE, SyncMode.SYNC_REMOTE)


def is_origin_remote() -> bool:
    """
    Check if origin is remote client
    :return: Boolean
    """
    return sync_mode in (SyncMode.RECEIVER, SyncMode.PROXY, SyncMode.DUMP_REMOTE,
                         SyncMode.IMPORT_REMOTE, SyncMode.SYNC_REMOTE)


def is_import() -> bool:
    """
    Check if sync mode is import
    :return: Boolean
    """
    return sync_mode in (SyncMode.IMPORT_LOCAL, SyncMode.IMPORT_REMOTE)


def is_dump() -> bool:
    """
    Check if sync mode is dump
    :return: Boolean
    """
    return sync_mode in (SyncMode.DUMP_LOCAL, SyncMode.DUMP_REMOTE)


def run_command(command: str, client: str, force_output: bool = False,
                allow_fail: bool = False, skip_dry_run: bool = False) -> str | None:
    """
    Run command depending on the given client
    :param command: String
    :param client: String
    :param force_output: Boolean
    :param allow_fail: Boolean
    :param skip_dry_run: Boolean
    :return: Command output or None
    """
    cfg = system.get_typed_config()
    if cfg.verbose:
        # Sanitize command to prevent credentials from appearing in logs
        _safe_command = sanitize_command_for_logging(command)
        output.message(
            output.host_to_subject(client),
            output.CliFormat.BLACK + _safe_command + output.CliFormat.ENDC,
            debug=True
        )

    if cfg.dry_run and skip_dry_run:
        return None

    if is_remote(client):
        if force_output:
            return ''.join(remote_system.run_ssh_command_by_client(client, command).readlines()).strip()
        else:
            return remote_system.run_ssh_command_by_client(client, command)
    else:
        res = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        # Wait for the process end and print error in case of failure
        out, err = res.communicate()

        if res.wait() != 0 and err.decode() != '' and not allow_fail:
            helper.run_script(script='error')
            raise DbSyncError(err.decode())

        if force_output:
            return out.decode().strip()

        return None


def check_for_protection() -> None:
    """
    Check if the target system is protected and exit if so.
    """
    cfg = system.get_typed_config()
    if sync_mode in (SyncMode.RECEIVER, SyncMode.SENDER, SyncMode.PROXY, SyncMode.SYNC_LOCAL,
                     SyncMode.SYNC_REMOTE, SyncMode.IMPORT_LOCAL, SyncMode.IMPORT_REMOTE) and \
            cfg.target.protect:
        _host = helper.get_ssh_host_name(Client.TARGET)
        raise DbSyncError(
            f'The host {_host} is protected against the import of a database dump. '
            'Please check synchronisation target or adjust the host configuration.'
        )

