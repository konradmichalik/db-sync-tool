# Introduction

db-sync-tool is a Python CLI tool for synchronizing MySQL/MariaDB databases between systems. It supports automatic database credential extraction from popular PHP frameworks and various sync modes for different use cases.

## Features

- **Database sync** from and to remote systems
  - MySQL (>= 5.5)
  - MariaDB (>= 10.0)
- **Proxy mode** between two remote systems
- Several [synchronization modes](/reference/sync-modes)
- **Automatic database credential extraction** using supported frameworks:
  - [TYPO3](/getting-started/typo3) (>= v7.6)
  - [Symfony](/getting-started/symfony) (>= v2.8)
  - [Drupal](/getting-started/drupal) (>= v8.0)
  - [WordPress](/getting-started/wordpress) (>= v5.0)
  - [Laravel](/getting-started/laravel) (>= v4.0)
- Easy dump creation (database backup)
- **Cleanup** feature for backups
- Extended **logging** capabilities
- Many more possibilities for [customization](/configuration/)

## Requirements

- Python **3.10** or higher
- SSH access to remote systems (if syncing remotely)
- MySQL or MariaDB client installed

## How It Works

1. **Configuration**: Define origin and target systems in a config file or via CLI arguments
2. **Credential extraction**: If using a supported framework, credentials are automatically parsed
3. **Export**: Create a mysqldump on the origin system
4. **Transfer**: Transfer the dump file via SSH/SFTP or rsync
5. **Import**: Import the dump on the target system
6. **Cleanup**: Remove temporary files

## Next Steps

- [Installation](/getting-started/installation) - Get db-sync-tool installed
- [Quick Start](/getting-started/quickstart) - Your first database sync
- [Framework Guides](/getting-started/typo3) - Framework-specific setup
