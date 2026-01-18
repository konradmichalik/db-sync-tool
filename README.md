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

Run `db_sync_tool --help` to see all available options. Arguments are organized into logical groups:

```
 Usage: db_sync_tool [OPTIONS] [ORIGIN] [TARGET]

 Synchronize a database from origin to target system.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   origin      [ORIGIN]  Origin database defined in host file                 │
│   target      [TARGET]  Target database defined in host file                 │
╰──────────────────────────────────────────────────────────────────────────────╯
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
╭─ Execution ──────────────────────────────────────────────────────────────────╮
│ --yes             -y     Skip user confirmation for database import          │
│ --dry-run         -dr    Testing without running export, transfer or import  │
│ --reverse         -r     Reverse origin and target hosts                     │
│ --force-password  -fpw   Force password user query                           │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Database Dump ──────────────────────────────────────────────────────────────╮
│ --import-file     -i     Import database from a specific file dump           │
│ --dump-name       -dn    Set a specific dump file name                       │
│ --keep-dump       -kd    Skip import and save dump in the given directory    │
│ --clear-database  -cd    Drop all tables before importing                    │
│ --tables          -ta    Specific tables to export (e.g. --tables=t1,t2)     │
│ --where           -w     WHERE clause for partial sync                       │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Origin Client ──────────────────────────────────────────────────────────────╮
│ --origin-host      -oh    SSH host to origin system                          │
│ --origin-user      -ou    SSH user for origin system                         │
│ --origin-path      -op    Path to database credential file                   │
│ --origin-db-name   -odn   Database name for origin system                    │
│ ...                                                                          │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Target Client ──────────────────────────────────────────────────────────────╮
│ --target-host      -th    SSH host to target system                          │
│ --target-user      -tu    SSH user for target system                         │
│ --target-path      -tp    Path to database credential file                   │
│ --target-db-name   -tdn   Database name for target system                    │
│ ...                                                                          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

If you haven't declared a path to a SSH key, you will be prompted to enter the SSH password.

#### Shell completion

The CLI supports automatic shell completion for bash, zsh, fish, and PowerShell:

```bash
# Install completion for your shell
db_sync_tool --install-completion

# Restart your shell, then use tab completion
db_sync_tool --config<TAB>  # completes to --config-file
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
