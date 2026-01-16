"""Tests for db-sync-tool features."""
import pytest
from conftest import get_row_count, exec_in_container, CONFIGS


@pytest.mark.integration
def test_truncate_tables(run_sync):
    """Truncate tables before import using wildcard pattern."""
    result = run_sync("www2", f"{CONFIGS}/truncate/sync-www1-to-local.yml")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_specific_tables(run_sync):
    """Sync only specific tables with -ta flag."""
    result = run_sync("www2", f"{CONFIGS}/tables/sync-www1-to-local.json", ["-ta", "person"])
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_post_sql(run_sync):
    """Execute SQL after import (deletes one row)."""
    result = run_sync("www2", f"{CONFIGS}/post_sql/sync-www1-to-local.yml")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 2


@pytest.mark.integration
def test_manual_credentials(run_sync):
    """Sync with manually specified database credentials."""
    result = run_sync("www2", f"{CONFIGS}/manual/sync-www1-to-local.json")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_yaml_config(run_sync):
    """Sync with YAML configuration file."""
    result = run_sync("www2", f"{CONFIGS}/yaml/sync-www1-to-local.yml")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_reverse_direction(run_sync):
    """Reverse sync direction with --reverse flag."""
    result = run_sync("www2", f"{CONFIGS}/reverse/sync-www1-to-local.yml", ["--reverse"])
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_rsync_transfer(run_sync):
    """Use rsync for file transfer instead of SFTP."""
    result = run_sync("www2", f"{CONFIGS}/rsync/sync-www1-to-local.json", ["--use-rsync"])
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_external_hosts_file(run_sync):
    """Use external hosts.json file for host definitions."""
    result = run_sync("proxy", f"{CONFIGS}/link/sync-www1-to-www2.json",
                      ["-o", f"{CONFIGS}/link/hosts.json"])
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_inline_hosts(run_sync):
    """Use inline hosts.yaml with named references."""
    result = run_sync("proxy", f"{CONFIGS}/link_inline/sync-www1-to-www2.yaml")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_named_hosts():
    """Use hosts.json with host names as positional arguments."""
    result = exec_in_container("proxy", [
        "sh", "-c",
        f"cd /var/www/html && PYTHONPATH=/var/www/html python3 -m db_sync_tool "
        f"-y -m -o {CONFIGS}/link/hosts.json www1 www2 -t TYPO3"
    ])
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_config_overwrite(run_sync):
    """Override configuration via --origin-path argument."""
    result = run_sync("www2", f"{CONFIGS}/overwrite/sync-www1-to-local.yml",
                      ["--origin-path", "/var/www/html/tests/fixtures/www1/LocalConfiguration.php"])
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_jump_host(run_sync):
    """Connect via SSH jump host."""
    result = run_sync("www2", f"{CONFIGS}/jump_host/sync-www1-to-local.json")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_mysqldump_options(run_sync):
    """Pass options to mysqldump."""
    result = run_sync("www2", f"{CONFIGS}/mysqldump_options/sync-www1-to-local.json")
    assert result.returncode == 0, result.stderr


@pytest.mark.integration
def test_where_clause(run_sync):
    """Filter data with WHERE clause."""
    result = run_sync("www2", f"{CONFIGS}/where/sync-www1-to-local.json")
    assert result.returncode == 0, result.stderr
