# Symfony

db-sync-tool can automatically detect database credentials from [Symfony](https://symfony.com/) applications (>= v2.8).

## Configuration Files

| Symfony Version | Config File | Documentation |
|-----------------|-------------|---------------|
| >= 3.4 | `.env` | Uses `DATABASE_URL` environment variable |
| <= 2.8 | `parameters.yml` | Uses database parameters |

See the [Doctrine documentation](https://symfony.com/doc/current/doctrine.html) for more information.

## Command Line

Example for [receiver mode](/reference/sync-modes#receiver):

```bash
db_sync_tool \
    --type Symfony \
    --origin-host <ORIGIN_HOST> \
    --origin-user <ORIGIN_USER> \
    --origin-path <ORIGIN_PATH> \
    --target-path <TARGET_PATH>
```

## Configuration File

### Using .env (Symfony >= 3.4)

```yaml
# config.yaml
type: Symfony
target:
  path: /var/www/local/project/.env
origin:
  host: prod.example.com
  user: ssh_user
  path: /var/www/html/project/shared/.env
```

The `.env` file should contain:

```dotenv
DATABASE_URL="mysql://user:password@localhost:3306/dbname"
```

### Using parameters.yml (Symfony <= 2.8)

```yaml
# config.yaml
type: Symfony
target:
  path: /var/www/local/project/app/config/parameters.yml
origin:
  host: prod.example.com
  user: ssh_user
  path: /var/www/html/project/app/config/parameters.yml
```

## Complete Example

```yaml
type: Symfony
target:
  path: /var/www/local/project/.env
origin:
  host: 192.87.33.123
  user: ssh_demo_user
  path: /var/www/html/project/shared/.env
  name: Production
ignore_table:
  - sessions
  - messenger_messages
```

## Next Steps

- [Configuration Reference](/configuration/reference) - All configuration options
- [Sync Modes](/reference/sync-modes) - Different synchronization modes
