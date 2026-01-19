# Advanced Options

Advanced configuration options for scripts, logging, cleanup, and more.

## Before and After Scripts

Run custom commands at different stages of the sync process:

```yaml
# Global scripts (run on local system)
script:
  before: echo "Starting sync"
  after: echo "Sync complete"
  error: echo "Sync failed"

# Origin-specific scripts
origin:
  script:
    before: /var/www/scripts/pre-export.sh
    after: /var/www/scripts/post-export.sh
    error: /var/www/scripts/export-error.sh

# Target-specific scripts
target:
  script:
    before: php artisan down
    after: php artisan up && php artisan cache:clear
    error: php artisan up
```

## After Dump Import

Import an additional SQL file after the main sync:

```yaml
target:
  after_dump: /path/to/additional.sql
```

Or execute SQL commands directly:

```yaml
target:
  post_sql:
    - UPDATE sys_domain SET hidden = 1;
    - UPDATE users SET email = CONCAT('test-', email);
```

## Logging

Enable logging to a file:

```yaml
log_file: /var/log/db-sync-tool.log
```

::: tip
By default, only a summary is logged. Use `-v` for detailed logging:
```bash
db_sync_tool -f config.yaml -v
```
:::

## Dump Directory

Change where temporary dump files are stored (default: `/tmp/`):

```yaml
origin:
  dump_dir: /var/backups/db/

target:
  dump_dir: /home/user/dumps/
```

::: warning
Use unique directories per project to avoid conflicts with the cleanup feature.
:::

## Cleanup / Keep Dumps

Automatically clean up old dump files, keeping only the N most recent:

```yaml
origin:
  dump_dir: /var/backups/db/
  keep_dumps: 5  # Keep last 5 dumps
```

::: danger
This deletes all `.sql` and `.tar.gz` files in `dump_dir` except the newest N. Use unique directories per project!
:::

## Check Dump

Verify dump file completeness after creation (enabled by default):

```yaml
check_dump: true  # default
# or
check_dump: false  # disable verification
```

## Linking Hosts

For projects with multiple config files, define hosts once and reference them:

### hosts.yaml

```yaml
prod:
  host: prod.example.com
  user: deploy
  path: /var/www/html/typo3conf/LocalConfiguration.php

staging:
  host: staging.example.com
  user: deploy
  path: /var/www/html/typo3conf/LocalConfiguration.php
```

### config.yaml

```yaml
origin:
  link: "@prod"
target:
  link: "@staging"
```

### Usage

```bash
db_sync_tool -f config.yaml -o hosts.yaml
```

## Protect Host

Prevent accidental imports to critical systems:

```yaml
origin:
  host: prod.example.com
  user: deploy
  path: /var/www/html/LocalConfiguration.php
  protect: true  # Cannot be used as target
```

When attempting to use a protected host as a target, a confirmation is required.

## Reverse Hosts

Quickly swap origin and target:

```bash
db_sync_tool -f config.yaml --reverse
```

This is useful when you normally sync prod → local but occasionally need local → staging.

## Jump Host

Access protected servers through a bastion/jump host:

```yaml
origin:
  host: internal.server.local
  user: app_user
  path: /var/www/html/config.php
  jump_host:
    host: bastion.example.com      # Public IP
    private: 10.0.0.5              # Private IP
    user: bastion_user             # Optional (defaults to origin user)
    port: 22                       # Optional (defaults to origin port)
    name: Bastion Server           # Optional (for logging)
```

The `private` entry is the internal IP address of the jump host, which can be found with:
```bash
hostname -I
# or
ip addr
```

## Console Commands

Specify custom paths for required commands:

```yaml
origin:
  console:
    php: /usr/local/bin/php
    mysql: /usr/local/mysql/bin/mysql
    mysqldump: /usr/local/mysql/bin/mysqldump
```

## SSH Port

Use a non-standard SSH port:

```yaml
origin:
  host: prod.example.com
  user: deploy
  port: 2222  # default: 22
```

## Naming Hosts

Add descriptive names for better logging:

```yaml
origin:
  name: Production
  host: prod.example.com

target:
  name: Local Dev
  path: /var/www/local/config.php
```

## Clear Database

Drop all tables before importing:

```bash
db_sync_tool -f config.yaml --clear-database
```

This ensures a clean sync without leftover tables.
