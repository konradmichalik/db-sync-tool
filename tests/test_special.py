"""Tests for special features (scripts, logging, shell mode, cleanup)."""
import subprocess
import pytest
from conftest import get_row_count, file_exists_local, exec_in_container, TESTS_DIR, DOCKER_COMPOSE, CONFIGS


@pytest.mark.integration
def test_scripts_execution(run_sync):
    """Execute pre/post scripts at global, origin, and target levels."""
    result = run_sync("www2", f"{CONFIGS}/scripts/sync-www1-to-local.json")

    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 4  # 3 + 1 from script INSERT

    # Check marker files
    for www in ["www1", "www2"]:
        assert file_exists_local(f"fixtures/{www}/before_script.txt")
        assert file_exists_local(f"fixtures/{www}/after_script.txt")
    assert file_exists_local("fixtures/www1/before_script_global.txt")
    assert file_exists_local("fixtures/www1/after_script_global.txt")


@pytest.mark.integration
def test_logging(run_sync):
    """Create log file at specified path."""
    result = run_sync("www2", f"{CONFIGS}/logging/sync-www1-to-local.json")
    assert result.returncode == 0, result.stderr
    assert file_exists_local("fixtures/test.log")


@pytest.mark.integration
def test_shell_arguments():
    """Sync using shell arguments instead of config file."""
    result = exec_in_container("www2", [
        "sh", "-c",
        "cd /var/www/html && PYTHONPATH=/var/www/html python3 -m db_sync_tool "
        "--type TYPO3 "
        "--target-path /var/www/html/tests/fixtures/www2/LocalConfiguration.php "
        "--origin-path /var/www/html/tests/fixtures/www1/LocalConfiguration.php "
        "--origin-host www1 --origin-user user --origin-password password -y -m"
    ])
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_keep_dump(run_sync):
    """Keep dump file locally with -kd flag."""
    result = run_sync("www2", f"{CONFIGS}/download/sync-www1-to-local.json",
                      ["-kd", "/var/www/html/tests/fixtures/www2/download/", "-dn", "dump"])
    assert result.returncode == 0, result.stderr
    assert file_exists_local("fixtures/www2/download/dump.sql")


@pytest.mark.integration
def test_cleanup_old_backups(run_sync):
    """Clean up old backup files based on keep_dumps setting."""
    # Setup: Create dummy backup files
    backup_dir = TESTS_DIR / "fixtures" / "www1" / "database_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for i in range(1, 6):
        (backup_dir / f"{i}.sql").touch()

    result = run_sync("www2", f"{CONFIGS}/cleanup/dump-www1-from-local.json", ["-dn", "test"])

    assert result.returncode == 0, result.stderr
    assert not file_exists_local("fixtures/www1/database_backup/1.sql")  # Oldest removed
