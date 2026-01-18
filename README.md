# db sync tool

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/db_sync_tool-kmi)
![PyPI](https://img.shields.io/pypi/v/db_sync_tool-kmi)
![Pepy Total Downloads](https://img.shields.io/pepy/dt/db-sync-tool-kmi)
![PyPI - Downloads](https://img.shields.io/pypi/dm/db-sync-tool-kmi)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/jackd248/db-sync-tool/badges/quality-score.png?b=main)](https://scrutinizer-ci.com/g/jackd248/db-sync-tool/?branch=main)
[![Build Status](https://scrutinizer-ci.com/g/jackd248/db-sync-tool/badges/build.png?b=main)](https://scrutinizer-ci.com/g/jackd248/db-sync-tool/build-status/main)

Python script to synchronize a database from an origin to a target system with automatic database credential extraction depending on the selected framework.

## Features

- __Database sync__ from and to a remote system
  - [MySQL](https://www.mysql.com/) (>= 5.5)
  - [MariaDB](https://mariadb.org/) (>= 10.0)
- __Proxy mode__ between two remote systems
- Several [synchronisation modes](docs/MODE.md)
- Automatic database __credential extraction__ using a supported framework
    - [TYPO3](https://typo3.org/) (>= v7.6)
    - [Symfony](https://symfony.com/) (>= v2.8)
    - [Drupal](https://www.drupal.org/) (>= v8.0)
    - [Wordpress](https://wordpress.org) (>= v5.0)
    - [Laravel](https://laravel.com/) (>= v4.0)
- Easily dump creation (database __backup__)
- __Cleanup__ feature for backups
- Extended __logging__ capabilities
- Many more possibilities for [customization](docs/CONFIG.md)

## Installation

### Prerequisite

The script needs [python](https://python.org/) __3.10__ or higher. It is necessary for some additional functionalities to have [pip](https://pypi.org/project/pip/) installed on your local machine. 

<a name="install-pip"></a>
### pip
The library can be installed from [PyPI](https://pypi.org/project/db-sync-tool-kmi/):
```bash
$ pip3 install db-sync-tool-kmi
```

<a name="install-composer"></a>
### composer
While using the script within the PHP framework context, the script is available via [packagist.org](https://packagist.org/packages/kmi/db-sync-tool) using composer:

```bash
$ composer require kmi/db-sync-tool
```

Additionally install the python requirements via the following pip command:

````bash
$ pip3 install -e vendor/kmi/db-sync-tool/
````

## Quickstart

Detailed instructions for:

- [Manual database sync](docs/quickstart/START.md)
- [TYPO3 database sync](docs/quickstart/TYPO3.md)
- [Symfony database sync](docs/quickstart/SYMFONY.md)
- [Drupal database sync](docs/quickstart/DRUPAL.md)
- [Wordpress database sync](docs/quickstart/WORDPRESS.md)

If you want to have an inside in more configuration examples, see the [test scenarios](tests/scenario). 

## Usage

### Command line

Run the python script via command line.

Installed via [pip](#install-pip):
```bash
$ db_sync_tool
```

Installed via [composer](#install-composer):
```bash
$ python3 vendor/kmi/db-sync-tool/db_sync_tool
```

![Example receiver](docs/images/db-sync-tool-example-receiver.gif)

<a name="shell-arguments"></a>
#### Shell arguments

```bash
usage: db_sync_tool [-h] [-f CONFIG_FILE] [-v] [-y] [-m] [-dr] [-i IMPORT_FILE] [-dn DUMP_NAME] [-kd KEEP_DUMP] [-o HOST_FILE] [-l LOG_FILE] [-cd] [-ta TABLES] [-r] [-t TYPE] [-tp TARGET_PATH]
                    [-tn TARGET_NAME] [-th TARGET_HOST] [-tu TARGET_USER] [-tpw TARGET_PASSWORD] [-tk TARGET_KEY] [-tpo TARGET_PORT] [-tdd TARGET_DUMP_DIR] [-tkd TARGET_KEEP_DUMPS] [-tdn TARGET_DB_NAME]
                    [-tdh TARGET_DB_HOST] [-tdu TARGET_DB_USER] [-tdpw TARGET_DB_PASSWORD] [-tdpo TARGET_DB_PORT] [-tad TARGET_AFTER_DUMP] [-op ORIGIN_PATH] [-on ORIGIN_NAME] [-oh ORIGIN_HOST]
                    [-ou ORIGIN_USER] [-opw ORIGIN_PASSWORD] [-ok ORIGIN_KEY] [-opo ORIGIN_PORT] [-odd ORIGIN_DUMP_DIR] [-okd ORIGIN_KEEP_DUMPS] [-odn ORIGIN_DB_NAME] [-odh ORIGIN_DB_HOST]
                    [-odu ORIGIN_DB_USER] [-odpw ORIGIN_DB_PASSWORD] [-odpo ORIGIN_DB_PORT] [-fpw] [-ur] [-uro USE_RSYNC_OPTIONS]
                    [origin] [target]

A tool for automatic database synchronization from and to host systems.

positional arguments:
  origin                Origin database defined in host file
  target                Target database defined in host file

optional arguments:
  -h, --help            show this help message and exit
  -f CONFIG_FILE, --config-file CONFIG_FILE
                        Path to configuration file
  -v, --verbose         Enable extended console output
  -y, --yes             Skipping user confirmation for database import
  -m, --mute            Mute console output
  -dr, --dry-run        Testing process without running database export, transfer or import.
  -i IMPORT_FILE, --import-file IMPORT_FILE
                        Import database from a specific file dump
  -dn DUMP_NAME, --dump-name DUMP_NAME
                        Set a specific dump file name (default is "_[dbname]_[date]")
  -kd KEEP_DUMP, --keep-dump KEEP_DUMP
                        Skipping target import of the database dump and saving the available dump file in the given directory
  -o HOST_FILE, --host-file HOST_FILE
                        Using an additional hosts file for merging hosts information with the configuration file
  -l LOG_FILE, --log-file LOG_FILE
                        File path for creating a additional log file
  -cd, --clear-database
                        Dropping all tables before importing a new sync to get a clean database.
  -ta TABLES, --tables TABLES
                        Defining specific tables to export, e.g. --tables=table1,table2
  -r, --reverse         Reverse origin and target hosts
  -t TYPE, --type TYPE  Defining the framework type [TYPO3, Symfony, Drupal, Wordpress]
  -tp TARGET_PATH, --target-path TARGET_PATH
                        File path to target database credential file depending on the framework type
  -tn TARGET_NAME, --target-name TARGET_NAME
                        Providing a name for the target system
  -th TARGET_HOST, --target-host TARGET_HOST
                        SSH host to target system
  -tu TARGET_USER, --target-user TARGET_USER
                        SSH user for target system
  -tpw TARGET_PASSWORD, --target-password TARGET_PASSWORD
                        SSH password for target system
  -tk TARGET_KEY, --target-key TARGET_KEY
                        File path to SSH key for target system
  -tpo TARGET_PORT, --target-port TARGET_PORT
                        SSH port for target system
  -tdd TARGET_DUMP_DIR, --target-dump-dir TARGET_DUMP_DIR
                        Directory path for database dump file on target system
  -tkd TARGET_KEEP_DUMPS, --target-keep-dumps TARGET_KEEP_DUMPS
                        Keep dump file count for target system
  -tdn TARGET_DB_NAME, --target-db-name TARGET_DB_NAME
                        Database name for target system
  -tdh TARGET_DB_HOST, --target-db-host TARGET_DB_HOST
                        Database host for target system
  -tdu TARGET_DB_USER, --target-db-user TARGET_DB_USER
                        Database user for target system
  -tdpw TARGET_DB_PASSWORD, --target-db-password TARGET_DB_PASSWORD
                        Database password for target system
  -tdpo TARGET_DB_PORT, --target-db-port TARGET_DB_PORT
                        Database port for target system
  -tad TARGET_AFTER_DUMP, --target-after-dump TARGET_AFTER_DUMP
                        Additional dump file to insert after the regular database import
  -op ORIGIN_PATH, --origin-path ORIGIN_PATH
                        File path to origin database credential file depending on the framework type
  -on ORIGIN_NAME, --origin-name ORIGIN_NAME
                        Providing a name for the origin system
  -oh ORIGIN_HOST, --origin-host ORIGIN_HOST
                        SSH host to origin system
  -ou ORIGIN_USER, --origin-user ORIGIN_USER
                        SSH user for origin system
  -opw ORIGIN_PASSWORD, --origin-password ORIGIN_PASSWORD
                        SSH password for origin system
  -ok ORIGIN_KEY, --origin-key ORIGIN_KEY
                        File path to SSH key for origin system
  -opo ORIGIN_PORT, --origin-port ORIGIN_PORT
                        SSH port for origin system
  -odd ORIGIN_DUMP_DIR, --origin-dump-dir ORIGIN_DUMP_DIR
                        Directory path for database dump file on origin system
  -okd ORIGIN_KEEP_DUMPS, --origin-keep-dumps ORIGIN_KEEP_DUMPS
                        Keep dump file count for origin system
  -odn ORIGIN_DB_NAME, --origin-db-name ORIGIN_DB_NAME
                        Database name for origin system
  -odh ORIGIN_DB_HOST, --origin-db-host ORIGIN_DB_HOST
                        Database host for origin system
  -odu ORIGIN_DB_USER, --origin-db-user ORIGIN_DB_USER
                        Database user for origin system
  -odpw ORIGIN_DB_PASSWORD, --origin-db-password ORIGIN_DB_PASSWORD
                        Database password for origin system
  -odpo ORIGIN_DB_PORT, --origin-db-port ORIGIN_DB_PORT
                        Database port for origin system
  -fpw, --force-password
                        Force password user query
  -ur, --use-rsync      Use rsync as transfer method
  -uro USE_RSYNC_OPTIONS, --use-rsync-options USE_RSYNC_OPTIONS
                        Additional rsync options
  -w WHERE, --where WHERE
                        Additional where clause for mysql dump to sync only selected rows, e.g. --where="deleted=0"
  -amo OPTIONS, --additional-mysqldump-options OPTIONS
                        Additional mysqldump options for creating the database dump, e.g. --additional-mysqldump-options="--where="deleted=0"
```

If you haven't declared a path to a SSH key, during the script execution you are requested to enter the SSH password for the given user in the shell argument or the `config.json` to enable a SSH connection for the remote system.

<a name="modern-cli"></a>
#### Modern CLI (typer)

An alternative CLI based on [typer](https://typer.tiangolo.com/) is available with improved help output and shell completion support. The typer CLI organizes arguments into logical groups for better readability.

**Enable typer CLI:**
```bash
# Set environment variable
export DB_SYNC_TOOL_USE_TYPER=1

# Or use inline
DB_SYNC_TOOL_USE_TYPER=1 db_sync_tool --help
```

**Features:**
- Grouped help output (Configuration, Output, Execution, Database Dump, etc.)
- Automatic shell completion (`db_sync_tool --install-completion`)
- Same arguments and behavior as the standard CLI

**Example help output:**
```
 Usage: db_sync_tool [OPTIONS] [ORIGIN] [TARGET]

 Synchronize a database from origin to target system.

╭─ Configuration ──────────────────────────────────────────────────────────────╮
│ --config-file  -f      TEXT  Path to configuration file                      │
│ --host-file    -o      TEXT  Using an additional hosts file                  │
│ --log-file     -l      TEXT  File path for creating an additional log file   │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Output ─────────────────────────────────────────────────────────────────────╮
│ --verbose  -v      INTEGER  Enable verbose output (-v) or debug (-vv)        │
│ --mute     -m               Mute console output                              │
│ --quiet    -q               Suppress all output except errors                │
│ --output           [interactive|ci|json|quiet]  Output format                │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Origin Client ──────────────────────────────────────────────────────────────╮
│ --origin-host  -oh   TEXT  SSH host to origin system                         │
│ --origin-user  -ou   TEXT  SSH user for origin system                        │
│ ...                                                                          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**Shell completion:**
```bash
# Install completion for your shell (bash, zsh, fish, powershell)
DB_SYNC_TOOL_USE_TYPER=1 db_sync_tool --install-completion

# Restart your shell, then use tab completion
db_sync_tool --config<TAB>  # completes to --config-file
```

**Make typer the default (optional):**
```bash
# Add to your ~/.bashrc or ~/.zshrc
export DB_SYNC_TOOL_USE_TYPER=1
``` 

### Import

You can import the python package and use them inside your project:

```python
from db_sync_tool import sync

if __name__ == "__main__":
    sync.Sync(config={}, args*)
```

## Configuration

You can configure the script with [shell arguments](#shell-arguments) or using a separate configuration file.

### Configuration File

The `config.json` contains important information about the origin and the target system. In dependence on the given configuration the [synchronisation mode](docs/MODE.md) is implicitly selected.

Example structure of a `config.yml` for a Symfony system in receiver mode (`path` defines the location of the Symfony database configuration file):
```yaml
type: Symfony
origin:
    host: 192.87.33.123
    user: ssh_demo_user
    path: /var/www/html/project/shared/.env
target:
    path: /var/www/html/app/.env
```

It is possible to adjust the `config.yml` [configuration](docs/CONFIG.md).

## File sync

There is an addon script available to sync files to. Use the [file-sync-tool](https://github.com/jackd248/file-sync-tool) to easily transfer files between origin and target system. 

## Release Guide

A detailed guide is available to release a new version. See [here](docs/RELEASE.md).

## Tests

A docker container set up is available for testing purpose. See [here](tests/README.md).

## Support

If you like the project, feel free to support the development.

<a href="https://www.buymeacoffee.com/konradmichalik" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-green.png" alt="Buy Me A Coffee" height="41" width="174"></a>
