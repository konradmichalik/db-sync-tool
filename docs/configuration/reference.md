# Configuration Reference

Complete reference for `config.yaml` (or `config.json`).

## Full Configuration

```yaml
# Application type: TYPO3 | Symfony | Drupal | WordPress | Laravel
# Not necessary if database credentials are provided manually
type:

# Database source system
origin:
  # Informative name for logging (e.g., "prod")
  name:
  # Path to framework config file with database credentials
  path:
  # Link to host definition (e.g., "@prod")
  link:
  # SSH host (presence makes this a remote system)
  host:
  # SSH user
  user:
  # SSH port (default: 22)
  port:
  # SSH password (not recommended - use ssh_key or agent)
  password:
  # Path to SSH private key
  ssh_key:
  # SSH jump host configuration
  jump_host:
    host:      # Public IP/hostname
    private:   # Private IP (for session channel)
    user:      # SSH user (default: parent user)
    port:      # SSH port (default: parent port)
    name:      # Informative name
  # Directory for temporary dump files (default: /tmp/)
  dump_dir:
  # Manual database credentials
  db:
    name:      # Database name
    host:      # Database host
    password:  # Database password
    user:      # Database user
    port:      # Database port (default: 3306)
  # Scripts to run
  script:
    before:    # Before sync on origin
    after:     # After sync on origin
    error:     # On error
  # Custom command paths
  console:
    php: /usr/bin/php
    mysql: /usr/bin/mysql
    mysqldump: /usr/bin/mysqldump

# Database target system (same structure as origin)
target:
  name:
  path:
  link:
  host:
  user:
  port:
  password:
  ssh_key:
  jump_host:
    host:
    private:
    user:
    port:
    name:
  dump_dir:
  # Protect against accidental imports
  protect: true
  db:
    name:
    host:
    password:
    user:
    port:
  script:
    before:
    after:
    error:
  console:
  # Cleanup: keep only N most recent dumps
  keep_dumps:
  # Additional SQL file to import after sync
  after_dump:
  # SQL commands to run after import
  post_sql:
    -

# Path to log file
log_file:

# Tables to exclude from dump (supports wildcards)
ignore_table: []

# Tables to truncate before import (supports wildcards)
truncate_table: []

# Verify dump completeness (default: true)
check_dump:

# Global scripts
script:
  before:
  after:
  error:
```

## Common Configurations

### Receiver Mode (Remote → Local)

```yaml
type: TYPO3
origin:
  host: prod.example.com
  user: deploy
  path: /var/www/html/typo3conf/LocalConfiguration.php
target:
  path: /var/www/local/typo3conf/LocalConfiguration.php
```

### Sender Mode (Local → Remote)

```yaml
type: TYPO3
origin:
  path: /var/www/local/typo3conf/LocalConfiguration.php
target:
  host: staging.example.com
  user: deploy
  path: /var/www/html/typo3conf/LocalConfiguration.php
```

### Proxy Mode (Remote → Remote)

```yaml
type: TYPO3
origin:
  host: prod.example.com
  user: deploy
  path: /var/www/html/typo3conf/LocalConfiguration.php
target:
  host: staging.example.com
  user: deploy
  path: /var/www/html/typo3conf/LocalConfiguration.php
```

### Manual Database Credentials

```yaml
origin:
  host: prod.example.com
  user: deploy
  db:
    name: production_db
    host: localhost
    user: db_user
    password: db_password
    port: 3306
target:
  db:
    name: local_db
    host: localhost
    user: root
    password: root
```

## Table Filtering

### Ignore Tables

Exclude tables from the dump:

```yaml
ignore_table:
  - cache_*        # Wildcard pattern
  - sys_log
  - be_sessions
  - fe_sessions
```

### Truncate Tables

Clear tables before import (useful for session tables):

```yaml
truncate_table:
  - sessions
  - cache_pages
```

## File Formats

Configuration files can be written in YAML or JSON:

::: code-group

```yaml [config.yaml]
type: TYPO3
origin:
  host: prod.example.com
  user: deploy
  path: /var/www/html/LocalConfiguration.php
target:
  path: /var/www/local/LocalConfiguration.php
```

```json [config.json]
{
  "type": "TYPO3",
  "origin": {
    "host": "prod.example.com",
    "user": "deploy",
    "path": "/var/www/html/LocalConfiguration.php"
  },
  "target": {
    "path": "/var/www/local/LocalConfiguration.php"
  }
}
```

:::
