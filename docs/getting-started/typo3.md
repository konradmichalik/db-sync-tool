# TYPO3

db-sync-tool can automatically detect database credentials from [TYPO3](https://typo3.org/) applications (>= v7.6).

## Configuration Files

The tool supports the following configuration file formats:

| File | TYPO3 Version | Description |
|------|---------------|-------------|
| `LocalConfiguration.php` | v7.6 - v12.x | Standard TYPO3 configuration |
| `settings.php` | v13+ | New location in `config/system/settings.php` |
| `AdditionalConfiguration.php` | v7.6 - v12.x | Override configuration |
| `additional.php` | v13+ | New location in `config/system/additional.php` |
| `.env` | v9+ | Environment-based configuration |

::: tip TYPO3 v13 Changes
In TYPO3 v13, configuration files were relocated:
- `typo3conf/LocalConfiguration.php` → `config/system/settings.php`
- `typo3conf/AdditionalConfiguration.php` → `config/system/additional.php`

Both old and new paths are supported.

**Important:** When using `settings.php`, you must specify `type: TYPO3` explicitly in your config, as the filename is also used by Drupal.
:::

See the [TYPO3 documentation](https://docs.typo3.org/m/typo3/reference-coreapi/main/en-us/Configuration/ConfigurationFiles/Index.html) for more information.

## Command Line

Example for [receiver mode](/reference/sync-modes#receiver):

```bash
db_sync_tool \
    --type TYPO3 \
    --origin-host <ORIGIN_HOST> \
    --origin-user <ORIGIN_USER> \
    --origin-path <ORIGIN_PATH> \
    --target-path <TARGET_PATH>
```

## Configuration File

### TYPO3 v7.6 - v12.x

```yaml
# config.yaml
type: TYPO3
target:
  path: /var/www/html/typo3conf/LocalConfiguration.php
origin:
  host: prod.example.com
  user: ssh_user
  path: /var/www/html/shared/typo3conf/LocalConfiguration.php
```

### TYPO3 v13+

```yaml
# config.yaml
type: TYPO3
target:
  path: /var/www/html/config/system/settings.php
origin:
  host: prod.example.com
  user: ssh_user
  path: /var/www/html/shared/config/system/settings.php
```

## Complete Example

```yaml
type: TYPO3
target:
  path: /var/www/html/htdocs/typo3/web/typo3conf/LocalConfiguration.php
origin:
  host: 192.87.33.123
  user: ssh_demo_user
  path: /var/www/html/shared/typo3conf/LocalConfiguration.php
  name: Demo Prod
ignore_table:
  - be_users
  - sys_domain
  - cf_cache_*
```

## .env Support

Alternatively, credentials can be parsed from a `.env` file. Point the `path` to a `.env` file:

### Default Environment Variables

```dotenv
TYPO3_CONF_VARS__DB__Connections__Default__host=db
TYPO3_CONF_VARS__DB__Connections__Default__port=3306
TYPO3_CONF_VARS__DB__Connections__Default__password=db
TYPO3_CONF_VARS__DB__Connections__Default__user=db
TYPO3_CONF_VARS__DB__Connections__Default__dbname=db
```

### Custom Environment Variables

If your `.env` uses different keys, map them in the configuration:

```yaml
type: TYPO3
target:
  path: /var/www/html/.env
origin:
  name: Demo Prod
  host: 123.456.78.90
  user: ssh_demo_user
  path: /var/www/html/shared/.env
  db:
    name: TYPO3_DB_NAME
    host: TYPO3_DB_HOST
    user: TYPO3_DB_USER
    password: TYPO3_DB_PASSWORD
ignore_table:
  - cf_cache_*
```

## Common Ignore Tables

TYPO3 projects often exclude cache and log tables:

```yaml
ignore_table:
  - cache_*
  - cf_*
  - sys_log
  - sys_history
  - be_sessions
  - fe_sessions
```

## Next Steps

- [Configuration Reference](/configuration/reference) - All configuration options
- [Advanced Options](/configuration/advanced) - Scripts, logging, cleanup
