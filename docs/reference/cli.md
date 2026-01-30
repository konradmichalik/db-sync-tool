# CLI Reference

Complete command line reference for db-sync-tool.

## Basic Usage

```bash
db_sync_tool [OPTIONS] [ORIGIN] [TARGET]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `ORIGIN` | Origin database defined in host file or auto-discovery |
| `TARGET` | Target database defined in host file or auto-discovery |

## Configuration Options

| Option | Short | Description |
|--------|-------|-------------|
| `--config-file` | `-f` | Path to configuration file |
| `--host-file` | `-o` | Using an additional hosts file |
| `--log-file` | `-l` | File path for creating an additional log file |
| `--json-log` | `-jl` | Use JSON format for log file output (structured logging) |

## Output Options

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Enable verbose output (`-v`) or debug (`-vv`) |
| `--mute` | `-m` | Mute console output |
| `--quiet` | `-q` | Suppress all output except errors |
| `--output` | | Output format: `interactive`, `ci`, `json`, `quiet` |

## Execution Options

| Option | Short | Description |
|--------|-------|-------------|
| `--yes` | `-y` | Skip user confirmation for database import |
| `--dry-run` | `-dr` | Testing without running export, transfer, or import |
| `--reverse` | `-r` | Reverse origin and target hosts |
| `--force-password` | `-fpw` | Force password user query |

## Database Dump Options

| Option | Short | Description |
|--------|-------|-------------|
| `--import-file` | `-i` | Import database from a specific file dump |
| `--dump-name` | `-dn` | Set a specific dump file name |
| `--keep-dump` | `-kd` | Skip import and save dump in the given directory |
| `--clear-database` | `-cd` | Drop all tables before importing |
| `--tables` | `-ta` | Specific tables to export (e.g., `--tables=t1,t2`) |
| `--where` | `-w` | WHERE clause for partial sync |
| `--additional-mysqldump-options` | `-amo` | Additional mysqldump options |

## Framework Options

| Option | Short | Description |
|--------|-------|-------------|
| `--type` | `-t` | Framework type: `TYPO3`, `Symfony`, `Drupal`, `WordPress`, `Laravel` |

## Transfer Options

| Option | Short | Description |
|--------|-------|-------------|
| `--use-rsync` | `-ur` | Use rsync as transfer method |
| `--use-rsync-options` | `-uro` | Additional rsync options |

## File Transfer Options

| Option | Short | Description |
|--------|-------|-------------|
| `--with-files` | `-wf` | Enable file synchronization (requires 'files' section in config) |
| `--files-only` | `-fo` | Sync only files, skip database synchronization |

## Origin Client Options

| Option | Short | Description |
|--------|-------|-------------|
| `--origin-path` | `-op` | Path to database credential file |
| `--origin-name` | `-on` | Providing a name for the origin system |
| `--origin-host` | `-oh` | SSH host to origin system |
| `--origin-user` | `-ou` | SSH user for origin system |
| `--origin-password` | `-opw` | SSH password for origin system |
| `--origin-key` | `-ok` | File path to SSH key for origin system |
| `--origin-port` | `-opo` | SSH port for origin system |
| `--origin-dump-dir` | `-odd` | Directory path for database dump file on origin |
| `--origin-keep-dumps` | `-okd` | Keep dump file count for origin system |

## Origin Database Options

| Option | Short | Description |
|--------|-------|-------------|
| `--origin-db-name` | `-odn` | Database name for origin system |
| `--origin-db-host` | `-odh` | Database host for origin system |
| `--origin-db-user` | `-odu` | Database user for origin system |
| `--origin-db-password` | `-odpw` | Database password for origin system |
| `--origin-db-port` | `-odpo` | Database port for origin system |

## Target Client Options

| Option | Short | Description |
|--------|-------|-------------|
| `--target-path` | `-tp` | Path to database credential file |
| `--target-name` | `-tn` | Providing a name for the target system |
| `--target-host` | `-th` | SSH host to target system |
| `--target-user` | `-tu` | SSH user for target system |
| `--target-password` | `-tpw` | SSH password for target system |
| `--target-key` | `-tk` | File path to SSH key for target system |
| `--target-port` | `-tpo` | SSH port for target system |
| `--target-dump-dir` | `-tdd` | Directory path for database dump file on target |
| `--target-keep-dumps` | `-tkd` | Keep dump file count for target system |
| `--target-after-dump` | `-tad` | Additional dump file to insert after regular import |

## Target Database Options

| Option | Short | Description |
|--------|-------|-------------|
| `--target-db-name` | `-tdn` | Database name for target system |
| `--target-db-host` | `-tdh` | Database host for target system |
| `--target-db-user` | `-tdu` | Database user for target system |
| `--target-db-password` | `-tdpw` | Database password for target system |
| `--target-db-port` | `-tdpo` | Database port for target system |

## Other Options

| Option | Description |
|--------|-------------|
| `--install-completion` | Install shell completion for the current shell |
| `--show-completion` | Show completion for the current shell |
| `--version` | Show version and exit |
| `--help` | Show help message and exit |

## Examples

### Basic Sync with Config File

```bash
db_sync_tool -f config.yaml
```

### Auto-Discovery with Host Names

```bash
db_sync_tool production local
```

### Verbose Dry Run

```bash
db_sync_tool -f config.yaml -v --dry-run
```

### Skip Confirmation

```bash
db_sync_tool -f config.yaml -y
```

### Import from Dump File

```bash
db_sync_tool -f config.yaml -i /path/to/dump.sql
```

### Keep Dump Without Import

```bash
db_sync_tool -f config.yaml --keep-dump /var/backups/
```

### Sync Specific Tables

```bash
db_sync_tool -f config.yaml --tables=users,orders
```

### Partial Sync with WHERE Clause

```bash
db_sync_tool -f config.yaml --tables=orders --where="created_at > '2024-01-01'"
```

### Reverse Origin and Target

```bash
db_sync_tool -f config.yaml --reverse
```

### Clear Database Before Import

```bash
db_sync_tool -f config.yaml --clear-database
```

### Sync with Files

```bash
db_sync_tool -f config.yaml --with-files
```

### Sync Only Files (Skip Database)

```bash
db_sync_tool -f config.yaml --files-only
```

### Use Rsync Transfer

```bash
db_sync_tool -f config.yaml --use-rsync
```

### CI/CD Mode (No Prompts)

```bash
db_sync_tool -f config.yaml -y --output=ci
```

### JSON Logging

```bash
db_sync_tool -f config.yaml -l /var/log/sync.log --json-log
```

### Debug Mode

```bash
db_sync_tool -f config.yaml -vv
```

## Shell Completion

Install shell completion for your shell:

```bash
# Install
db_sync_tool --install-completion

# Show completion script
db_sync_tool --show-completion
```

Supported shells: bash, zsh, fish, PowerShell

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DB_SYNC_TOOL_CONFIG` | Default config file path |
| `SSH_AUTH_SOCK` | SSH agent socket for key-based auth |

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Connection error |
| 4 | Database error |
