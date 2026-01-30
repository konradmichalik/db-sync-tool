# WordPress

db-sync-tool can automatically detect database credentials from [WordPress](https://wordpress.org) applications (>= v5.0).

## Configuration File

The tool parses the `wp-config.php` file which contains the database credentials.

See the [WordPress documentation](https://wordpress.org/support/article/editing-wp-config-php/) for more information.

## Command Line

Example for [receiver mode](/reference/sync-modes#receiver):

```bash
db_sync_tool \
    --type WordPress \
    --origin-host <ORIGIN_HOST> \
    --origin-user <ORIGIN_USER> \
    --origin-path <ORIGIN_PATH> \
    --target-path <TARGET_PATH>
```

## Example Configuration

```yaml
# config.yaml
type: WordPress
target:
  path: /var/www/local/wordpress/wp-config.php
origin:
  host: prod.example.com
  user: ssh_user
  path: /var/www/html/wordpress/wp-config.php
```

## Complete Example

```yaml
type: WordPress
target:
  path: /var/www/local/wordpress/wp-config.php
origin:
  host: 192.87.33.123
  user: ssh_demo_user
  path: /var/www/html/wordpress/wp-config.php
  name: Production
ignore_table:
  - wp_options
  - wp_sessions
```

## wp-config.php Format

The tool parses standard WordPress configuration constants:

```php
define( 'DB_NAME', 'database_name' );
define( 'DB_USER', 'database_user' );
define( 'DB_PASSWORD', 'database_password' );
define( 'DB_HOST', 'localhost' );
```

## Next Steps

- [Configuration Reference](/configuration/reference) - All configuration options
- [Sync Modes](/reference/sync-modes) - Different synchronization modes
