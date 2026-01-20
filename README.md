<div align="center">

![db-sync-tool](docs/images/db-sync-tool-example-receiver.gif)

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/db_sync_tool-kmi)](https://pypi.org/project/db-sync-tool-kmi/)
[![PyPI](https://img.shields.io/pypi/v/db_sync_tool-kmi)](https://pypi.org/project/db-sync-tool-kmi/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/db-sync-tool-kmi)](https://pypi.org/project/db-sync-tool-kmi/)
[![Packagist](https://img.shields.io/packagist/v/kmi/db-sync-tool)](https://packagist.org/packages/kmi/db-sync-tool)

# Database Sync Tool

A Python CLI to synchronize MySQL/MariaDB databases between systems with automatic credential extraction.

[**Explore the docs &raquo;**](https://konradmichalik.github.io/db-sync-tool/)

[Report Bug](https://github.com/konradmichalik/db-sync-tool/issues/new) ·
[Request Feature](https://github.com/konradmichalik/db-sync-tool/issues/new) ·
[Latest Release](https://github.com/konradmichalik/db-sync-tool/releases/latest)

</div>

## ✨ Features

* Sync databases from and to remote systems via SSH
* Proxy mode for transfers between isolated environments
* Automatic credential extraction from PHP frameworks
  * TYPO3, Symfony, Drupal, WordPress, Laravel
* Auto-discovery configuration for quick syncs
* Host protection to prevent accidental overwrites
* Optimized transfers with gzip compression and rsync

## 🚀 Getting Started

```bash
# Install via pip
pip install db-sync-tool-kmi

# Sync using auto-discovery
db_sync_tool production local

# Or use a config file
db_sync_tool -f config.yaml
```

Find more [installation methods](https://konradmichalik.github.io/db-sync-tool/getting-started/installation) in the documentation.

## 📕 Documentation

Find all configuration options, sync modes, and framework guides in the [official documentation](https://konradmichalik.github.io/db-sync-tool/).

## 🧑‍💻 Contributing

Please have a look at [`CONTRIBUTING.md`](CONTRIBUTING.md).

## ⭐ License

This project is licensed under the MIT License.
