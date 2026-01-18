#!/usr/bin/env python3

"""
Helper script
"""

import shutil
import os
from db_sync_tool.utility import mode, system, output
from db_sync_tool.utility.security import quote_shell_arg  # noqa: F401 (re-export)
from db_sync_tool.utility.pure import (  # noqa: F401 (re-export)
    parse_version, get_file_from_path, remove_surrounding_quotes,
    clean_db_config, dict_to_args, remove_multiple_elements_from_string
)
from db_sync_tool.remote import utility as remote_utility


def clean_up() -> None:
    """
    Clean up temporary files and resources
    """
    # Note: MySQL config files are cleaned up in sync.py's finally block
    # to ensure cleanup even on errors
    cfg = system.get_typed_config()

    # Skip database cleanup for files-only mode or import mode
    if not mode.is_import() and not cfg.files_only:
        remote_utility.remove_target_database_dump()
        if mode.get_sync_mode() == mode.SyncMode.PROXY:
            remove_temporary_data_dir()


def remove_temporary_data_dir() -> None:
    """
    Remove temporary data directory for storing database dump files
    """
    if os.path.exists(system.default_local_sync_path):
        output.message(
            output.Subject.LOCAL,
            'Cleaning up',
            True
        )
        shutil.rmtree(system.default_local_sync_path)


def clean_up_dump_dir(client: str, path: str, num: int = 5) -> None:
    """
    Clean up the dump directory from old dump files (only affect .sql and .gz files)
    :param client: Client identifier
    :param path: Path to dump directory
    :param num: Number of files to keep
    """
    # Distinguish stat command on os system (Darwin|Linux)
    if check_os(client).strip() == 'Darwin':
        _command = get_command(client, 'stat') + ' -f "%Sm %N" ' + path + ' | ' + get_command(
            client,
            'sort') + ' -rn | ' + get_command(
            client, 'grep') + ' -E "\\.gz$|\\.sql$"'
    else:
        _command = get_command(client, 'stat') + ' -c "%y %n" ' + path + ' | ' + \
                   get_command(client,'sort') + ' -rn | ' + get_command(client, 'grep') + \
                   ' -E "\\.gz$|\\.sql$"'

    # List files in directory sorted by change date
    _result = mode.run_command(
        _command,
        client,
        True
    )
    _files = _result.splitlines() if _result else []

    for i in range(len(_files)):
        _filename = _files[i].rsplit(' ', 1)[-1]

        # Remove oldest files chosen by keep_dumps count
        if not i < num:
            mode.run_command(
                'rm ' + _filename,
                client
            )


def check_os(client: str) -> str:
    """
    Check which system is running (Linux|Darwin)
    :param client: Client identifier
    :return: OS name
    """
    result = mode.run_command(
        get_command(client, 'uname') + ' -s',
        client,
        True
    )
    return result if result else ''


def get_command(client: str, command: str) -> str:
    """
    Get command helper for overriding default commands on the given client
    :param client: Client identifier
    :param command: Command name
    :return: String command
    """
    cfg = system.get_typed_config()
    client_cfg = cfg.get_client(client)
    if command in client_cfg.console:
        return client_cfg.console[command]
    return command


def get_dump_dir(client: str) -> str:
    """
    Get database dump directory by client
    :param client: Client identifier
    :return: String path
    """
    cfg = system.get_typed_config()
    # Check if using default dump dir
    if client == 'origin':
        use_default = cfg.default_origin_dump_dir
    else:
        use_default = cfg.default_target_dump_dir

    if use_default:
        return '/tmp/'
    else:
        return cfg.get_client(client).dump_dir


def check_and_create_dump_dir(client: str, path: str) -> None:
    """
    Check if a path exists on the client system and creates the given path if necessary
    :param client: Client identifier
    :param path: Path to check/create
    """
    _safe_path = quote_shell_arg(path)
    mode.run_command(
        '[ ! -d ' + _safe_path + ' ] && mkdir -p ' + _safe_path,
        client
    )


def get_ssh_host_name(client: str, with_user: bool = False, minimal: bool = False) -> str:
    """
    Format ssh host name depending on existing client name
    :param client: Client identifier
    :param with_user: Include username in output
    :param minimal: Return minimal format
    :return: Formatted host name
    """
    cfg = system.get_typed_config()
    client_cfg = cfg.get_client(client)

    if not client_cfg.user and not client_cfg.host:
        return ''

    if with_user:
        _host = client_cfg.user + '@' + client_cfg.host
    else:
        _host = client_cfg.host

    if client_cfg.name:
        if minimal:
            return client_cfg.name
        else:
            return (output.CliFormat.BOLD + client_cfg.name +
                    output.CliFormat.ENDC + output.CliFormat.BLACK +
                    ' (' + _host + ')' + output.CliFormat.ENDC)
    else:
        return _host


