#!/usr/bin/env python3

"""
Parser script
"""

import sys
import types
from db_sync_tool.utility import mode, system, output, helper
from db_sync_tool.utility.exceptions import ConfigError, ValidationError
from db_sync_tool.remote import client as remote_client


class Framework:
    TYPO3 = 'TYPO3'
    SYMFONY = 'Symfony'
    DRUPAL = 'Drupal'
    WORDPRESS = 'Wordpress'
    LARAVEL = 'Laravel'
    MANUAL = 'Manual'


mapping = {
    Framework.TYPO3: [
        'LocalConfiguration.php',
        'AdditionalConfiguration.php'
    ],
    Framework.SYMFONY: [
        '.env',
        'parameters.yml'
    ],
    Framework.DRUPAL: [
        'settings.php'
    ],
    Framework.WORDPRESS: [
        'wp-config.php'
    ],
    Framework.LARAVEL: [
        '.env'
    ]
}


def get_database_configuration(client):
    """
    Getting database configuration of given client and defined sync base (framework type)
    :param client: String
    :return:
    """
    cfg = system.get_typed_config()

    # check framework type
    _base = ''

    automatic_type_detection()

    # Re-get config after type detection may have updated it
    cfg = system.get_typed_config()

    if cfg.type and (cfg.origin.path != '' or cfg.target.path != ''):
        _type = cfg.type.lower()
        if _type == 'typo3':
            # TYPO3 sync base
            _base = Framework.TYPO3
        elif _type == 'symfony':
            # Symfony sync base
            _base = Framework.SYMFONY
        elif _type == 'drupal':
            # Drupal sync base
            _base = Framework.DRUPAL
        elif _type == 'wordpress':
            # Wordpress sync base
            _base = Framework.WORDPRESS
        elif _type == 'laravel':
            # Laravel sync base
            _base = Framework.LARAVEL
        else:
            raise ConfigError(f'Framework type not supported: {_type}')
    elif cfg.origin.db.name != '' or cfg.target.db.name != '':
        _base = Framework.MANUAL
    else:
        raise ConfigError('Missing framework type or database credentials')

    sys.path.append('../recipes')
    _parser: types.ModuleType | None = None
    if _base == Framework.TYPO3:
        # Import TYPO3 parser
        from ..recipes import typo3
        _parser = typo3

    elif _base == Framework.SYMFONY:
        # Import Symfony parser
        from ..recipes import symfony
        _parser = symfony

    elif _base == Framework.DRUPAL:
        # Import Symfony parser
        from ..recipes import drupal
        _parser = drupal

    elif _base == Framework.WORDPRESS:
        # Import Symfony parser
        from ..recipes import wordpress
        _parser = wordpress

    elif _base == Framework.LARAVEL:
        # Import Symfony parser
        from ..recipes import laravel
        _parser = laravel

    if client == mode.Client.ORIGIN:
        output.message(
            output.Subject.INFO,
            'Sync base: ' + _base,
            True
        )

    if _base != Framework.MANUAL:
        load_parser(client, _parser)
    else:
        if client == mode.Client.ORIGIN and mode.is_origin_remote():
            remote_client.load_ssh_client_origin()
        elif client == mode.Client.TARGET and mode.is_target_remote():
            remote_client.load_ssh_client_target()

    validate_database_credentials(client)


def load_parser(client, parser):
    """
    Loading parser and checking database configuration
    :param client:
    :param parser:
    :return:
    """
    cfg = system.get_typed_config()
    _path = cfg.get_client(client).path

    output.message(
        output.host_to_subject(client),
        f'Checking database configuration {output.CliFormat.BLACK}{_path}{output.CliFormat.ENDC}',
        True
    )
    if client == mode.Client.ORIGIN:
        if mode.is_origin_remote():
            remote_client.load_ssh_client_origin()
        else:
            helper.run_script(client, 'before')
    else:
        if mode.is_target_remote():
            remote_client.load_ssh_client_target()
        else:
            helper.run_script(client, 'before')

    # Check only if database configuration is a file
    if not helper.check_file_exists(client, _path) and _path[-1] != '/':
        raise ConfigError(f'Database configuration for {client} not found: {_path}')
    parser.check_configuration(client)


def validate_database_credentials(client):
    """
    Validate the parsed database credentials
    :param client: String
    :return:
    """
    cfg = system.get_typed_config()
    db_cfg = cfg.get_client(client).db

    output.message(
        output.host_to_subject(client),
        'Validating database credentials',
        True
    )
    _db_credential_keys = ['name', 'host', 'password', 'user']

    for _key in _db_credential_keys:
        _value = getattr(db_cfg, _key, None)
        if _value is None or _value == '':
            raise ValidationError(
                f'Missing database credential "{_key}" for {client} client'
            )
        else:
            output.message(
                output.host_to_subject(client),
                f'Database credential "{_key}" valid',
                verbose_only=True
            )


def automatic_type_detection():
    """
    Detects the framework type by the provided path using the default mapping
    """
    cfg = system.get_typed_config()

    # Skip if type is already set or manual db config is provided
    if cfg.type or cfg.origin.db.name != '' or cfg.target.db.name != '':
        return

    detected_type = None
    file = None

    for _client in [mode.Client.ORIGIN, mode.Client.TARGET]:
        client_cfg = cfg.get_client(_client)
        if client_cfg.path != '':
            file = helper.get_file_from_path(client_cfg.path)
            for _key, _files in mapping.items():
                if file in _files:
                    detected_type = _key

    if detected_type:
        output.message(
            output.Subject.LOCAL,
            f'Automatic framework type detection '
            f'{output.CliFormat.BLACK}{file}{output.CliFormat.ENDC}',
            verbose_only=True
        )
        system.set_framework_type(detected_type)
