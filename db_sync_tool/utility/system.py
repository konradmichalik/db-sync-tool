#!/usr/bin/env python3

"""
System module
"""

import json
import os
import getpass
import secrets
from pathlib import Path
from typing import Any, TYPE_CHECKING
import yaml
from db_sync_tool.utility import log, parser, mode, helper, output, validation
from db_sync_tool.utility.console import get_output_manager
from db_sync_tool.utility.exceptions import ConfigError
from db_sync_tool.remote import utility as remote_utility

if TYPE_CHECKING:
    from db_sync_tool.utility.config import SyncConfig

#
# GLOBALS
#

config: dict[str, Any] = {
    'verbose': 0,  # 0=compact, 1=verbose, 2=debug
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
    'with_files': False,  # Enable file synchronization (opt-in)
    'files_only': False,  # Sync only files, skip database
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

# Typed configuration (single source of truth after migration)
_typed_config: 'SyncConfig | None' = None


def get_typed_config() -> 'SyncConfig':
    """
    Get current configuration as typed SyncConfig object.

    :return: SyncConfig instance
    """
    global _typed_config
    if _typed_config is None:
        from db_sync_tool.utility.config import SyncConfig
        _typed_config = SyncConfig.from_dict(config)
    return _typed_config


def refresh_typed_config() -> None:
    """
    Refresh typed config after dict changes.

    Call this after modifying system.config to keep _typed_config in sync.
    This is needed during the migration phase where both dict and dataclass
    are used.
    """
    global _typed_config
    from db_sync_tool.utility.config import SyncConfig
    _typed_config = SyncConfig.from_dict(config)


def _set_config_value(key: str, value, client: str | None = None) -> None:
    """
    Set a configuration value and refresh typed config.

    :param key: Configuration key
    :param value: Value to set
    :param client: Optional client identifier for nested config
    """
    if client:
        config.setdefault(client, {})[key] = value
    else:
        config[key] = value
    refresh_typed_config()


def set_database_config(client: str, db_config: dict) -> None:
    """Set database configuration for a client."""
    _set_config_value('db', db_config, client)


def set_framework_type(type_name: str) -> None:
    """Set the framework type."""
    _set_config_value('type', type_name)


def set_is_same_client(value: bool) -> None:
    """Set is_same_client flag."""
    _set_config_value('is_same_client', value)


def set_use_sshpass(value: bool) -> None:
    """Set use_sshpass flag."""
    _set_config_value('use_sshpass', value)


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
    :param args: Dictionary (or argparse.Namespace with resolved_config attribute)
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
                    raise ConfigError(
                        f'Unsupported configuration file type [json,yml,yaml]: '
                        f'{config["config_file_path"]}'
                    )
                output.message(
                    output.Subject.LOCAL,
                    f'Loading host configuration '
                    f'{output.CliFormat.BLACK}{_config_file_path}{output.CliFormat.ENDC}',
                    True
                )
        else:
            raise ConfigError(
                f'Local configuration not found: {config["config_file_path"]}'
            )

    # Apply resolved config from ConfigResolver (if present)
    _apply_resolved_config(args)

    # workaround for argument order handling respecting the linking feature
    build_config(args, True)
    link_configuration_with_hosts()
    build_config(args)

    validation.check(config)
    check_options()

    if not config[mode.Client.TARGET] and not config[mode.Client.ORIGIN]:
        raise ConfigError(
            'Configuration is missing, use a separate file or provide host parameter'
        )

    # Refresh typed config after all configuration is loaded
    refresh_typed_config()

    helper.run_script(script='before')
    log.get_logger().info('Starting db_sync_tool')


def _apply_resolved_config(args) -> None:
    """
    Apply resolved config from ConfigResolver to the global config.

    :param args: argparse.Namespace or dict that may contain resolved_config
    """
    global config

    # Get resolved_config from args (if present)
    resolved_config = getattr(args, 'resolved_config', None)
    if resolved_config is None:
        return

    # Apply merged config first (global defaults + project defaults)
    if resolved_config.merged_config:
        for key, value in resolved_config.merged_config.items():
            if key not in ('origin', 'target'):
                config[key] = value

    # Apply origin config
    if resolved_config.origin_config:
        config[mode.Client.ORIGIN] = {**config[mode.Client.ORIGIN], **resolved_config.origin_config}

    # Apply target config
    if resolved_config.target_config:
        config[mode.Client.TARGET] = {**config[mode.Client.TARGET], **resolved_config.target_config}

    # Log the source
    if resolved_config.source:
        output.message(
            output.Subject.INFO,
            f'Configuration resolved from {resolved_config.source}',
            True
        )


# Argument mapping: (arg_name, config_path)
# config_path is a tuple: (client, key) or (client, nested_key, key) or just (key,) for top-level
_ARG_MAPPINGS_PRE_RUN = [
    ('type', ('type',)),
    ('tables', ('tables',)),
    ('origin', ('link_origin',)),
    ('target', ('link_target',)),
]

_ARG_MAPPINGS_MAIN = [
    # Target client mappings
    ('target_path', (mode.Client.TARGET, 'path')),
    ('target_name', (mode.Client.TARGET, 'name')),
    ('target_host', (mode.Client.TARGET, 'host')),
    ('target_user', (mode.Client.TARGET, 'user')),
    ('target_password', (mode.Client.TARGET, 'password')),
    ('target_key', (mode.Client.TARGET, 'ssh_key')),
    ('target_port', (mode.Client.TARGET, 'port')),
    ('target_dump_dir', (mode.Client.TARGET, 'dump_dir')),
    ('target_after_dump', (mode.Client.TARGET, 'after_dump')),
    ('target_db_name', (mode.Client.TARGET, 'db', 'name')),
    ('target_db_host', (mode.Client.TARGET, 'db', 'host')),
    ('target_db_user', (mode.Client.TARGET, 'db', 'user')),
    ('target_db_password', (mode.Client.TARGET, 'db', 'password')),
    ('target_db_port', (mode.Client.TARGET, 'db', 'port')),
    # Origin client mappings
    ('origin_path', (mode.Client.ORIGIN, 'path')),
    ('origin_name', (mode.Client.ORIGIN, 'name')),
    ('origin_host', (mode.Client.ORIGIN, 'host')),
    ('origin_user', (mode.Client.ORIGIN, 'user')),
    ('origin_password', (mode.Client.ORIGIN, 'password')),
    ('origin_key', (mode.Client.ORIGIN, 'ssh_key')),
    ('origin_port', (mode.Client.ORIGIN, 'port')),
    ('origin_dump_dir', (mode.Client.ORIGIN, 'dump_dir')),
    ('origin_db_name', (mode.Client.ORIGIN, 'db', 'name')),
    ('origin_db_host', (mode.Client.ORIGIN, 'db', 'host')),
    ('origin_db_user', (mode.Client.ORIGIN, 'db', 'user')),
    ('origin_db_password', (mode.Client.ORIGIN, 'db', 'password')),
    ('origin_db_port', (mode.Client.ORIGIN, 'db', 'port')),
    # Top-level config mappings
    ('where', ('where',)),
    ('additional_mysqldump_options', ('additional_mysqldump_options',)),
]


def _apply_arg_mapping(args, mapping):
    """
    Apply argument mappings to config dict.

    :param args: Argument namespace
    :param mapping: List of (arg_name, config_path) tuples
    """
    for arg_name, config_path in mapping:
        value = getattr(args, arg_name, None)
        if value is None:
            continue

        if len(config_path) == 1:
            # Top-level config key
            config[config_path[0]] = value
        elif len(config_path) == 2:
            # Client-level key: (client, key)
            config[config_path[0]][config_path[1]] = value
        elif len(config_path) == 3:
            # Nested client key: (client, nested_key, key)
            check_config_dict_key(config_path[0], config_path[1])
            config[config_path[0]][config_path[1]][config_path[2]] = value


def build_config(args, pre_run=False):
    """
    Apply provided CLI arguments to config dict.

    :param args: Argument namespace from argparse
    :param pre_run: Boolean, if True only apply link-related args
    :return: config dict
    """
    if args is None or not args:
        return {}

    _apply_arg_mapping(args, _ARG_MAPPINGS_PRE_RUN)

    if not pre_run:
        _apply_arg_mapping(args, _ARG_MAPPINGS_MAIN)

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
    # Refresh typed config after authorization changes (ssh_agent, password)
    refresh_typed_config()


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
                raise ConfigError(f'SSH {client} private key not found: {_ssh_key}')
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
    _prompt = get_output_manager().build_prompt(
        f'SSH password {helper.get_ssh_host_name(client, True)}: ',
        subject='INFO'
    )
    _password = getpass.getpass(_prompt)

    while _password.strip() == '':
        output.message(
            output.Subject.WARNING,
            'Password seems to be empty. Please enter a valid password.',
            True
        )

        _prompt = get_output_manager().build_prompt(
            f'SSH password {helper.get_ssh_host_name(client, True)}: ',
            subject='INFO'
        )
        _password = getpass.getpass(_prompt)

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
                       reverse=False,
                       with_files=False,
                       files_only=False):
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
    :param with_files:
    :param files_only:
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

    if with_files is not None:
        config['with_files'] = with_files

    if files_only is not None:
        config['files_only'] = files_only
        if files_only:
            # files_only implies with_files
            config['with_files'] = True


