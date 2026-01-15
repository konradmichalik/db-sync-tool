#!/usr/bin/env python3

"""
Parser script
"""

import sys
from db_sync_tool.utility import mode, system, output, helper
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
    system.config['db'] = {}

    # check framework type
    _base = ''

    automatic_type_detection()

    if 'type' in system.config and (
            'path' in system.config[mode.Client.ORIGIN] or
            'path' in system.config[mode.Client.TARGET]
    ):
        _type = system.config['type'].lower()
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
            sys.exit(
                output.message(
                    output.Subject.ERROR,
                    f'Framework type not supported: {_type}',
                    False
                )
            )
    elif 'db' in system.config['origin'] or 'db' in system.config['target']:
        _base = Framework.MANUAL
    else:
        sys.exit(
            output.message(
                output.Subject.ERROR,
                f'Missing framework type or database credentials',
                False
            )
        )

    sys.path.append('../recipes')
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
    _path = system.config[client]['path']

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
        sys.exit(
            output.message(
                output.Subject.ERROR,
                f'Database configuration for {client} not found: {_path}',
                False
            )
        )
    parser.check_configuration(client)


def validate_database_credentials(client):
    """
    Validate the parsed database credentials
    :param client: String
    :return:
    """
    output.message(
        output.host_to_subject(client),
        'Validating database credentials',
        True
    )
    _db_credential_keys = ['name', 'host', 'password', 'user']

    for _key in _db_credential_keys:
        if _key not in system.config[client]['db']:
            sys.exit(
                output.message(
                    output.Subject.ERROR,
                    f'Missing database credential "{_key}" for {client} client',
                    False
                )
            )
        if system.config[client]['db'][_key] is None or system.config[client]['db'][_key] == '':
            sys.exit(
                output.message(
                    output.Subject.ERROR,
                    f'Missing database credential "{_key}" for {client} client',
                    False
                )
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
    if 'type' in system.config or 'db' in system.config['origin'] or 'db' in system.config[
        'target']:
        return

    type = None
    file = None

    for _client in [mode.Client.ORIGIN, mode.Client.TARGET]:
        if 'path' in system.config[_client]:
            file = helper.get_file_from_path(system.config[_client]['path'])
            for _key, _files in mapping.items():
                if file in _files:
                    type = _key

    if type:
        output.message(
            output.Subject.LOCAL,
            f'Automatic framework type detection '
            f'{output.CliFormat.BLACK}{file}{output.CliFormat.ENDC}',
            verbose_only=True
        )
        system.config['type'] = type
