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

## Origin Client Options

| Option | Short | Description |
|--------|-------|-------------|
| `--origin-host` | `-oh` | SSH host to origin system |
| `--origin-user` | `-ou` | SSH user for origin system |
| `--origin-path` | `-op` | Path to database credential file |
| `--origin-db-name` | `-odn` | Database name for origin system |
| `--origin-db-host` | `-odh` | Database host for origin system |
| `--origin-db-user` | `-odu` | Database user for origin system |
| `--origin-db-password` | `-odp` | Database password for origin system |

## Target Client Options

| Option | Short | Description |
|--------|-------|-------------|
| `--target-host` | `-th` | SSH host to target system |
| `--target-user` | `-tu` | SSH user for target system |
| `--target-path` | `-tp` | Path to database credential file |
| `--target-db-name` | `-tdn` | Database name for target system |
| `--target-db-host` | `-tdh` | Database host for target system |
| `--target-db-user` | `-tdu` | Database user for target system |
| `--target-db-password` | `-tdp` | Database password for target system |

## Other Options

| Option | Description |
|--------|-------------|
| `--type` | Framework type: `TYPO3`, `SYMFONY`, `DRUPAL`, `WORDPRESS`, `LARAVEL` |
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

### CI/CD Mode (No Prompts)

```bash
db_sync_tool -f config.yaml -y --output=ci
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
