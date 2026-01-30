# Laravel

db-sync-tool can automatically detect database credentials from [Laravel](https://laravel.com/) applications (>= v4.0).

## Configuration File

The tool parses the `.env` file which contains the database credentials.

## Command Line

Example for [receiver mode](/reference/sync-modes#receiver):

```bash
db_sync_tool \
    --type Laravel \
    --origin-host <ORIGIN_HOST> \
    --origin-user <ORIGIN_USER> \
    --origin-path <ORIGIN_PATH> \
    --target-path <TARGET_PATH>
```

## Configuration File

```yaml
# config.yaml
type: Laravel
target:
  path: /var/www/local/laravel/.env
origin:
  host: prod.example.com
  user: ssh_user
  path: /var/www/html/laravel/.env
```

## Complete Example

```yaml
type: Laravel
target:
  path: /var/www/local/laravel/.env
origin:
  host: 192.87.33.123
  user: ssh_demo_user
  path: /var/www/html/laravel/.env
  name: Production
ignore_table:
  - jobs
  - failed_jobs
  - sessions
```

## .env Format

The tool parses standard Laravel environment variables:

```dotenv
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=laravel
DB_USERNAME=root
DB_PASSWORD=secret
```

## Common Ignore Tables

Laravel projects often exclude job and session tables:

```yaml
ignore_table:
  - jobs
  - failed_jobs
  - sessions
  - cache
  - cache_locks
```

## Next Steps

- [Configuration Reference](/configuration/reference) - All configuration options
- [Sync Modes](/reference/sync-modes) - Different synchronization modes
