# Tests

## Quick Start

### Unit Tests (no Docker required)
```bash
./tests/run-unit-tests.sh
```
Fast (~0.04s), tests security-critical functions in isolation.

### Integration Tests (Docker required)
```bash
./tests/run-integration-tests.sh
```
Full end-to-end tests with Docker containers.

### Options
```bash
# Unit tests
./tests/run-unit-tests.sh -v                      # verbose
./tests/run-unit-tests.sh --cov                   # with coverage
./tests/run-unit-tests.sh -k "injection"          # by name

# Integration tests
./tests/run-integration-tests.sh -v               # verbose
./tests/run-integration-tests.sh test_sync_modes.py  # single file
./tests/run-integration-tests.sh -k "typo3"       # by name
```

## Structure

```
tests/
├── unit/                    # Unit tests (no Docker)
│   ├── conftest.py
│   └── test_security.py     # 46 tests
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
│   └── test_sync_modes.py   # 38 tests
│
├── run-unit-tests.sh        # Unit test runner
├── run-integration-tests.sh # Integration test runner
└── pytest.ini               # Pytest configuration
```

## Unit Tests

| File | Tests | Purpose |
|------|-------|---------|
| `test_security.py` | 46 | Security-critical functions |

**Covered functions:**
- `quote_shell_arg()` - Command injection prevention
- `sanitize_table_name()` - SQL injection prevention
- `sanitize_command_for_logging()` - Credential masking

## Integration Tests

| File | Tests | Purpose |
|------|-------|---------|
| `test_sync_modes.py` | 6 | RECEIVER, SENDER, PROXY, SYNC_LOCAL, SYNC_REMOTE |
| `test_frameworks.py` | 8 | TYPO3, Symfony, WordPress, Laravel, Drupal |
| `test_features.py` | 11 | truncate, rsync, hosts, jump_host, etc. |
| `test_import_dump.py` | 4 | DUMP_LOCAL, DUMP_REMOTE, IMPORT_LOCAL, IMPORT_REMOTE |
| `test_special.py` | 5 | scripts, logging, shell mode, cleanup |

## Docker Architecture

```
www1 (db1) ←─SSH─→ www2 (db2)
               ↑
             proxy
```

- **www1/www2**: Web servers with Python 3.11, SSH, MariaDB client
- **db1/db2**: MariaDB 10.11 databases
- **proxy**: Jump host for proxy mode testing

## CI/CD

GitHub Actions runs:
- **Unit tests**: Python 3.10, 3.11, 3.12, 3.13 with coverage (fast, parallel)
- **Integration tests**: Python 3.10-3.13 with Docker (full E2E)
- **Lint**: ruff check and format
