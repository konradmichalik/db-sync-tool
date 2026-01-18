#!/usr/bin/env python3

"""
Mode script
"""

import subprocess

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
        cfg = system.get_typed_config()
        both_local = not cfg.origin.is_remote and not cfg.target.is_remote
        return both_local and SyncMode.is_same_host() and not SyncMode.is_sync_local()

    @staticmethod
    def is_dump_remote() -> bool:
        cfg = system.get_typed_config()
        both_remote = cfg.origin.is_remote and cfg.target.is_remote
        return both_remote and SyncMode.is_same_host() and not SyncMode.is_sync_remote()

    @staticmethod
    def is_receiver() -> bool:
        cfg = system.get_typed_config()
        return cfg.origin.is_remote and not SyncMode.is_proxy() and not SyncMode.is_sync_remote()

    @staticmethod
    def is_sender() -> bool:
        cfg = system.get_typed_config()
        return cfg.target.is_remote and not SyncMode.is_proxy() and not SyncMode.is_sync_remote()

    @staticmethod
    def is_proxy() -> bool:
        cfg = system.get_typed_config()
        return cfg.origin.is_remote and cfg.target.is_remote

    @staticmethod
    def is_import_local() -> bool:
        cfg = system.get_typed_config()
        return cfg.import_file != '' and not cfg.target.is_remote

    @staticmethod
    def is_import_remote() -> bool:
        cfg = system.get_typed_config()
        return cfg.import_file != '' and cfg.target.is_remote

    @staticmethod
    def is_sync_local() -> bool:
        cfg = system.get_typed_config()
        return (not cfg.origin.is_remote and not cfg.target.is_remote and
                SyncMode.is_same_host() and SyncMode.is_same_sync())

    @staticmethod
    def is_sync_remote() -> bool:
        cfg = system.get_typed_config()
        return (cfg.origin.is_remote and cfg.target.is_remote and
                SyncMode.is_same_host() and SyncMode.is_same_sync())

    @staticmethod
    def is_same_sync() -> bool:
        cfg = system.get_typed_config()
        # Different paths on same host
        if cfg.origin.path and cfg.target.path and cfg.origin.path != cfg.target.path:
            return True
        # Different databases on same host
        if cfg.origin.db.name and cfg.target.db.name:
            if (cfg.origin.db.name, cfg.origin.db.host) != (cfg.target.db.name, cfg.target.db.host):
                return True
        return False

    @staticmethod
    def is_same_host() -> bool:
        cfg = system.get_typed_config()
        return (cfg.origin.host == cfg.target.host and
                cfg.origin.port == cfg.target.port and
                cfg.origin.user == cfg.target.user)


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

