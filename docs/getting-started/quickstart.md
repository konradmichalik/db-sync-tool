# Quick Start

This guide shows how to sync databases without using automatic credential detection from a framework.

## Command Line

Most sync features can be declared via command line arguments. Here's an example for [receiver mode](/reference/sync-modes#receiver):

```bash
db_sync_tool \
    --origin-host <ORIGIN_HOST> \
    --origin-user <ORIGIN_USER> \
    --origin-db-name <ORIGIN_DB_NAME> \
    --origin-db-user <ORIGIN_DB_USER> \
    --origin-db-password <ORIGIN_DB_PASSWORD> \
    --target-db-name <TARGET_DB_NAME> \
    --target-db-user <TARGET_DB_USER> \
    --target-db-password <TARGET_DB_PASSWORD>
```

## Configuration File

For reusability, create a configuration file with all sync details.

### Using YAML (Recommended)

```bash
db_sync_tool -f config.yaml
```

```yaml
# config.yaml
target:
  db:
    name: local_db
    host: localhost
    user: db_user
    password: db_password
origin:
  host: remote.example.com
  user: ssh_user
  db:
    name: remote_db
    host: localhost
    user: db_user
    password: db_password
```

### Using JSON

```bash
db_sync_tool -f config.json
```

```json
{
  "target": {
    "db": {
      "name": "local_db",
      "host": "localhost",
      "user": "db_user",
      "password": "db_password"
    }
  },
  "origin": {
    "host": "remote.example.com",
    "user": "ssh_user",
    "db": {
      "name": "remote_db",
      "host": "localhost",
      "user": "db_user",
      "password": "db_password"
    }
  }
}
```

## Auto-Discovery

For faster workflows, use [auto-discovery configuration](/configuration/auto-discovery):

```bash
# Define hosts in ~/.db-sync-tool/hosts.yaml
# Then sync with just:
db_sync_tool production local
```

## Common Options

| Option | Short | Description |
|--------|-------|-------------|
| `--config-file` | `-f` | Path to configuration file |
| `--verbose` | `-v` | Enable verbose output |
| `--dry-run` | `-dr` | Test without making changes |
| `--yes` | `-y` | Skip confirmation prompts |

See [CLI Reference](/reference/cli) for all options.

## Next Steps

- [TYPO3 Guide](/getting-started/typo3) - Sync TYPO3 databases
- [Configuration](/configuration/) - Full configuration options
- [Sync Modes](/reference/sync-modes) - Learn about different sync modes
