"""Tests for framework credential parsing (TYPO3, Symfony, WordPress, Laravel, Drupal)."""
import pytest
from conftest import get_row_count, CONFIGS


# TYPO3

@pytest.mark.integration
def test_typo3_env(run_sync):
    """TYPO3 with .env configuration."""
    result = run_sync("www2", f"{CONFIGS}/typo3_env/sync-www1-to-local.json")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_typo3_env_alternate(run_sync):
    """TYPO3 with alternate .env file."""
    result = run_sync("www2", f"{CONFIGS}/typo3-2_env/sync-www1-to-local.json")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_typo3_additional_config(run_sync):
    """TYPO3 with AdditionalConfiguration.php."""
    result = run_sync("www2", f"{CONFIGS}/typo3_additional/sync-www1-to-local.json")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_typo3_v7_legacy(run_sync):
    """TYPO3 v7 legacy format."""
    result = run_sync("www2", f"{CONFIGS}/typo3v7/sync-www1-to-local.json")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


# Symfony

@pytest.mark.integration
def test_symfony(run_sync):
    """Symfony with parameters.yml."""
    result = run_sync("www2", f"{CONFIGS}/symfony/sync-www1-to-local.json")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_symfony_28(run_sync):
    """Symfony 2.8 legacy format."""
    result = run_sync("www2", f"{CONFIGS}/symfony2.8/sync-www1-to-local.json")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


# WordPress

@pytest.mark.integration
def test_wordpress(run_sync):
    """WordPress with wp-config.php."""
    result = run_sync("www2", f"{CONFIGS}/wordpress/sync-www1-to-local.json")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


# Laravel

@pytest.mark.integration
def test_laravel(run_sync):
    """Laravel with .env."""
    result = run_sync("www2", f"{CONFIGS}/laravel/sync-www1-to-local.json")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


# Drupal

@pytest.mark.integration
def test_drupal(run_sync):
    """Drupal with settings.php (direct parsing)."""
    result = run_sync("www2", f"{CONFIGS}/drupal/sync-www1-to-local.json")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3
