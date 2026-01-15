#!/usr/bin/env python3

"""
rsync script
"""

import re
from db_sync_tool.utility import mode, system, output

# Default options for rsync command
# https://wiki.ubuntuusers.de/rsync/
default_options = [
    '--delete',
    '-a',
    '-z',
    '--stats',
    '--human-readable',
    '--iconv=UTF-8',
    '--chmod=D2770,F660'
]


def get_password_environment(client):
    """
    Optionally create a password environment variable for sshpass password authentication
    https://www.redhat.com/sysadmin/ssh-automation-sshpass
    :param client: String
    :return:
    """
    if not client:
        return ''

    if system.config['use_sshpass'] and not 'ssh_key' in system.config[client] and 'password' in system.config[client]:
        return f'SSHPASS=\'{system.config[client]["password"]}\' '
    return ''


def get_authorization(client):
    """
    Define authorization arguments for rsync command
    :param client: String
    :return: String
    """
    _ssh_key = None
    if not client:
        return ''

    if 'ssh_key' in system.config[client]:
        _ssh_key = system.config[mode.Client.ORIGIN]['ssh_key']

    _ssh_port = system.config[client]['port'] if 'port' in system.config[client] else 22

    if _ssh_key is None:
        if system.config['use_sshpass'] and get_password_environment(client):
            # In combination with SSHPASS environment variable
            # https://www.redhat.com/sysadmin/ssh-automation-sshpass
            return f'--rsh="sshpass -e ssh -p{_ssh_port} -o StrictHostKeyChecking=no -l {system.config[client]["user"]}"'
        else:
            return f'-e "ssh -p{_ssh_port} -o StrictHostKeyChecking=no"'
    else:
        # Provide ssh key file path for ssh authentication
        return f'-e "ssh -i {_ssh_key} -p{_ssh_port}"'


def get_host(client):
    """
    Return user@host if client is not local
    :param client: String
    :return: String
    """
    if mode.is_remote(client):
        return f'{system.config[client]["user"]}@{system.config[client]["host"]}:'
    return ''


def get_options():
    """
    Prepare rsync options with stored default options and provided addtional options
    :return: String
    """
    _options = f'{" ".join(default_options)}'
    if not system.config['use_rsync_options'] is None:
        _options += f'{system.config["use_rsync_options"]}'
    return _options


def read_stats(stats):
    """
    Read rsync stats and print a summary
    :param stats: String
    :return:
    """
    if system.config['verbose']:
        print(f'{output.Subject.DEBUG}{output.CliFormat.BLACK}{stats}{output.CliFormat.ENDC}')

    _file_size = parse_string(stats, r'Total transferred file size:\s*([\d.]+[MKG]?)')

    if _file_size:
        output.message(
            output.Subject.INFO,
            f'Status: {unit_converter(_file_size[0])} transferred'
        )


def parse_string(string, regex):
    """
    Parse string by given regex
    :param string: String
    :param regex: String
    :return:
    """
    _file_size_pattern = regex
    _regex_matcher = re.compile(_file_size_pattern)
    return _regex_matcher.findall(string)


def unit_converter(size_in_bytes):
    """

    :param size_in_bytes:
    :return:
    """
    units = ['Bytes', 'kB', 'MB', 'GB']

    if isinstance(size_in_bytes, (int, float)):
        _convertedSize = float(size_in_bytes)
        for unit in units:
            if _convertedSize < 1024:
                return str(_convertedSize) + ' ' + unit
            _convertedSize = _convertedSize / 1024

        return _convertedSize
    return size_in_bytes


def run_rsync_command(remote_client, origin_path, target_path, origin_ssh='', target_ssh=''):
    """

    :param target_ssh:
    :param origin_ssh:
    :param target_path:
    :param origin_path:
    :param remote_client:
    :return:
    """
    if origin_ssh != '':
        origin_ssh += ':'
    if target_ssh != '':
        target_ssh += ':'

    _output = mode.run_command(
        f'{get_password_environment(remote_client)}rsync {get_options()} '
        f'{get_authorization(remote_client)} '
        f'{origin_ssh}{origin_path} {target_ssh}{target_path}',
        mode.Client.LOCAL,
        True
    )
    read_stats(_output)
