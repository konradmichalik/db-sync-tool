"""Tests for db-sync-tool file transfer feature."""
import pytest
from conftest import (
    CONFIGS, FIXTURES, get_row_count, exec_in_container,
    file_exists_in_container, dir_exists_in_container, file_content_in_container
)

# Test paths
FILEADMIN_WWW2 = f"{FIXTURES}/www2/fileadmin"
CONFIG_FILE = f"{CONFIGS}/files/sync-with-files.yml"


@pytest.mark.integration
def test_with_files_flag(run_sync):
    """Test --with-files transfers files along with database."""
    result = run_sync("www2", CONFIG_FILE, ["--with-files"])
    assert result.returncode == 0, f"Sync failed: {result.stderr}"

    assert get_row_count("db2", "person") == 3
    assert file_exists_in_container("www2", f"{FILEADMIN_WWW2}/test1.txt")
    assert file_exists_in_container("www2", f"{FILEADMIN_WWW2}/test2.txt")


@pytest.mark.integration
def test_files_only_flag(run_sync):
    """Test --files-only transfers only files, no database."""
    exec_in_container("db2", ["mariadb", "-udb", "-pdb", "db", "-e", "DELETE FROM person WHERE id > 1"])
    assert get_row_count("db2", "person") == 1

    result = run_sync("www2", CONFIG_FILE, ["--files-only"])
    assert result.returncode == 0, f"Sync failed: {result.stderr}"

    assert get_row_count("db2", "person") == 1, "Database should not be touched"
    assert file_exists_in_container("www2", f"{FILEADMIN_WWW2}/test1.txt")


@pytest.mark.integration
def test_without_files_flag(run_sync):
    """Test that without --with-files, files are NOT transferred."""
    result = run_sync("www2", CONFIG_FILE)
    assert result.returncode == 0, f"Sync failed: {result.stderr}"

    assert get_row_count("db2", "person") == 3
    assert not file_exists_in_container("www2", f"{FILEADMIN_WWW2}/test1.txt")


@pytest.mark.integration
def test_files_exclude_patterns(run_sync):
    """Test exclude patterns in file transfer config."""
    result = run_sync("www2", CONFIG_FILE, ["--with-files"])
    assert result.returncode == 0, f"Sync failed: {result.stderr}"

    assert file_exists_in_container("www2", f"{FILEADMIN_WWW2}/test1.txt")
    assert not dir_exists_in_container("www2", f"{FILEADMIN_WWW2}/_processed_")
    assert not dir_exists_in_container("www2", f"{FILEADMIN_WWW2}/_temp_")


@pytest.mark.integration
def test_file_content_preserved(run_sync):
    """Test that file content is correctly transferred."""
    result = run_sync("www2", CONFIG_FILE, ["--with-files"])
    assert result.returncode == 0, f"Sync failed: {result.stderr}"

    content = file_content_in_container("www2", f"{FILEADMIN_WWW2}/test1.txt")
    assert "Test file 1 for file transfer" in content
