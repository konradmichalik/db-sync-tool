# Drupal

db-sync-tool can automatically detect database credentials from [Drupal](https://www.drupal.org/) applications (>= v8.0).

## How It Works

The tool uses `drush` to extract database settings from Drupal installations.

See the [Drush documentation](https://www.drush.org/latest/commands/core_status/) for more information.

## Prerequisites

- Drush must be installed and accessible on the system
- PHP CLI available

## Command Line

Example for [receiver mode](/reference/sync-modes#receiver):

```bash
db_sync_tool \
    --type DRUPAL \
    --origin-host <ORIGIN_HOST> \
    --origin-user <ORIGIN_USER> \
    --origin-path <ORIGIN_PATH> \
    --target-path <TARGET_PATH>
```

## Configuration File

Point the `path` to the Drupal installation directory:

```yaml
# config.yaml
type: DRUPAL
target:
  path: /var/www/local/drupal
origin:
  host: prod.example.com
  user: ssh_user
  path: /var/www/html/drupal
```

## Complete Example

```yaml
type: DRUPAL
target:
  path: /var/www/local/drupal
origin:
  host: 192.87.33.123
  user: ssh_demo_user
  path: /var/www/html/drupal
  name: Production
ignore_table:
  - cache_*
  - sessions
  - watchdog
```

## Common Ignore Tables

Drupal projects often exclude cache and session tables:

```yaml
ignore_table:
  - cache_*
  - sessions
  - watchdog
  - flood
```

## Next Steps

- [Configuration Reference](/configuration/reference) - All configuration options
- [Sync Modes](/reference/sync-modes) - Different synchronization modes
