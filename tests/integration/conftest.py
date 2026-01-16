"""pytest fixtures for db-sync-tool integration tests."""
import subprocess
import time
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
DOCKER_COMPOSE = ["docker", "compose", "-f", str(TESTS_DIR / "docker" / "docker-compose.yml")]
CONFIGS = "/var/www/html/tests/configs"


def exec_in_container(container: str, cmd: list[str]) -> subprocess.CompletedProcess:
    """Execute command in Docker container."""
    return subprocess.run(
        DOCKER_COMPOSE + ["exec", "-T", container] + cmd,
        capture_output=True, text=True
    )


def get_row_count(db: str, table: str) -> int:
    """Get row count from database table."""
    result = exec_in_container(db, [
        "mariadb", "-udb", "-pdb", "db", "-N", "-e", f"SELECT COUNT(*) FROM {table}"
    ])
    if result.returncode != 0:
        raise RuntimeError(f"Failed to query {db}: {result.stderr}")
    return int(result.stdout.strip())


def file_exists_local(path: str) -> bool:
    """Check if file exists locally."""
    return (TESTS_DIR / path).exists()


@pytest.fixture(scope="session")
def docker_up():
    """Start Docker containers for test session."""
    print("\n[pytest] Starting Docker containers...")

    for cmd in [["build"], ["up", "-d", "--wait"]]:
        result = subprocess.run(DOCKER_COMPOSE + cmd, capture_output=True, text=True)
        if result.returncode != 0:
            pytest.fail(f"Docker {cmd[0]} failed: {result.stderr}")

    time.sleep(5)  # Wait for MariaDB
    print("[pytest] Docker containers ready")
    yield

    print("\n[pytest] Stopping Docker containers...")
    subprocess.run(DOCKER_COMPOSE + ["down", "-v"], capture_output=True)


@pytest.fixture(autouse=True)
def reset_test_state(docker_up):
    """Reset database and cleanup fixtures before/after each test."""
    def cleanup():
        # Clean up inside containers (handles root-owned files from Docker)
        for container in ["www1", "www2"]:
            exec_in_container(container, [
                "sh", "-c",
                "rm -rf /var/www/html/tests/fixtures/www1/database_backup "
                "/var/www/html/tests/fixtures/www2/database_backup "
                "/var/www/html/tests/fixtures/www1/download "
                "/var/www/html/tests/fixtures/www2/download "
                "/var/www/html/tests/fixtures/www1/before_script*.txt "
                "/var/www/html/tests/fixtures/www1/after_script*.txt "
                "/var/www/html/tests/fixtures/www2/before_script*.txt "
                "/var/www/html/tests/fixtures/www2/after_script*.txt "
                "/var/www/html/tests/fixtures/test.log 2>/dev/null || true"
            ])

    def set_permissions():
        # Set write permissions for SSH user on fixtures directories (needed for CI)
        for container in ["www1", "www2"]:
            exec_in_container(container, [
                "sh", "-c",
                "chmod -R 777 /var/www/html/tests/fixtures/www1 "
                "/var/www/html/tests/fixtures/www2 2>/dev/null || true"
            ])

    # Reset databases
    for db in ["db1", "db2"]:
        exec_in_container(db, [
            "mariadb", "-udb", "-pdb", "db", "-e",
            "DROP TABLE IF EXISTS person; SOURCE /tmp/dump/db.sql;"
        ])

    cleanup()
    set_permissions()
    yield
    cleanup()


@pytest.fixture
def run_sync():
    """Run db_sync_tool in container. Returns CompletedProcess."""
    def _run(container: str, config: str, extra_args: list[str] = None) -> subprocess.CompletedProcess:
        args = f" {' '.join(extra_args)}" if extra_args else ""
        return exec_in_container(container, [
            "sh", "-c",
            f"cd /var/www/html && PYTHONPATH=/var/www/html python3 -m db_sync_tool -f {config} -y -m{args}"
        ])
    return _run
