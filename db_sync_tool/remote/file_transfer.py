#!/usr/bin/env python3

"""
File transfer module using rsync.

Provides file synchronization functionality integrated with db-sync-tool's
existing infrastructure for SSH authentication and rsync handling.
"""

import shutil
from pathlib import Path

from db_sync_tool.utility import mode, system, output, helper
from db_sync_tool.utility.config import FileTransferConfig
from db_sync_tool.remote import rsync

# Temporary directory for PROXY mode file transfers
_temp_file_dir: str | None = None


def transfer_files() -> None:
    """
    Transfer configured files between clients.

    Iterates through the files configuration and synchronizes each
    origin/target pair using rsync.
    """
    cfg = system.get_typed_config()

    # Check if file transfer is enabled
    if not cfg.with_files and not cfg.files_only:
        return

    # Skip if no files configured
    if not cfg.files:
        output.message(
            output.Subject.WARNING,
            'File transfer enabled but no files configured',
            True
        )
        return

    # Skip file transfer for dump/import modes
    if mode.is_dump() or mode.is_import():
        output.message(
            output.Subject.WARNING,
            'File transfer not available in dump/import mode',
            True
        )
        return

    output.message(
        output.Subject.INFO,
        f'Starting file transfer ({len(cfg.files)} configured)',
        True
    )

    for i, file_config in enumerate(cfg.files, 1):
        output.message(
            output.Subject.INFO,
            f'[{i}/{len(cfg.files)}] {file_config.origin} -> {file_config.target}',
            True
        )
        _transfer_single(file_config)

    output.message(
        output.Subject.INFO,
        'File transfer completed',
        True
    )


def _transfer_single(file_config: FileTransferConfig) -> None:
    """
    Transfer a single file configuration entry.

    :param file_config: FileTransferConfig instance
    """
    cfg = system.get_typed_config()

    origin_path = _resolve_path(file_config.origin, mode.Client.ORIGIN)
    target_path = _resolve_path(file_config.target, mode.Client.TARGET)

    if cfg.dry_run:
        output.message(
            output.Subject.INFO,
            f'[DRY RUN] Would sync {origin_path} -> {target_path}',
            True
        )
        return

    sync_mode_val = mode.get_sync_mode()

    if sync_mode_val == mode.SyncMode.PROXY:
        _transfer_proxy(origin_path, target_path, file_config)
    elif sync_mode_val == mode.SyncMode.SYNC_REMOTE:
        _transfer_remote_to_remote(origin_path, target_path, file_config)
    else:
        _transfer_standard(origin_path, target_path, file_config)


def _resolve_path(path: str, client: str) -> str:
    """
    Resolve file path, making relative paths absolute.

    :param path: Path (relative or absolute)
    :param client: Client identifier (origin/target)
    :return: Resolved absolute path
    """
    if path.startswith('/'):
        return path

    base_path = system.get_typed_config().get_client(client).path
    if not base_path:
        return path

    # Preserve trailing slash for rsync (important for directory sync behavior)
    resolved = str(Path(base_path).parent / path)
    if path.endswith('/') and not resolved.endswith('/'):
        resolved += '/'
    return resolved


def _get_excludes(excludes: list[str]) -> str:
    """
    Build rsync exclude arguments.

    :param excludes: List of patterns to exclude
    :return: String with --exclude flags
    """
    if not excludes:
        return ''
    return ' '.join(f'--exclude={helper.quote_shell_arg(e)}' for e in excludes)


def _get_file_options(file_config: FileTransferConfig) -> str:
    """
    Get rsync options for file transfer.

    :param file_config: FileTransferConfig instance
    :return: Combined options string
    """
    cfg = system.get_typed_config()
    base_options = rsync.get_options()

    # Add global file options
    if cfg.files_options:
        base_options += f' {cfg.files_options}'

    # Add per-transfer options
    if file_config.options:
        base_options += f' {file_config.options}'

    return base_options


