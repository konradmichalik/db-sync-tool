#!/usr/bin/env python3

"""
Validation script
"""

from jsonschema import validators
from db_sync_tool.utility import output
from db_sync_tool.utility.exceptions import ValidationError

#
# GLOBALS
#
schema = {
    "type": "object",
    "properties": {
        "type": {"enum": ['TYPO3', 'Symfony', 'Drupal', 'Wordpress', 'Laravel']},
        "log_file": {"type": "string"},
        "ignore_table": {"type": "array"},
        "target": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "host": {"type": "string", "format": "hostname"},
                "user": {"type": "string"},
                "password": {"type": "string"},
                "path": {"type": "string"},
                "ssh_key": {"type": "string"},
                "port": {"type": "number"},
                "dump_dir": {"type": "string"},
                "after_dump": {"type": "string"},
                "db": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "host": {"type": "string", "format": "hostname"},
                        "user": {"type": "string"},
                        "password": {"type": "string"},
                        "port": {"type": "number"},
                    }
                },
                "script": {
                    "type": "object",
                    "properties": {
                        "before": {"type": "string"},
                        "after": {"type": "string"},
                        "error": {"type": "string"},
                    }
                }
            }
        },
        "origin": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "host": {"type": "string", "format": "hostname"},
                "user": {"type": "string"},
                "password": {"type": "string"},
                "path": {"type": "string"},
                "ssh_key": {"type": "string"},
                "port": {"type": "number"},
                "dump_dir": {"type": "string"},
                "after_dump": {"type": "string"},
                "db": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "host": {"type": "string", "format": "hostname"},
                        "user": {"type": "string"},
                        "password": {"type": "string"},
                        "port": {"type": "number"},
                    }
                },
                "script": {
                    "type": "object",
                    "properties": {
                        "before": {"type": "string"},
                        "after": {"type": "string"},
                        "error": {"type": "string"},
                    }
                }
            }
        },
    },
}


#
# FUNCTIONS
#


def check(config):
    output.message(
        output.Subject.LOCAL,
        'Validating configuration',
        True
    )
    v = validators.Draft7Validator(schema)
    errors = sorted(v.iter_errors(config), key=lambda e: e.path)

    for error in errors:
        output.message(
            output.Subject.ERROR,
            f'{error.message}',
            True
        )
    if errors:
        raise ValidationError('Configuration validation failed')
