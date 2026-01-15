#!/usr/bin/env python3

"""
System module
"""

import sys
import json
import os
import getpass
import secrets
import yaml
from db_sync_tool.utility import log, parser, mode, helper, output, validation
from db_sync_tool.remote import utility as remote_utility

#
# GLOBALS
#

config = {
    'verbose': False,
    'mute': False,
    'dry_run': False,
    'keep_dump': False,
    'dump_name': '',
    'import': '',
    'link_hosts': '',
    'default_origin_dump_dir': True,
    'default_target_dump_dir': True,
    'check_dump': True,
    'is_same_client': False,
    'config_file_path': None,
    'clear_database': False,
    'force_password': False,
    'use_rsync': True,  # rsync is 5-10x faster than Paramiko SFTP
    'use_rsync_options': None,
    'use_sshpass': False,
    'ssh_agent': False,
    'ssh_password': {
        mode.Client.ORIGIN: None,
        mode.Client.TARGET: None
    },
    'link_target': None,
    'link_origin': None,
    'tables': '',
    'where': '',
    'additional_mysqldump_options': ''
}

#
# DEFAULTS
#

# Generate a secure random suffix to prevent predictable temp paths
_temp_suffix = secrets.token_hex(8)
default_local_sync_path = f'/tmp/db_sync_tool_{_temp_suffix}/'


def create_secure_temp_dir(path):
    """
    Create a temporary directory with secure permissions (0700).
    Prevents other users from accessing sensitive database dumps.

    :param path: String path to create
    :return: String path
    """
    if not os.path.exists(path):
        os.makedirs(path, mode=0o700)
    else:
        # Ensure secure permissions even if directory exists
        os.chmod(path, 0o700)
    return path


#
# FUNCTIONS
#

def check_target_configuration():
    """
    Checking target database configuration
    :return:
    """
    parser.get_database_configuration(mode.Client.TARGET)


def get_configuration(host_config, args = {}):
    """
    Checking configuration information by file or dictionary
    :param host_config: Dictionary
    :param args: Dictionary
    :return:
    """
    global config
    config[mode.Client.TARGET] = {}
    config[mode.Client.ORIGIN] = {}

    if host_config:
        if type(host_config) is dict:
            config.update(__m=host_config)
        else:
            config.update(__m=json.dumps(obj=host_config))

    _config_file_path = config['config_file_path']
    if not _config_file_path is None:
        if os.path.isfile(_config_file_path):
            with open(_config_file_path, 'r') as read_file:
                if _config_file_path.endswith('.json'):
                    config.update(json.load(read_file))
                elif _config_file_path.endswith('.yaml') or _config_file_path.endswith('.yml'):
                    config.update(yaml.safe_load(read_file))
                else:
                    sys.exit(
                        output.message(
                            output.Subject.ERROR,
                            f'Unsupported configuration file type [json,yml,yaml]: '
                            f'{config["config_file_path"]}',
                            False
                        )
                    )
                output.message(
                    output.Subject.LOCAL,
                    f'Loading host configuration '
                    f'{output.CliFormat.BLACK}{_config_file_path}{output.CliFormat.ENDC}',
                    True
                )
        else:
            sys.exit(
                output.message(
                    output.Subject.ERROR,
                    f'Local configuration not found: {config["config_file_path"]}',
                    False
                )
            )

    # workaround for argument order handling respecting the linking feature
    build_config(args, True)
    link_configuration_with_hosts()
    build_config(args)

    validation.check(config)
    check_options()

    if not config[mode.Client.TARGET] and not config[mode.Client.ORIGIN]:
        sys.exit(
            output.message(
                output.Subject.ERROR,
                f'Configuration is missing, use a separate file or provide host parameter',
                False
            )
        )
    helper.run_script(script='before')
    log.get_logger().info('Starting db_sync_tool')


