# Configuration

Here you can find an overview over the possible configuration adjustments.

- [Auto-Discovery Configuration](#auto-discovery)
- [Full configuration reference](#configuration_reference)
- [Ignore tables](#ignore_tables)
- [Authentication](#authentication)
- [Linking hosts](#linking)
- [SSH Port](#port)
- [Console commands](#console)
- [(Temporary) dump directory](#directory)
- [Before and after script](#script)
- [After dump](#after-dump)
- [Logging](#logging)
- [Cleaning up / keeping dumps count](#clean_up)
- [Naming hosts](#naming)
- [Check dump](#check)
- [Manual database credentials](#manual)
- [Clearing database](#clear)
- [Protect host](#protect)
- [Reverse hosts](#reverse)
- [Jump host](#jump_host)

<a name="auto-discovery"></a>
## Auto-Discovery Configuration

The tool supports automatic configuration discovery for faster and more convenient workflows. Instead of always specifying `-f config.yaml`, you can organize your configurations for quick access.

### Configuration Lookup Order

When you run `db_sync_tool`, it searches for configuration in this order:

1. **Explicit file** (`-f config.yaml`) → Uses that file directly
2. **Project config by name** (`db_sync_tool prod`) → Loads `.db-sync-tool/prod.yaml`
3. **Host references** (`db_sync_tool production local`) → Uses hosts from `~/.db-sync-tool/hosts.yaml`
4. **Interactive selection** (no args) → Prompts user to select from available configs
5. **Error** → If nothing found

### Global Hosts (`~/.db-sync-tool/`)

Define reusable host configurations in your home directory. These can be referenced from any project.

**Directory structure:**
```
~/.db-sync-tool/
├── hosts.yaml       # Host definitions
└── defaults.yaml    # Global defaults (optional)
```

**Example `~/.db-sync-tool/hosts.yaml`:**
```yaml
production:
  host: prod.example.com
  user: deploy
  path: /var/www/html/LocalConfiguration.php
  protect: true                    # Prevents accidental overwrites

staging:
  host: staging.example.com
  user: deploy
  path: /var/www/html/LocalConfiguration.php

local:
  path: /var/www/local/LocalConfiguration.php
```

**Example `~/.db-sync-tool/defaults.yaml`:**
```yaml
type: TYPO3
ignore_table:
  - cache_*
  - cf_*
  - sys_log
use_rsync: true
```

**Usage with host references:**
```bash
# Sync production → local using host definitions
db_sync_tool production local

# Interactive host selection
db_sync_tool
```

### Project Configs (`.db-sync-tool/`)

Create project-specific sync configurations in a `.db-sync-tool/` directory within your project. The tool searches the current directory and parent directories.

**Directory structure:**
```
myproject/
├── .db-sync-tool/
│   ├── prod.yaml       # Sync production → local
│   ├── staging.yaml    # Sync staging → local
│   └── defaults.yaml   # Project-specific defaults (optional)
├── src/
└── ...
```

**Example `.db-sync-tool/prod.yaml`:**
```yaml
origin: production      # Reference to host in ~/.db-sync-tool/hosts.yaml
target: local
ignore_table:
  - tx_solr_*          # Project-specific tables to ignore
```

**Example with inline configuration:**
```yaml
origin:
  host: custom.example.com
  user: deploy
  path: /var/www/app/.env
target:
  path: /home/dev/project/.env
type: Symfony
```

**Usage with project configs:**
```bash
# Load .db-sync-tool/prod.yaml
db_sync_tool prod

# Load .db-sync-tool/staging.yaml
db_sync_tool staging

# Interactive selection if multiple configs exist
db_sync_tool
```

### Configuration Merging

Configurations are merged in this order (later values override earlier):

1. **Global defaults** (`~/.db-sync-tool/defaults.yaml`)
2. **Project defaults** (`.db-sync-tool/defaults.yaml`)
3. **Project config** (`.db-sync-tool/[name].yaml`)
4. **CLI arguments** (`--target-host`, etc.)

This allows you to define common settings once and override them per-project or per-sync.

### Protected Hosts

Use the `protect: true` flag to prevent accidental database overwrites on production systems:

```yaml
production:
  host: prod.example.com
  user: deploy
  path: /var/www/html/config.php
  protect: true
```

When a protected host is used as a **target**, the tool will:
1. Display a prominent warning
2. Require explicit confirmation before proceeding

### Interactive Mode

When running without arguments and configs are available, the tool provides an interactive selection:

```
╭─ db-sync-tool ────────────────────────────────────────────╮
│  Project configs found: .db-sync-tool/                    │
╰───────────────────────────────────────────────────────────╯

  [1] prod      production (prod.example.com) → local (local)
  [2] staging   staging (staging.example.com) → local (local)

Selection [1-2]: 1

╭─ Sync Preview ────────────────────────────────────────────╮
│  production (prod.example.com) → local (local)            │
╰───────────────────────────────────────────────────────────╯

Continue? [y/N]:
```

Interactive mode is disabled when:
- Running in CI environments (detected automatically)
- Using `--quiet` or `--mute` flags
- Output is not a TTY (e.g., piped to another command)

<a name="configuration_reference"></a>
### Full configuration reference

Here you can find the full configuration reference for a `config.yml`:

```yaml
# Application type: TYPO3 [ Symfony | Drupal | Wordpress | Laravel
# Isn't necessary if the database credentials are provided manually
type: 
# Database source system
origin:
    # Just informative for logging, e.g. prod
    name:
    # Full path to the application file, which contains the necessary database credentials
    path: 
    # For reusability reasons you can store the host information in an additional hosts.yml file and link the needed entry here
    # See the section "Linking hosts" for more information
    # e.g. hosts.yml@prod
    link:
    # SSH host
    host:
    # SSH user
    user:
    # SSH port (default: 22)
    port:
    # SSh password (is not recommended to store the password here, use the interactive prompt or a ssh key instead)
    password:
    # SSH key path
    ssh_key:
    # Provide an optional configuration for a SSH jump host
    jump_host:
        # SSH jump host host
        host:
        # SSH jump host private ip, necessary for session channel
        private:
        # SSH jump host user (default: origin SSH user)
        user:
        # SSH jump host port (default: origin SSH port)
        port:
        # Just informative for logging, e.g. prod
        name:
    # Temporary or finally dump file directory (default: /tmp/)
    dump_dir:
    # Manual database credentials
    db:
        # Database name
        name:
        # Database host
        host:
        # Database password
        password:
        # Database user
        user:
        # Database port (default: 3306)
        port:
    # Additional console scripts
    script:
        # Script before synchronisation on origin system
        before:
        # Script after synchronisation on origin system
        after:
        # Script in failure case
        error:
    # Additional console path variables
    console:
        # If a command variable is not available via the standard path, you can define a divergent path
        # e.g. php: /usr/bin/php
# Database target system
target:
    # Just informative for logging, e.g. prod
    name:
    # Full path to the application file, which contains the necessary database credentials
    path: 
    # For reusability reasons you can store the host information in an additional hosts.yml file and link the needed entry here
    # See the section "Linking hosts" for more information
    # e.g. hosts.yml@prod
    link:
    # SSH host
    host:
    # SSH user
    user:
    # SSH port (default: 22)
    port:
    # SSh password (is not recommended to store the password here, use the interactive prompt or a ssh key instead)
    password:
    # SSH key path
    ssh_key:
    # Provide an optional configuration for a SSH jump host
    jump_host:
        # SSH jump host host
        host:
        # SSH jump host private ip, necessary for session channel
        private:
        # SSH jump host user (default: target SSH user)
        user:
        # SSH jump host port (default: target SSH port)
        port:
        # Just informative for logging, e.g. prod
        name:
    # Temporary or finally dump file directory (default: /tmp/)
    dump_dir:
    # Lock the host against the import of a database dump
    protect: true
    # Manual database credentials
    db:
        # Database name
        name:
        # Database host
        host:
        # Database password
        password:
        # Database user
        user:
        # Database port (default: 3306)
        port:
    # Additional console scripts
    script:
        # Script before synchronisation on target system
        before:
        # Script after synchronisation on target system
        after:
        # Script in failure case
        error:
    # Additional console path variables
    console:
        # If a command variable is not available via the standard path, you can define a divergent path
        # e.g. php: /usr/bin/php
    # Define the backup clean up functionality and defines how many dumps will be keep depending on time
    keep_dumps:
    # Path to an additional dump file, which will be imported after the synchronisation finished
    # e.g. /path/to/dump/file.sql
    after_dump:
    # Additional sql commands after the import
    post_sql: 
    - 
# Path to an additional log file
log_file:
# List of tables to ignore for the synchronisation
ignore_table: []
# List of tables to truncate before the synchronisation
truncate_table: []
# Disable the check dump feature, to verify the completeness of the created dump file (default: true)
check_dump:
# Additional console scripts
script:
    # Script before synchronisation
    before:
    # Script after synchronisation
    after:
    # Script in failure case
    error:
```


> The config file can be written in `yaml` or `json`.

<a name="ignore_tables"></a>
### Ignore/truncate tables 

Often it is better to exclude some tables from the sql dump for performance reasons, e.g. caching tables. Specify them as comma separated list in the `ignore_table` array.

You can use wildcards to define several tables:

```yaml
ignore_tables:
    - cache_*
```

There is also an option to truncate tables before the import with listing shown as below:
```yaml
truncate_tables:
    - cache_*
```

<a name="authentication"></a>
### Authentication

There a different ways to authenticate against remote systems.

### SSH key

Without any option, the db_sync_tool tries to authenticate with a running ssh agent.

If you want to authenticate with a specific private ssh key instead of a user entered password to the server (useful for CI/CD), you can add the file path to the private key file in your `config.json`:

```json
{
  "origin": {
    "ssh_key": "/home/bob/.ssh/id_rsa"
  }
}
```

### SSH password

It's not recommended, but you can also specify the plain password inside the host configuration in the `config.json`:

```json
{
  "origin": {
    "password": "1234"
  }
}
```

If no options are provided so far (no ssh agent, ssh key, defined password), a prompt is displayed to enter the necessary password for the ssh authentication. You can also force the user input by adding the `--force-password` / `-fpw` option to the script call. 

<a name="linking"></a>
### Linking hosts

For larger project setups with multiple configuration files, it's better to reuse the host configuration in every sync scenario. So you can link to predefined host in your `config.json`:

```json
{
  "origin": {
    "link": "@prod"
  },
  "target": {
    "link": "@dev"
  }
}
```

You specify the path to the `hosts.json` file with the `-o` option within the script call. The `hosts.json` should look like this:

```json
{
  "prod": {
    "host": "host",
    "user": "user",
    "path": "/var/www/html/project/shared/typo3conf/LocalConfiguration.php"
  },
  "dev": {
    "host": "host",
    "user": "user",
    "path": "/var/www/html/project/shared/typo3conf/LocalConfiguration.php"
  }
}
```


<a name="port"></a>
### SSH Port

You can also specify a different SSH port to the client in your `config.json` (the default port is `22`):

```json
{
  "origin": {
    "port": "1234"
  }
}
```

<a name="console"></a>
### Console commands

The script using among other things the `php`, `mysql`, `mysqldump`, `grep` commands to synchronize the databases. Sometimes these commands are not available via the path variable, so you have to specify the full path to the source in the `config.json` depending on the system:

```json
{
  "origin": {
    "console": {
      "php": "/usr/bin/php",
      "mysql": "/usr/bin/mysql",
      "mysqldump": "/usr/bin/mysqldump"
    }
  }
}
```

<a name="directory"></a>
### (Temporary) dump directory

Normally is the script creating the sql dump in the `/tmp/` directory. If this directory is not writable or you want to export the database automatically in another directory, you can specify an alternative directory in the `config.json`, where the temporary sql dump will be saved:

```json
{
  "origin": {
    "dump_dir": "/path/to/writable/dir/"
  }
}
```

**Note:** It is recommended to use for every application another directory to avoid side effects (e.g. cleaning up feature).

<a name="script"></a>
### Before and after script

Sometimes it is necessary to run a specific command before or after the dump creation on the origin or target system to ensure the correct synchronisation process. Therefore you can specify these commands in the `config.json`:

```json
{
  "script": {
    "before": "",
    "after": "",
    "error": ""
  },
  "origin": {
    "script": {
      "before": "",
      "after": "",
      "error": ""
    },
  },
  "target": {
    "script": {
      "before": "",
      "after": "",
      "error": ""
    },
  }
}
```

<a name="after-dump"></a>
### After dump

It is possible to provide an additional dump file, which will be imported after the regular database import is finished. You can specify the path to the `after_dump` file of the target host in the `config.yml`:

```yaml
target:
    after_dump: path/to/dump/file.sql
```

Alternatively you can define post sql commands, which will be executed in the 

```yaml
target:
    post_sql: 
        - UPDATE sys_domain SET hidden = 1;
```

<a name="logging"></a>
### Logging

You can enable the logging to a separate log file via the `log_file` entry in the `config.json`:

```json
{
  "log_file": "/path/to/file/info.log"
}
```

**Note**: By default only a summary of the sync actions will be logged. If you enable the verbose option (`-v`) all console output will also be logged in the given log file.

<a name="clean_up"></a>
### Cleaning up / keeping dumps count

With the concept of the *DUMP_REMOTE* or *DUMP_LOCAL* mode can you implement an automatic backup system. However it's a good option to clean up old dump files and only keep the newest ones. Therefore you can use the `keep_dumps` entry in the `config.json`:

```json
{
  "origin": {
    "dump_dir": "/path/to/writable/dir/",
    "keep_dumps": 5
  }
}
```

**Note**: Be aware of this feature. It will only keep the latest (e.g. 5) files in the `dump_dir` directory and delete all other `.sql` and `.tar.gz` files.

<a name="naming"></a>
### Naming hosts

For a better differentiation of the different host systems you can optionally provide a specific name in the `config.json`:

```json
{
  "origin": {
    "name": "Prod"
  },
  "target": {
    "name": "Stage"
  }
}
```

<a name="check"></a>
### Check dump

The script is checking the target dump if the file is being downloaded completely. If you want to prevent this check, you can disable them in the `config.json`:

```json
{
  "check_dump": false
}
```

<a name="manual"></a>
### Manual database credentials

It is also possible to skip the automatic database credential detection depending on the framework and provide the database credentials by your own in the `config.json` (example for RECEIVER mode):

```json
{
  "name": "project",
  "target": {
    "db": {
      "name": "db",
      "host": "db2",
      "password": "db",
      "user": "db",
      "port": 3306
    }
  },
  "origin": {
    "host": "www1",
    "user": "user",
    "password": "password",
    "db": {
      "name": "db",
      "host": "db1",
      "password": "db",
      "user": "db",
      "port": 3306
    }
  },
  "ignore_table": []
}
```

<a name="clear"></a>
### Clearing database

If you want a clean database sync, it is necessary to drop all existing tables of the target database. Use the `--clear-database` option (`-cd`) for this.

<a name="protect"></a>
### Protect host

You can declare a protected to host to prevent an unintentional import on this system. 

```yaml
type: TYPO3
origin:
    host: <ORIGIN_HOST>
    user: <ORIGIN_USER>
    path: <ORIGIN_PATH>
    name: Demo Prod
    protect: true
target:
    path: <TARGET_PATH>
```


<a name="reverse"></a>
### Reverse hosts

You can easily reverse the declared origin and target hosts with the `--reverse` argument:

```yaml
$ db_sync_tool -f config.yml --reverse
```

<a name="jump_host"></a>
### Jump host

You can define an optionally SSH jump host, for accessing protected server. Unfortunately this can not be read out of the `.ssh/config`, so you have to specify them as follows:
```yaml
origin:
    jump_host:
        host: <ORIGIN_JUMP_HOST_HOST>
        private: <ORIGIN_JUMP_HOST_PRIVATE>
        user: <ORIGIN_JUMP_HOST_USER>
        port: <ORIGIN_JUMP_HOST_PORT>
        name: Demo Jump Host
```

The `host` entry is the public ip address, the `private` entry is the private ip address (can be determined by `hostname -I` or `ip addr` or `ifconfig`).

The entries for `user` (as default the parent/origin SSH user is used), `port` (as default the parent/origin SSH port is used) and `name` are optional. 