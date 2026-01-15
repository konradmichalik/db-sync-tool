"""Tests for db-sync-tool sync modes (RECEIVER, SENDER, PROXY, SYNC_LOCAL, SYNC_REMOTE)."""
import pytest
from conftest import get_row_count, CONFIGS


@pytest.mark.integration
def test_receiver_mode(run_sync):
    """RECEIVER: remote origin -> local target."""
    result = run_sync("www2", f"{CONFIGS}/receiver/sync-www1-to-local.json")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_sender_mode(run_sync):
    """SENDER: local origin -> remote target."""
    result = run_sync("www2", f"{CONFIGS}/sender/sync-local-to-www1.json")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db1", "person") == 3


@pytest.mark.integration
def test_proxy_mode(run_sync):
    """PROXY: remote origin -> proxy -> remote target."""
    result = run_sync("proxy", f"{CONFIGS}/proxy/sync-www1-to-www2.json")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_sync_local(run_sync):
    """SYNC_LOCAL: same host, different databases."""
    result = run_sync("www2", f"{CONFIGS}/sync_local/sync-local-to-local.json")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db2", "person") == 3


@pytest.mark.integration
def test_sync_remote(run_sync):
    """SYNC_REMOTE: same remote host sync."""
    result = run_sync("www1", f"{CONFIGS}/sync_remote/sync-www2-to-www2.json")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db1", "person") == 3


@pytest.mark.integration
def test_sync_remote_manual(run_sync):
    """SYNC_REMOTE with manual credentials."""
    result = run_sync("www1", f"{CONFIGS}/sync_remote_manual/sync-www2-to-www2.json")
    assert result.returncode == 0, result.stderr
    assert get_row_count("db1", "person") == 3