def build_config(args, pre_run = False):
    """
    ADding the provided arguments
    :param args:
    :param pre_run:
    :return:
    """
    if args is None or not args:
        return {}

    if not args.type is None:
        config['type'] = args.type

    if not args.tables is None:
        config['tables'] = args.tables

    if not args.origin is None:
        config['link_origin'] = args.origin

    if not args.target is None:
        config['link_target'] = args.target

    # for order reasons check just the link arguments
    if pre_run: return

    if not args.target_path is None:
        config[mode.Client.TARGET]['path'] = args.target_path

    if not args.target_name is None:
        config[mode.Client.TARGET]['name'] = args.target_name

    if not args.target_host is None:
        config[mode.Client.TARGET]['host'] = args.target_host

    if not args.target_user is None:
        config[mode.Client.TARGET]['user'] = args.target_user

    if not args.target_password is None:
        config[mode.Client.TARGET]['password'] = args.target_password

    if not args.target_key is None:
        config[mode.Client.TARGET]['ssh_key'] = args.target_key

    if not args.target_port is None:
        config[mode.Client.TARGET]['port'] = args.target_port

    if not args.target_dump_dir is None:
        config[mode.Client.TARGET]['dump_dir'] = args.target_dump_dir

    if not args.target_db_name is None:
        check_config_dict_key(mode.Client.TARGET, 'db')
        config[mode.Client.TARGET]['db']['name'] = args.target_db_name

    if not args.target_db_host is None:
        check_config_dict_key(mode.Client.TARGET, 'db')
        config[mode.Client.TARGET]['db']['host'] = args.target_db_host

    if not args.target_db_user is None:
        check_config_dict_key(mode.Client.TARGET, 'db')
        config[mode.Client.TARGET]['db']['user'] = args.target_db_user

    if not args.target_db_password is None:
        check_config_dict_key(mode.Client.TARGET, 'db')
        config[mode.Client.TARGET]['db']['password'] = args.target_db_password

    if not args.target_db_port is None:
        check_config_dict_key(mode.Client.TARGET, 'db')
        config[mode.Client.TARGET]['db']['port'] = args.target_db_port

    if not args.target_after_dump is None:
        config[mode.Client.TARGET]['after_dump'] = args.target_after_dump

    if not args.origin_path is None:
        config[mode.Client.ORIGIN]['path'] = args.origin_path

    if not args.origin_name is None:
        config[mode.Client.ORIGIN]['name'] = args.origin_name

    if not args.origin_host is None:
        config[mode.Client.ORIGIN]['host'] = args.origin_host

    if not args.origin_user is None:
        config[mode.Client.ORIGIN]['user'] = args.origin_user

    if not args.origin_password is None:
        config[mode.Client.ORIGIN]['password'] = args.origin_password

    if not args.origin_key is None:
        config[mode.Client.ORIGIN]['ssh_key'] = args.origin_key

    if not args.origin_port is None:
        config[mode.Client.ORIGIN]['port'] = args.origin_port

    if not args.origin_dump_dir is None:
        config[mode.Client.ORIGIN]['dump_dir'] = args.origin_dump_dir

    if not args.origin_db_name is None:
        check_config_dict_key(mode.Client.ORIGIN, 'db')
        config[mode.Client.ORIGIN]['db']['name'] = args.origin_db_name

    if not args.origin_db_host is None:
        check_config_dict_key(mode.Client.ORIGIN, 'db')
        config[mode.Client.ORIGIN]['db']['host'] = args.origin_db_host

    if not args.origin_db_user is None:
        check_config_dict_key(mode.Client.ORIGIN, 'db')
        config[mode.Client.ORIGIN]['db']['user'] = args.origin_db_user

    if not args.origin_db_password is None:
        check_config_dict_key(mode.Client.ORIGIN, 'db')
        config[mode.Client.ORIGIN]['db']['password'] = args.origin_db_password

    if not args.origin_db_port is None:
        check_config_dict_key(mode.Client.ORIGIN, 'db')
        config[mode.Client.ORIGIN]['db']['port'] = args.origin_db_port

    if not args.where is None:
        config['where'] = args.where

    if not args.additional_mysqldump_options is None:
        config['additional_mysqldump_options'] = args.additional_mysqldump_options

    return config


def check_options():
    """
    Checking configuration provided file
    :return:
    """
    global config
    if 'dump_dir' in config[mode.Client.ORIGIN]:
        config['default_origin_dump_dir'] = False

    if 'dump_dir' in config[mode.Client.TARGET]:
        config['default_target_dump_dir'] = False

    if 'check_dump' in config:
        config['check_dump'] = config['check_dump']

    # Check rsync availability if enabled (default: True)
    # Falls back to Paramiko SFTP if rsync is not available
    if config['use_rsync']:
        if helper.check_rsync_version():
            helper.check_sshpass_version()
        else:
            config['use_rsync'] = False
            output.message(
                output.Subject.WARNING,
                'rsync not found, falling back to SFTP transfer',
                True
            )

    reverse_hosts()
    mode.check_sync_mode()


