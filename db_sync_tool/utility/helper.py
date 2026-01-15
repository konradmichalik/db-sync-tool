#!/usr/bin/env python3

"""
Helper script
"""

import shutil
import os
import re
import shlex
from db_sync_tool.utility import mode, system, output
from db_sync_tool.remote import utility as remote_utility


def quote_shell_arg(arg):
    """
    Safely quote a string for use as a shell argument.
    Prevents command injection by escaping special characters.

    :param arg: String to quote
    :return: Safely quoted string
    """
    if arg is None:
        return "''"
    return shlex.quote(str(arg))


def clean_up():
    """
    Clean up temporary files and resources
    :return:
    """
    # Import here to avoid circular imports
    from db_sync_tool.database import utility as database_utility

    # Clean up MySQL config files (security: remove credential files)
    database_utility.cleanup_mysql_config_files()

    if not mode.is_import():
        remote_utility.remove_target_database_dump()
        if mode.get_sync_mode() == mode.SyncMode.PROXY:
            remove_temporary_data_dir()


def remove_temporary_data_dir():
    """
    Remove temporary data directory for storing database dump files
    :return:
    """
    if os.path.exists(system.default_local_sync_path):
        output.message(
            output.Subject.LOCAL,
            'Cleaning up',
            True
        )
        shutil.rmtree(system.default_local_sync_path)


def clean_up_dump_dir(client, path, num=5):
    """
    Clean up the dump directory from old dump files (only affect .sql and .tar.gz files)
    :param client:
    :param path:
    :param num:
    :return:
    """
    # Distinguish stat command on os system (Darwin|Linux)
    if check_os(client).strip() == 'Darwin':
        _command = get_command(client, 'stat') + ' -f "%Sm %N" ' + path + ' | ' + get_command(
            client,
            'sort') + ' -rn | ' + get_command(
            client, 'grep') + ' -E ".tar.gz|.sql"'
    else:
        _command = get_command(client, 'stat') + ' -c "%y %n" ' + path + ' | ' + \
                   get_command(client,'sort') + ' -rn | ' + get_command(client, 'grep') + \
                   ' -E ".tar.gz|.sql"'

    # List files in directory sorted by change date
    _files = mode.run_command(
        _command,
        client,
        True
    ).splitlines()

    for i in range(len(_files)):
        _filename = _files[i].rsplit(' ', 1)[-1]

        # Remove oldest files chosen by keep_dumps count
        if not i < num:
            mode.run_command(
                'rm ' + _filename,
                client
            )


def check_os(client):
    """
    Check which system is running (Linux|Darwin)
    :param client:
    :return:
    """
    return mode.run_command(
        get_command(client, 'uname') + ' -s',
        client,
        True
    )


def get_command(client, command):
    """
    Get command helper for overriding default commands on the given client
    :param client:
    :param command:
    :return: String command
    """
    if 'console' in system.config[client]:
        if command in system.config[client]['console']:
            return system.config[client]['console'][command]
    return command


def get_dump_dir(client):
    """
    Get database dump directory by client
    :param client:
    :return: String path
    """
    if system.config[f'default_{client}_dump_dir']:
        return '/tmp/'
    else:
        return system.config[client]['dump_dir']


def check_and_create_dump_dir(client, path):
    """
    Check if a path exists on the client system and creates the given path if necessary
    :param client:
    :param path:
    :return:
    """
    _safe_path = quote_shell_arg(path)
    mode.run_command(
        '[ ! -d ' + _safe_path + ' ] && mkdir -p ' + _safe_path,
        client
    )


def get_ssh_host_name(client, with_user=False, minimal=False):
    """
    Format ssh host name depending on existing client name
    :param client:
    :param with_user:
    :param short:
    :return:
    """
    if not 'user' in system.config[client] and not 'host' in system.config[client]:
        return ''

    if with_user:
        _host = system.config[client]['user'] + '@' + system.config[client]['host']
    else:
        _host = system.config[client]['host']

    if 'name' in system.config[client]:
        if minimal:
            return system.config[client]['name']
        else:
            return output.CliFormat.BOLD + system.config[client][
                'name'] + output.CliFormat.ENDC + output.CliFormat.BLACK + ' (' + _host + ')' + \
               output.CliFormat.ENDC
    else:
        return _host


