# Configuration

db-sync-tool can be configured via command line arguments or configuration files (YAML or JSON).

## Configuration Methods

| Method | Best For |
|--------|----------|
| [Auto-Discovery](/configuration/auto-discovery) | Quick, repeated syncs with predefined hosts |
| [Config Files](/configuration/reference) | Complex setups, CI/CD pipelines |
| [CLI Arguments](/reference/cli) | One-off syncs, scripting |

## Quick Example

### Using a Config File

```yaml
# config.yaml
type: TYPO3
origin:
  host: prod.example.com
  user: deploy
  path: /var/www/html/typo3conf/LocalConfiguration.php
target:
  path: /var/www/local/typo3conf/LocalConfiguration.php
ignore_table:
  - cache_*
  - sys_log
```

```bash
db_sync_tool -f config.yaml
```

### Using Auto-Discovery

```bash
# With global hosts configured
db_sync_tool production local

# Interactive selection
db_sync_tool
```

### Using CLI Arguments

```bash
db_sync_tool \
    --type TYPO3 \
    --origin-host prod.example.com \
    --origin-user deploy \
    --origin-path /var/www/html/typo3conf/LocalConfiguration.php \
    --target-path /var/www/local/typo3conf/LocalConfiguration.php
```

## Key Configuration Sections

### Origin & Target

Every sync requires an **origin** (source) and **target** (destination):

```yaml
origin:
  host: remote.example.com  # SSH host (makes this remote)
  user: ssh_user           # SSH user
  path: /path/to/config    # Framework config path
target:
  path: /local/path/to/config  # No host = local
```

### Framework Type

Specify the framework for automatic credential extraction:

```yaml
type: TYPO3  # or SYMFONY, DRUPAL, WORDPRESS, LARAVEL
```

If omitted, the tool attempts to detect the framework from the file path.

### Ignore Tables

Exclude tables from the sync (supports wildcards):

```yaml
ignore_table:
  - cache_*
  - sessions
  - logs
```

### Truncate Tables

Clear tables before import:

```yaml
truncate_table:
  - user_sessions
```

## Next Steps

- [Auto-Discovery](/configuration/auto-discovery) - Set up quick syncs
- [Full Reference](/configuration/reference) - All configuration options
- [Authentication](/configuration/authentication) - SSH keys and passwords
