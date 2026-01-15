# Tests

## Quick Start

```bash
cd tests
./run_tests.sh
```

With options:
```bash
./run_tests.sh -v                    # verbose
./run_tests.sh test_sync_modes.py    # single file
./run_tests.sh -k "typo3"            # by name
```

## Structure

```
tests/
├── configs/         # Sync configurations (40 scenarios)
├── docker/          # Docker infrastructure
├── fixtures/        # Framework configs (www1/, www2/)
├── test_*.py        # pytest tests
└── run_tests.sh     # Test runner
```

## Test Files

| File | Tests |
|------|-------|
| `test_sync_modes.py` | RECEIVER, SENDER, PROXY, SYNC_LOCAL, SYNC_REMOTE |
| `test_frameworks.py` | TYPO3, Symfony, WordPress, Laravel, Drupal |
| `test_features.py` | truncate, rsync, hosts, jump_host, etc. |
| `test_import_dump.py` | DUMP_LOCAL, DUMP_REMOTE, IMPORT_LOCAL, IMPORT_REMOTE |
| `test_special.py` | scripts, logging, shell mode, cleanup |

## Architecture

```
www1 (db1) ←─SSH─→ www2 (db2)
               ↑
             proxy
```