def reverse_hosts():
    """
    Reverse origin and target hosts if --reverse flag is set.
    :return:
    """
    if config['reverse']:
        _origin = config[mode.Client.ORIGIN]
        _target = config[mode.Client.TARGET]

        config[mode.Client.ORIGIN] = _target
        config[mode.Client.TARGET] = _origin

        # Refresh typed config after swapping
        refresh_typed_config()

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
            raise ConfigError(
                'Missing hosts file for linking hosts with configuration. '
                'Use the "-o" / "--hosts" argument to define the filepath for the hosts file, '
                'when using a link parameter within the configuration or define the '
                'filepath direct in the link entry e.g. "host.yaml@entry1".'
            )

    if config['link_hosts'] != '':

        # Adjust filepath from relative to absolute
        if not config['link_hosts'].startswith('/'):
            base_path = Path(config['config_file_path']).resolve().parent if config['config_file_path'] else Path.cwd()
            config['link_hosts'] = str(base_path / config['link_hosts'])

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
                            raise ConfigError(
                                f'Misconfiguration of link hosts {config["link_origin"]}, '
                                f'{config["link_target"]} in {config["link_hosts"]}'
                            )
                    else:
                        raise ConfigError(f'Missing link hosts for {config["link_hosts"]}')
        else:
            raise ConfigError(f'Local host file not found: {config["link_hosts"]}')


def check_config_dict_key(client, key):
    """
    Create config key if is not present
    :param client:
    :param key:
    :return:
    """
    if key not in config[client]:
        config[client][key] = {}