def check_authorizations():
    """
    Checking authorization for clients
    :return:
    """
    check_authorization(mode.Client.ORIGIN)
    check_authorization(mode.Client.TARGET)


def check_authorization(client):
    """
    Checking arguments and fill options array
    :param client: String
    :return:
    """
    # only need authorization if client is remote
    if mode.is_remote(client):
        # Workaround if no authorization is needed
        if (mode.get_sync_mode() == mode.SyncMode.DUMP_REMOTE and
            client == mode.Client.TARGET) or \
                (mode.get_sync_mode() == mode.SyncMode.DUMP_LOCAL and
                 client == mode.Client.ORIGIN) or \
                (mode.get_sync_mode() == mode.SyncMode.IMPORT_REMOTE and
                 client == mode.Client.ORIGIN):
            return

        # ssh key authorization
        if config['force_password']:
            config[client]['password'] = get_password_by_user(client)
        elif 'ssh_key' in config[client]:
            _ssh_key = config[client]['ssh_key']
            if not os.path.isfile(_ssh_key):
                sys.exit(
                    output.message(
                        output.Subject.ERROR,
                        f'SSH {client} private key not found: {_ssh_key}',
                        False
                    )
                )
        elif 'password' in config[client]:
            config[client]['password'] = config[client]['password']
        elif remote_utility.check_keys_from_ssh_agent():
            config['ssh_agent'] = True
        else:
            # user input authorization
            config[client]['password'] = get_password_by_user(client)

        if mode.get_sync_mode() == mode.SyncMode.DUMP_REMOTE and \
                client == mode.Client.ORIGIN and 'password' in \
                config[mode.Client.ORIGIN]:
            config[mode.Client.TARGET]['password'] = config[mode.Client.ORIGIN]['password']


def get_password_by_user(client):
    """
    Getting password by user input
    :param client: String
    :return: String password
    """
    _password = getpass.getpass(
        output.message(
            output.Subject.INFO,
            'SSH password ' + helper.get_ssh_host_name(client, True) + ': ',
            False
        )
    )

    while _password.strip() == '':
        output.message(
            output.Subject.WARNING,
            'Password seems to be empty. Please enter a valid password.',
            True
        )

        _password = getpass.getpass(
            output.message(
                output.Subject.INFO,
                'SSH password ' + helper.get_ssh_host_name(client, True) + ': ',
                False
            )
        )

    return _password


def check_args_options(config_file=None,
                       verbose=False,
                       yes=False,
                       mute=False,
                       dry_run=False,
                       import_file=None,
                       dump_name=None,
                       keep_dump=None,
                       host_file=None,
                       clear=False,
                       force_password=False,
                       use_rsync=False,
                       use_rsync_options=None,
                       reverse=False):
    """
    Checking arguments and fill options array
    :param config_file:
    :param verbose:
    :param yes:
    :param mute:
    :param dry_run:
    :param import_file:
    :param dump_name:
    :param keep_dump:
    :param host_file:
    :param clear:
    :param force_password:
    :param use_rsync:
    :param use_rsync_options:
    :param reverse:
    :return:
    """
    global config
    global default_local_sync_path

    if not config_file is None:
        config['config_file_path'] = config_file

    if not verbose is None:
        config['verbose'] = verbose

    if not yes is None:
        config['yes'] = yes

    if not mute is None:
        config['mute'] = mute

    if not dry_run is None:
        config['dry_run'] = dry_run

        if dry_run:
            output.message(
                output.Subject.INFO,
                'Test mode: DRY RUN',
                True
            )

    if not import_file is None:
        config['import'] = import_file

    if not dump_name is None:
        config['dump_name'] = dump_name

    if not host_file is None:
        config['link_hosts'] = host_file

    if not clear is None:
        config['clear_database'] = clear

    if not force_password is None:
        config['force_password'] = force_password

    if use_rsync is not None:
        config['use_rsync'] = use_rsync

    if use_rsync_options is not None:
        config['use_rsync_options'] = use_rsync_options

    if not reverse is None:
        config['reverse'] = reverse

    if not keep_dump is None:
        default_local_sync_path = keep_dump

        # Adding trailing slash if necessary
        if default_local_sync_path[-1] != '/':
            default_local_sync_path += '/'

        config['keep_dump'] = True
        output.message(
            output.Subject.INFO,
            '"Keep dump" option chosen',
            True
        )