def create_local_temporary_data_dir():
    """
    Create local temporary data dir
    :return:
    """
    # @ToDo: Combine with check_and_create_dump_dir()
    if not os.path.exists(system.default_local_sync_path):
        os.makedirs(system.default_local_sync_path)


def dict_to_args(dict):
    """
    Convert an dictionary to a args list
    :param dict: Dictionary
    :return: List
    """
    _args = []
    for key, val in dict.items():
        if isinstance(val, bool):
            if val:
                _args.append(f'--{key}')
        else:
            _args.append(f'--{key}')
            _args.append(str(val))
    if len(_args) == 0:
        return None
    return _args


def check_file_exists(client, path):
    """
    Check if a file exists
    :param client: String
    :param path: String file path
    :return: Boolean
    """
    _safe_path = quote_shell_arg(path)
    return mode.run_command(f'[ -f {_safe_path} ] && echo "1"', client, True) == '1'


def run_script(client=None, script='before'):
    """
    Executing script command
    :param client: String
    :param script: String
    :return:
    """
    if client is None:
        _config = system.config
        _subject = output.Subject.LOCAL
        client = mode.Client.LOCAL
    else:
        _config = system.config[client]
        _subject = output.host_to_subject(client)

    if not 'scripts' in _config:
        return

    if f'{script}' in _config['scripts']:
        output.message(
            _subject,
            f'Running script {client}',
            True
        )
        mode.run_command(
            _config['scripts'][script],
            client
        )


def check_rsync_version():
    """
    Check rsync version
    :return:
    """
    _raw_version = mode.run_command(
        'rsync --version',
        mode.Client.LOCAL,
        True
    )
    _version = parse_version(_raw_version)
    output.message(
        output.Subject.LOCAL,
        f'rsync version {_version}'
    )


def check_sshpass_version():
    """
    Check sshpass version
    :return:
    """
    _raw_version = mode.run_command(
        'sshpass -V',
        mode.Client.LOCAL,
        force_output=True,
        allow_fail=True
    )
    _version = parse_version(_raw_version)

    if _version:
        output.message(
            output.Subject.LOCAL,
            f'sshpass version {_version}'
        )
        system.config['use_sshpass'] = True
        return True


def parse_version(output):
    """
    Parse version out of console output
    https://stackoverflow.com/a/60730346
    :param output: String
    :return:
    """
    _version_pattern = r'\d+(=?\.(\d+(=?\.(\d+)*)*)*)*'
    _regex_matcher = re.compile(_version_pattern)
    _version = _regex_matcher.search(output)
    if _version:
        return _version.group(0)
    else:
        return None


def get_file_from_path(path):
    """
    Trims a path string to retrieve the file
    :param path:
    :return: file
    """
    return path.split('/')[-1]


def confirm(prompt=None, resp=False):
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
        prompt = '%s [%s|%s]: ' % (prompt, 'Y', 'n')
    else:
        prompt = '%s [%s|%s]: ' % (prompt, 'y', 'N')

    while True:
        ans = input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print('Please enter y or n.')
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False


def clean_db_config(config):
    """
    Iterates over all entries of a dictionary and removes enclosing inverted commas
    from the values, if present.

    :param config: The dictionary to be edited
    :return: A new dictionary with adjusted values
    """
    # Iterate over all entries in the dictionary and use the inverted comma function
    return {key: remove_surrounding_quotes(value) for key, value in config.items()}


def remove_surrounding_quotes(s):
    """
    Removes the enclosing inverted commas (single or double),
    if there are quotes at both the beginning and the end of the string.

    :param s: The string to be checked
    :return: The string without enclosing quotes, if available
    """
    if isinstance(s, str):
        if s.startswith('"') and s.endswith('"'):
            return s[1:-1]
        elif s.startswith("'") and s.endswith("'"):
            return s[1:-1]
    return s


def run_sed_command(client, command):
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
    if option == '':
        option = '-E'

    return mode.run_command(
        f"{get_command(client, 'sed')} -n {option} {command}",
        client,
        True
    ).strip().replace('\n', '')
