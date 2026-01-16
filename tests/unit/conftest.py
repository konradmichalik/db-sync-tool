"""Pytest fixtures for unit tests.

Unit tests don't require Docker - they test isolated functions.
"""
import pytest


@pytest.fixture
def mock_config():
    """Provide a minimal mock configuration for testing."""
    return {
        'verbose': False,
        'dry_run': False,
        'origin': {
            'db': {
                'name': 'test_db',
                'user': 'test_user',
                'password': 'test_password',
                'host': 'localhost',
                'port': 3306
            }
        },
        'target': {
            'db': {
                'name': 'target_db',
                'user': 'target_user',
                'password': 'target_password',
                'host': 'localhost',
                'port': 3306
            }
        }
    }