def reverse_hosts():
    """
    Checking authorization for clients
    :return:
    """
    if config['reverse']:
        _origin = config[mode.Client.ORIGIN]
        _target = config[mode.Client.TARGET]

        config[mode.Client.ORIGIN] = _target
        config[mode.Client.TARGET] = _origin

        output.message(
            output.Subject.INFO,
            'Reverse origin and target hosts',
            True
        )


def link_configuration_with_hosts():
    """
    Merging the hosts definition with the given configuration file
    @ToDo Simplify function
    :return:
    """
    if ('link' in config[mode.Client.ORIGIN] or 'link' in config[mode.Client.TARGET]) and config['link_hosts'] == '':
        #
        # Try to read host file path from link entry
        #
        _host = str(config[mode.Client.ORIGIN]['link'].split('@')[0]) if 'link' in config[mode.Client.ORIGIN] else ''
        _host = str(config[mode.Client.TARGET]['link'].split('@')[0]) if 'link' in config[mode.Client.TARGET] else _host

        config['link_hosts'] = _host

        if config['link_hosts'] == '':
            # Try to find default hosts.json file in same directory
            sys.exit(
                output.message(
                    output.Subject.ERROR,
                    f'Missing hosts file for linking hosts with configuration. '
                    f'Use the "-o" / "--hosts" argument to define the filepath for the hosts file, '
                    f'when using a link parameter within the configuration or define the the '
                    f'filepath direct in the link entry e.g. "host.yaml@entry1".',
                    False
                )
            )

    if config['link_hosts'] != '':

        # Adjust filepath from relative to absolute
        if config['link_hosts'][0] != '/':
            config['link_hosts'] = os.path.dirname(os.path.abspath(config['config_file_path'])) + '/' + config['link_hosts']

        if os.path.isfile(config['link_hosts']):
            with open(config['link_hosts'], 'r') as read_file:
                if config['link_hosts'].endswith('.json'):
                    _hosts = json.load(read_file)
                elif config['link_hosts'].endswith('.yaml') or config['link_hosts'].endswith('.yml'):
                    _hosts = yaml.safe_load(read_file)

                output.message(
                    output.Subject.INFO,
                    f'Linking configuration with hosts {output.CliFormat.BLACK}{config["link_hosts"]}{output.CliFormat.ENDC}',
                    True
                )
                if not config['config_file_path'] is None:
                    if 'link' in config[mode.Client.ORIGIN]:
                        _host_name = str(config[mode.Client.ORIGIN]['link']).split('@')[1]
                        if _host_name in _hosts:
                            config[mode.Client.ORIGIN] = {**config[mode.Client.ORIGIN], **_hosts[_host_name]}

                    if 'link' in config[mode.Client.TARGET]:
                        _host_name = str(config[mode.Client.TARGET]['link']).split('@')[1]
                        if _host_name in _hosts:
                            config[mode.Client.TARGET] = {**config[mode.Client.TARGET], **_hosts[_host_name]}
                else:
                    if 'link_target' in config and 'link_origin' in config:
                        if config['link_target'] in _hosts and config['link_origin'] in _hosts:
                            config[mode.Client.TARGET] = _hosts[config['link_target']]
                            config[mode.Client.ORIGIN] = _hosts[config['link_origin']]
                        else:
                            sys.exit(
                                output.message(
                                    output.Subject.ERROR,
                                    f'Misconfiguration of link hosts {config["link_origin"]}, '
                                    f'{config["link_target"]} in {config["link_hosts"]}',
                                    False
                                )
                            )
                    else:
                        sys.exit(
                            output.message(
                                output.Subject.ERROR,
                                f'Missing link hosts for {config["link_hosts"]}',
                                False
                            )
                        )
        else:
            sys.exit(
                output.message(
                    output.Subject.ERROR,
                    f'Local host file not found: {config["link_hosts"]}',
                    False
                )
            )


def check_config_dict_key(client, key):
    """
    Create config key if is not present
    :param client:
    :param key:
    :return:
    """
    if key not in config[client]:
        config[client][key] = {}

