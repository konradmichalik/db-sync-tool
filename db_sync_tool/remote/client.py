#!/usr/bin/env python3

"""
SSH client management for remote connections.

Provides both legacy global access and modern context manager patterns:

Legacy (backwards compatible):
    from db_sync_tool.remote import client
    client.load_ssh_client_origin()
    # use client.ssh_client_origin
    client.close_ssh_clients()

Modern (recommended):
    from db_sync_tool.remote.client import SSHClientManager
    with SSHClientManager() as mgr:
        mgr.load_origin()
        # use mgr.origin
"""

import sys
import warnings
import paramiko
from db_sync_tool.utility import mode, system, helper, output

# Suppress paramiko warnings about unknown host keys
warnings.filterwarnings("ignore", message="Unknown.*host key", module="paramiko")

default_timeout = 600


class SSHClientManager:
    """
    Manages SSH client connections with automatic cleanup.

    Can be used as a context manager for guaranteed resource cleanup,
    or instantiated directly for more control.
    """

    _instance: 'SSHClientManager | None' = None

    def __init__(self):
        self._origin: paramiko.SSHClient | None = None
        self._target: paramiko.SSHClient | None = None
        self._additional: list[paramiko.SSHClient] = []

    @classmethod
    def get_instance(cls) -> 'SSHClientManager':
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def origin(self) -> paramiko.SSHClient | None:
        """Get origin SSH client."""
        return self._origin

    @property
    def target(self) -> paramiko.SSHClient | None:
        """Get target SSH client."""
        return self._target

    def _update_legacy_globals(self) -> None:
        """Sync internal state to legacy global variables."""
        global ssh_client_origin, ssh_client_target, additional_ssh_clients
        ssh_client_origin = self._origin
        ssh_client_target = self._target
        additional_ssh_clients = list(self._additional)

    def load_origin(self) -> paramiko.SSHClient:
        """Load and return the origin SSH client."""
        self._origin = load_ssh_client(mode.Client.ORIGIN)
        self._update_legacy_globals()
        helper.run_script(mode.Client.ORIGIN, 'before')
        return self._origin

    def load_target(self) -> paramiko.SSHClient:
        """Load and return the target SSH client."""
        self._target = load_ssh_client(mode.Client.TARGET)
        self._update_legacy_globals()
        helper.run_script(mode.Client.TARGET, 'before')
        return self._target

    def add_additional(self, client: paramiko.SSHClient) -> None:
        """Register an additional SSH client for cleanup."""
        self._additional.append(client)
        self._update_legacy_globals()

    def close_all(self) -> None:
        """
        Close all managed SSH connections.

        Uses exception handling to ensure all cleanup steps complete,
        even if individual steps fail. This is important since close_all()
        is called from __exit__.
        """
        errors = []

        # Origin cleanup
        try:
            helper.run_script(mode.Client.ORIGIN, 'after')
        except Exception as e:
            errors.append(f"origin after-script: {e}")
        try:
            if self._origin is not None:
                self._origin.close()
        except Exception as e:
            errors.append(f"origin close: {e}")
        finally:
            self._origin = None

        # Target cleanup
        try:
            helper.run_script(mode.Client.TARGET, 'after')
        except Exception as e:
            errors.append(f"target after-script: {e}")
        try:
            if self._target is not None:
                self._target.close()
        except Exception as e:
            errors.append(f"target close: {e}")
        finally:
            self._target = None

        # Additional clients cleanup
        for i, client in enumerate(self._additional):
            try:
                client.close()
            except Exception as e:
                errors.append(f"additional client {i}: {e}")
        self._additional.clear()

        # Global after-script
        try:
            helper.run_script(script='after')
        except Exception as e:
            errors.append(f"global after-script: {e}")

        # Always sync globals
        self._update_legacy_globals()

        # Log errors if any occurred (but don't raise - cleanup should be silent)
        if errors:
            for err in errors:
                output.message(output.Subject.WARNING, f"Cleanup error: {err}", verbose_only=True)

    def __enter__(self) -> 'SSHClientManager':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - ensures cleanup even on errors."""
        self.close_all()


# Legacy global variables for backwards compatibility
ssh_client_origin: paramiko.SSHClient | None = None
ssh_client_target: paramiko.SSHClient | None = None
additional_ssh_clients: list[paramiko.SSHClient] = []


def load_ssh_client_origin():
    """
    Loading the origin ssh client (legacy function).

    Prefer using SSHClientManager for new code.
    """
    SSHClientManager.get_instance().load_origin()


def load_ssh_client_target():
    """
    Loading the target ssh client (legacy function).

    Prefer using SSHClientManager for new code.
    """
    SSHClientManager.get_instance().load_target()


def load_ssh_client(ssh):
    """
    Initializing the given ssh client
    :param ssh: String
    :return:
    """
    _host_name = helper.get_ssh_host_name(ssh, True)
    _ssh_client = paramiko.SSHClient()
    # Load known hosts from system for security (prevents MITM attacks)
    _ssh_client.load_system_host_keys()
    # Log warning for unknown hosts but still accept connection (convenience over strict security)
    # Note: This does NOT prevent MITM - use RejectPolicy() for strict host verification
    _ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy())

    _ssh_port = system.config[ssh]['port'] if 'port' in system.config[ssh] else 22
    _ssh_key = None
    _ssh_password = None

    # Check authentication
    if 'ssh_key' in system.config[ssh]:
        _authentication_method = f'{output.CliFormat.BLACK} - ' \
                                 f'(authentication: key){output.CliFormat.ENDC}'
        _ssh_key = system.config[ssh]['ssh_key']
    elif 'password' in system.config[ssh]:
        _authentication_method = f'{output.CliFormat.BLACK} - ' \
                                 f'(authentication: password){output.CliFormat.ENDC}'
        _ssh_password = system.config[ssh]['password']
    elif 'ssh_agent' in system.config:
        _authentication_method = f'{output.CliFormat.BLACK} - ' \
                                 f'(authentication: key){output.CliFormat.ENDC}'
    else:
        sys.exit(
            output.message(
                output.Subject.ERROR,
                'Missing SSH authentication. Neither ssh key nor ssh password given.',
                False
            )
        )

    # Try to connect to remote client via paramiko
    try:
        _ssh_client.connect(hostname=system.config[ssh]['host'],
                            username=system.config[ssh]['user'],
                            key_filename=_ssh_key,
                            password=_ssh_password,
                            port=_ssh_port,
                            compress=True,
                            timeout=default_timeout,
                            sock=get_jump_host_channel(ssh))
        #
        # Workaround for long-lasting requests
        # https://stackoverflow.com/questions/50009688/python-paramiko-ssh-session-not-active-after-being-idle-for-many-hours
        #
        _ssh_client.get_transport().set_keepalive(60)

    except paramiko.ssh_exception.AuthenticationException:
        sys.exit(
            output.message(
                output.Subject.ERROR,
                f'SSH authentication for {_host_name} failed',
                False
            )
        )

    output.message(
        output.host_to_subject(ssh),
        f'Initialize remote SSH connection {_host_name}{_authentication_method}',
        True
    )

    return _ssh_client


def close_ssh_clients():
    """
    Closing ssh client sessions (legacy function).

    Prefer using SSHClientManager as context manager for new code.
    """
    SSHClientManager.get_instance().close_all()


def get_jump_host_channel(client):
    """
    Provide an optional transport channel for a SSH jump host client
    https://gist.github.com/tintoy/443c42ea3865680cd624039c4bb46219
    :param client:
    :return:
    """
    _jump_host_channel = None
    if 'jump_host' in system.config[client]:
        # prepare jump host config
        _jump_host_client = paramiko.SSHClient()
        _jump_host_client.load_system_host_keys()
        _jump_host_client.set_missing_host_key_policy(paramiko.WarningPolicy())

        _jump_host_host = system.config[client]['jump_host']['host']
        _jump_host_user = system.config[client]['jump_host']['user'] if 'user' in system.config[client]['jump_host'] else system.config[client]['user']

        if 'ssh_key' in system.config[client]['jump_host']:
            _jump_host_ssh_key = system.config[client]['jump_host']['ssh_key']
        elif 'ssh_key' in system.config[client]:
            _jump_host_ssh_key = system.config[client]['ssh_key']
        else:
            _jump_host_ssh_key = None

        if 'port' in system.config[client]['jump_host']:
            _jump_host_port = system.config[client]['jump_host']['port']
        elif 'port' in system.config[client]:
            _jump_host_port = system.config[client]['port']
        else:
            _jump_host_port = 22

        # connect to the jump host
        _jump_host_client.connect(
            hostname=_jump_host_host,
            username=_jump_host_user,
            key_filename=_jump_host_ssh_key,
            password=system.config[client]['jump_host']['password'] if 'password' in system.config[client]['jump_host'] else None,
            port=_jump_host_port,
            compress=True,
            timeout=default_timeout
        )

        # Register for cleanup via manager (also updates legacy global)
        SSHClientManager.get_instance().add_additional(_jump_host_client)

        # open the necessary channel
        _jump_host_transport = _jump_host_client.get_transport()
        _jump_host_channel = _jump_host_transport.open_channel(
            'direct-tcpip',
            dest_addr=(system.config[client]['host'], 22),
            src_addr=(system.config[client]['jump_host']['private'] if 'private' in system.config[client]['jump_host'] else system.config[client]['jump_host']['host'], 22)
        )

        # print information
        _destination_client = helper.get_ssh_host_name(client, minimal=True)
        _jump_host_name = system.config[client]['jump_host']['name'] if 'name' in system.config[client]['jump_host'] else _jump_host_host
        output.message(
            output.host_to_subject(client),
            f'Initialize remote SSH jump host {output.CliFormat.BLACK}local ➔ {output.CliFormat.BOLD}{_jump_host_name}{output.CliFormat.ENDC}{output.CliFormat.BLACK} ➔ {_destination_client}{output.CliFormat.ENDC}',
            True
        )

    return _jump_host_channel