def _transfer_standard(origin_path: str, target_path: str,
                       file_config: FileTransferConfig) -> None:
    """
    Standard file transfer (RECEIVER, SENDER, SYNC_LOCAL modes).

    :param origin_path: Source path
    :param target_path: Destination path
    :param file_config: FileTransferConfig instance
    """
    # Determine which client is remote
    if mode.is_origin_remote():
        remote_client = mode.Client.ORIGIN
    elif mode.is_target_remote():
        remote_client = mode.Client.TARGET
    else:
        remote_client = None

    _run_rsync(
        remote_client=remote_client,
        origin_path=origin_path,
        target_path=target_path,
        file_config=file_config
    )


def _transfer_proxy(origin_path: str, target_path: str,
                    file_config: FileTransferConfig) -> None:
    """
    Proxy mode file transfer (remote -> local -> remote).

    :param origin_path: Source path
    :param target_path: Destination path
    :param file_config: FileTransferConfig instance
    """
    global _temp_file_dir

    # Create local temp directory
    _temp_file_dir = system.default_local_sync_path + 'files/'
    helper.check_and_create_dump_dir(mode.Client.LOCAL, _temp_file_dir)

    output.message(
        output.Subject.INFO,
        'Proxy mode: origin -> local',
        True
    )

    # Step 1: Origin -> Local
    _run_rsync(
        remote_client=mode.Client.ORIGIN,
        origin_path=origin_path,
        target_path=_temp_file_dir,
        file_config=file_config
    )

    output.message(
        output.Subject.INFO,
        'Proxy mode: local -> target',
        True
    )

    # Step 2: Local -> Target
    _run_rsync(
        remote_client=mode.Client.TARGET,
        origin_path=_temp_file_dir,
        target_path=target_path,
        file_config=file_config
    )


def _transfer_remote_to_remote(origin_path: str, target_path: str,
                                file_config: FileTransferConfig) -> None:
    """
    Remote-to-remote file transfer (SYNC_REMOTE mode).

    Executes rsync on origin to sync directly to target.

    :param origin_path: Source path
    :param target_path: Destination path
    :param file_config: FileTransferConfig instance
    """
    cfg = system.get_typed_config()

    # Build rsync command to run on origin
    excludes = _get_excludes(file_config.exclude)
    options = _get_file_options(file_config)
    password_env = rsync.get_password_environment(mode.Client.TARGET)
    auth = rsync.get_authorization(mode.Client.TARGET)
    target_host = f'{cfg.target.user}@{cfg.target.host}:'

    command = (
        f'{password_env}rsync {options} {auth} '
        f'{excludes} {origin_path} {target_host}{target_path}'
    ).strip()

    # Clean up multiple spaces
    command = ' '.join(command.split())

    mode.run_command(command, mode.Client.ORIGIN, True)


def _run_rsync(remote_client: str | None, origin_path: str, target_path: str,
               file_config: FileTransferConfig) -> None:
    """
    Execute rsync command for file transfer.

    :param remote_client: Client identifier for SSH authentication (or None for local)
    :param origin_path: Source path
    :param target_path: Destination path
    :param file_config: FileTransferConfig instance
    """
    excludes = _get_excludes(file_config.exclude)
    options = _get_file_options(file_config)

    # Build origin and target host prefixes
    if remote_client == mode.Client.ORIGIN:
        origin_host = rsync.get_host(mode.Client.ORIGIN)
        target_host = ''
    elif remote_client == mode.Client.TARGET:
        origin_host = ''
        target_host = rsync.get_host(mode.Client.TARGET)
    else:
        origin_host = ''
        target_host = ''

    # Build the rsync command
    password_env = rsync.get_password_environment(remote_client) if remote_client else ''
    auth = rsync.get_authorization(remote_client) if remote_client else ''

    command = (
        f'{password_env}rsync {options} {auth} {excludes} '
        f'{origin_host}{origin_path} {target_host}{target_path}'
    ).strip()

    # Clean up multiple spaces
    command = ' '.join(command.split())

    output_str = mode.run_command(command, mode.Client.LOCAL, True)
    if output_str:
        rsync.read_stats(output_str)


def cleanup() -> None:
    """Clean up temporary file transfer directory."""
    global _temp_file_dir
    if _temp_file_dir and Path(_temp_file_dir).exists():
        shutil.rmtree(_temp_file_dir, ignore_errors=True)
        _temp_file_dir = None
