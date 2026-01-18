# Sync Modes

db-sync-tool supports different synchronization modes depending on the origin (source) and target (destination) configuration. The mode is automatically determined based on the presence of `host` entries.

## Overview

| Mode | Origin | Target | Description |
|------|--------|--------|-------------|
| [Receiver](#receiver) | Remote | Local | Get database from remote system |
| [Sender](#sender) | Local | Remote | Send database to remote system |
| [Proxy](#proxy) | Remote | Remote | Transfer via local proxy |
| [Dump Local](#dump-local) | Local | - | Create local backup |
| [Dump Remote](#dump-remote) | Remote | - | Create remote backup |
| [Import Local](#import-local) | - | Local | Import dump to local |
| [Import Remote](#import-remote) | - | Remote | Import dump to remote |
| [Sync Local](#sync-local) | Local | Local | Sync between local databases |
| [Sync Remote](#sync-remote) | Remote | Remote | Sync within same remote system |

## Receiver {#receiver}

Get a database dump from a remote system (origin) to your local system (target).

**This is the default and most common mode.**

![Sync mode receiver](/images/sm-receiver.png)

### Configuration

Origin has `host`, target does not:

```yaml
origin:
  host: prod.example.com
  user: deploy
  path: /var/www/html/LocalConfiguration.php
target:
  path: /var/www/local/LocalConfiguration.php
```

### Use Cases
- Pulling production data to local development
- Creating local backups of remote databases

## Sender {#sender}

Send a database dump from your local system (origin) to a remote system (target).

![Sync mode sender](/images/sm-sender.png)

### Configuration

Target has `host`, origin does not:

```yaml
origin:
  path: /var/www/local/LocalConfiguration.php
target:
  host: staging.example.com
  user: deploy
  path: /var/www/html/LocalConfiguration.php
```

### Use Cases
- Pushing local data to staging
- Deploying database changes to test environments

::: warning
Be careful when sending to remote systems. Consider using `protect: true` on production hosts.
:::

## Proxy {#proxy}

Transfer a database between two remote systems using your local machine as a proxy.

![Sync mode proxy](/images/sm-proxy.png)

This mode is useful when origin and target cannot connect directly (e.g., due to security restrictions).

### Configuration

Both origin and target have `host`:

```yaml
origin:
  host: prod.example.com
  user: deploy
  path: /var/www/html/LocalConfiguration.php
target:
  host: staging.example.com
  user: deploy
  path: /var/www/html/LocalConfiguration.php
```

### Flow
1. Dump created on origin
2. Transferred to local machine
3. Transferred to target
4. Imported on target

### Use Cases
- Syncing between isolated environments
- Cross-datacenter transfers
- Environments without direct network access

## Dump Local {#dump-local}

Create a database dump on your local system without transfer or import.

![Sync mode dump local](/images/sm-dump-local.png)

### Configuration

No `host` entries, only origin:

```yaml
origin:
  path: /var/www/local/LocalConfiguration.php
  dump_dir: /var/backups/
```

### Use Cases
- Local database backups
- Creating snapshots before risky operations

## Dump Remote {#dump-remote}

Create a database dump on a remote system without transfer or import.

![Sync mode dump remote](/images/sm-dump-remote.png)

### Configuration

Same `host` in both origin and target:

```yaml
origin:
  host: prod.example.com
  user: deploy
  path: /var/www/html/LocalConfiguration.php
  dump_dir: /var/backups/
target:
  host: prod.example.com
  user: deploy
  path: /var/www/html/LocalConfiguration.php
```

### Use Cases
- Remote backup creation
- Scheduled backup systems

## Import Local {#import-local}

Import an existing dump file to a local database.

![Sync mode import local](/images/sm-dump-local.png)

### Configuration

Use the `-i` / `--import-file` option:

```yaml
target:
  path: /var/www/local/LocalConfiguration.php
```

```bash
db_sync_tool -f config.yaml -i /path/to/dump.sql
```

### Use Cases
- Restoring from backup
- Importing shared database dumps

## Import Remote {#import-remote}

Import an existing dump file to a remote database.

![Sync mode import remote](/images/sm-dump-remote.png)

### Configuration

Use the `-i` / `--import-file` option with a remote target:

```yaml
target:
  host: staging.example.com
  user: deploy
  path: /var/www/html/LocalConfiguration.php
```

```bash
db_sync_tool -f config.yaml -i /remote/path/to/dump.sql
```

### Use Cases
- Restoring remote systems from backup
- Deploying database snapshots

## Sync Local {#sync-local}

Sync a database between two different local paths/databases.

![Sync mode sync local](/images/sm-sync-local.png)

### Configuration

No `host` entries, different `path` values:

```yaml
origin:
  path: /var/www/project-a/LocalConfiguration.php
target:
  path: /var/www/project-b/LocalConfiguration.php
```

### Use Cases
- Syncing between local projects
- Testing database migrations locally

## Sync Remote {#sync-remote}

Sync a database between two paths on the same remote system.

![Sync mode sync remote](/images/sm-sync-remote.png)

### Configuration

Same `host`, different `path` values:

```yaml
origin:
  host: server.example.com
  user: deploy
  path: /var/www/live/LocalConfiguration.php
target:
  host: server.example.com
  user: deploy
  path: /var/www/staging/LocalConfiguration.php
```

### Use Cases
- Copying production to staging on same server
- Testing environment refresh
