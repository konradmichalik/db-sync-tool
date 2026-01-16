"""Pytest fixtures for unit tests.

Unit tests don't require Docker - they test isolated functions.
This conftest.py overrides the parent fixtures to avoid Docker dependency.
"""
import pytest


# Override docker_up fixture to do nothing for unit tests
@pytest.fixture(scope="session")
def docker_up():
    """No-op fixture for unit tests - Docker not needed."""
    yield


# Override reset_test_state fixture to do nothing for unit tests
@pytest.fixture(autouse=True)
def reset_test_state(docker_up):
    """No-op fixture for unit tests - no state to reset."""
    yield


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