def create_local_temporary_data_dir() -> None:
    """
    Create local temporary data dir with secure permissions
    """
    cfg = system.get_typed_config()
    # Skip secure permissions for user-specified keep_dump directories
    if cfg.keep_dump:
        if not os.path.exists(system.default_local_sync_path):
            os.makedirs(system.default_local_sync_path)
    else:
        # Use secure temp dir creation with 0700 permissions
        system.create_secure_temp_dir(system.default_local_sync_path)


def check_file_exists(client: str, path: str) -> bool:
    """
    Check if a file exists
    :param client: Client identifier
    :param path: File path
    :return: Boolean
    """
    _safe_path = quote_shell_arg(path)
    return mode.run_command(f'[ -f {_safe_path} ] && echo "1"', client, True) == '1'


def run_script(client: str | None = None, script: str = 'before') -> None:
    """
    Executing script command
    :param client: Client identifier (or None for global scripts)
    :param script: Script name ('before', 'after', 'error')
    """
    cfg = system.get_typed_config()

    if client is None:
        # Global scripts
        scripts_dict = cfg.scripts
        _subject = output.Subject.LOCAL
        client = mode.Client.LOCAL
    else:
        # Client-specific scripts
        client_cfg = cfg.get_client(client)
        scripts_dict = client_cfg.scripts
        _subject = output.host_to_subject(client)

    if script in scripts_dict:
        output.message(
            _subject,
            f'Running script {client}',
            True
        )
        mode.run_command(
            scripts_dict[script],
            client
        )


def _check_tool_version(tool: str, version_flag: str = '--version') -> str | None:
    """
    Check if a tool is available and return its version.
    DRY helper for version checks.

    :param tool: Tool name
    :param version_flag: Flag to get version
    :return: Version string or None
    """
    raw_version = mode.run_command(
        f'{tool} {version_flag}',
        mode.Client.LOCAL,
        force_output=True,
        allow_fail=True
    )
    return parse_version(raw_version)


def check_rsync_version() -> bool:
    """
    Check rsync version and availability.

    :return: True if rsync is available, False otherwise
    """
    version = _check_tool_version('rsync')
    if version:
        output.message(output.Subject.LOCAL, f'rsync version {version}')
        return True
    return False


def check_sshpass_version() -> bool | None:
    """
    Check sshpass version
    :return: True if available, None otherwise
    """
    version = _check_tool_version('sshpass', '-V')
    if version:
        output.message(output.Subject.LOCAL, f'sshpass version {version}')
        system.set_use_sshpass(True)
        return True
    return None


def confirm(prompt: str | None = None, resp: bool = False) -> bool:
    """
    https://code.activestate.com/recipes/541096-prompt-the-user-for-confirmation/

    prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    >>> confirm(prompt='Create Directory?', resp=True)
    Create Directory? [Y|n]:
    True
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [y|N]:
    False

    """

    if prompt is None:
        prompt = 'Confirm'

    if resp:
        prompt = f'{prompt} [Y|n]: '
    else:
        prompt = f'{prompt} [y|N]: '

    while True:
        ans = input(prompt).lower()
        if not ans:
            return resp
        if ans in ('y', 'n'):
            return ans == 'y'
        print('Please enter y or n.')


def run_sed_command(client: str, command: str) -> str:
    """
    Executes a sed command on the specified client, trying -E first and falling back to -r if -E fails.

    :param client: The client on which the sed command should be executed.
    :param command: The sed command to execute (excluding the sed options).
    :return: The result of the sed command as a cleaned string (with newlines removed).
    """
    # Check if the client supports -E or -r option for sed
    option = mode.run_command(
         f"echo | {get_command(client, 'sed')} -E '' >/dev/null 2>&1 && echo -E || (echo | {get_command(client, 'sed')} -r '' >/dev/null 2>&1 && echo -r)",
         client,
         True
    )
    # If neither option is supported, default to -E
    if not option:
        option = '-E'

    result = mode.run_command(
        f"{get_command(client, 'sed')} -n {option} {command}",
        client,
        True
    )
    return result.strip().replace('\n', '') if result else ''
