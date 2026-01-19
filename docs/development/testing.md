# Testing

db-sync-tool has comprehensive unit and integration tests.

## Quick Start

### Unit Tests (No Docker Required)

```bash
./tests/run-unit-tests.sh
```

Fast (~0.04s), tests security-critical functions in isolation.

### Integration Tests (Docker Required)

```bash
./tests/run-integration-tests.sh
```

Full end-to-end tests with Docker containers.

## Test Options

### Unit Tests

```bash
# Verbose output
./tests/run-unit-tests.sh -v

# With coverage report
./tests/run-unit-tests.sh --cov

# Run specific tests by name
./tests/run-unit-tests.sh -k "injection"

# Run specific test file
./tests/run-unit-tests.sh test_security.py
```

### Integration Tests

```bash
# Verbose output
./tests/run-integration-tests.sh -v

# Run single test file
./tests/run-integration-tests.sh test_sync_modes.py

# Run tests by name pattern
./tests/run-integration-tests.sh -k "typo3"
```

## Test Structure

```text
tests/
├── unit/                    # Unit tests (no Docker)
│   ├── conftest.py
│   ├── test_security.py     # Security functions
│   ├── test_pure.py         # Pure utility functions
│   └── test_config.py       # Configuration dataclasses
│
├── integration/             # Integration tests (Docker)
│   ├── configs/             # Sync configurations (40+ scenarios)
│   ├── docker/              # Docker infrastructure
│   ├── fixtures/            # Framework configs (www1/, www2/)
│   ├── conftest.py
│   ├── test_features.py
│   ├── test_frameworks.py
│   ├── test_import_dump.py
│   ├── test_special.py
│   └── test_sync_modes.py
│
├── run-unit-tests.sh        # Unit test runner
├── run-integration-tests.sh # Integration test runner
└── pytest.ini               # Pytest configuration
```

## Unit Tests

| File | Tests | Purpose |
|------|-------|---------|
| `test_security.py` | 46 | Security-critical functions |
| `test_pure.py` | 38 | Pure utility functions |
| `test_config.py` | 33 | Configuration dataclasses |

### Covered Modules (98% Coverage)

- `utility/security.py` - Command/SQL injection prevention, credential masking
- `utility/pure.py` - Version parsing, path handling, string utilities
- `utility/config.py` - Typed configuration dataclasses

## Integration Tests

| File | Tests | Purpose |
|------|-------|---------|
| `test_sync_modes.py` | 6 | RECEIVER, SENDER, PROXY, SYNC_LOCAL, SYNC_REMOTE |
| `test_frameworks.py` | 8 | TYPO3, Symfony, WordPress, Laravel, Drupal |
| `test_features.py` | 11 | truncate, rsync, hosts, jump_host, etc. |
| `test_import_dump.py` | 4 | DUMP_LOCAL, DUMP_REMOTE, IMPORT_LOCAL, IMPORT_REMOTE |
| `test_special.py` | 5 | scripts, logging, shell mode, cleanup |

## Docker Architecture

```text
www1 (db1) ←─SSH─→ www2 (db2)
               ↑
             proxy
```

| Container | Purpose |
|-----------|---------|
| www1, www2 | Web servers with Python 3.11, SSH, MariaDB client |
| db1, db2 | MariaDB 10.11 databases |
| proxy | Jump host for proxy mode testing |

## CI/CD

GitHub Actions runs:

| Workflow | Description |
|----------|-------------|
| Unit tests | Python 3.10, 3.11, 3.12, 3.13 with coverage |
| Integration tests | Python 3.10-3.13 with Docker |
| Lint | ruff check and format |

## Writing Tests

### Unit Test Example

```python
# tests/unit/test_example.py
import pytest
from db_sync_tool.utility.security import sanitize_table_name

def test_sanitize_valid_table_name():
    assert sanitize_table_name("users") == "users"

def test_sanitize_invalid_characters():
    with pytest.raises(ValueError):
        sanitize_table_name("users; DROP TABLE--")
```

### Integration Test Example

```python
# tests/integration/test_example.py
import pytest

@pytest.mark.integration
def test_receiver_mode(run_sync):
    result = run_sync("receiver/typo3.yaml")
    assert result.returncode == 0
    assert "Import completed" in result.stdout
```

## Running Linter

```bash
# Check for issues
pipx run ruff check db_sync_tool/

# Auto-fix issues
pipx run ruff check db_sync_tool/ --fix

# Format code
pipx run ruff format db_sync_tool/
```
