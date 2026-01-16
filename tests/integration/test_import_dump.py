"""Tests for import and dump modes."""
import pytest
from conftest import get_row_count, file_exists_local, exec_in_container, CONFIGS


@pytest.mark.integration
def test_dump_local(run_sync):
    """DUMP_LOCAL: export database locally."""
    result = run_sync("www2", f"{CONFIGS}/dump_local/dump-local.json", ["-dn", "test"])
    assert result.returncode == 0, result.stderr
    assert file_exists_local("fixtures/www2/database_backup/test.sql.gz")


@pytest.mark.integration
def test_dump_remote(run_sync):
    """DUMP_REMOTE: export database from remote."""
    result = run_sync("www2", f"{CONFIGS}/dump_remote/dump-www1-from-local.json", ["-dn", "test"])
    assert result.returncode == 0, result.stderr
    assert file_exists_local("fixtures/www1/database_backup/test.sql.gz")


@pytest.mark.integration
def test_import_local(run_sync):
    """IMPORT_LOCAL: import existing dump locally."""
    # Setup: Copy test dump inside container (avoids permission issues)
    exec_in_container("www2", [
        "sh", "-c",
        "mkdir -p /var/www/html/tests/integration/fixtures/www2/database_backup && "
        "cp /var/www/html/tests/integration/docker/dump/test.sql /var/www/html/tests/integration/fixtures/www2/database_backup/test.sql"
    ])

    result = run_sync("www2", f"{CONFIGS}/import_local/import-local.json",
                      ["-i", "/var/www/html/tests/integration/fixtures/www2/database_backup/test.sql"])
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_import_remote(run_sync):
    """IMPORT_REMOTE: import existing dump to remote."""
    # Setup: Extract test dump inside container (avoids permission issues)
    exec_in_container("www1", [
        "sh", "-c",
        "mkdir -p /var/www/html/tests/integration/fixtures/www1/database_backup && "
        "tar -xzf /var/www/html/tests/integration/docker/dump/test.sql.tar.gz -C /var/www/html/tests/integration/fixtures/www1/database_backup"
    ])

    result = run_sync("www2", f"{CONFIGS}/import_remote/import-www1-from-local.json",
                      ["-i", "/var/www/html/tests/integration/fixtures/www1/database_backup/test.sql"])
    assert result.returncode == 0, result.stderr
    assert get_row_count("db1", "person") == 3
