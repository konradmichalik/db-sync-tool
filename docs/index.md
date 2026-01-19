---
layout: home

hero:
  name: db-sync-tool
  text: Database Synchronization Tool
  tagline: Sync MySQL/MariaDB databases between systems with automatic credential extraction
  actions:
    - theme: brand
      text: Get Started
      link: /getting-started/
    - theme: alt
      text: View on GitHub
      link: https://github.com/konradmichalik/db-sync-tool

features:
  - icon: 🔄
    title: Database Sync
    details: Synchronize MySQL/MariaDB databases between local and remote systems in various modes (receiver, sender, proxy).
  - icon: 🔐
    title: Auto Credential Extraction
    details: Automatically extract database credentials from popular PHP frameworks like TYPO3, Symfony, Drupal, WordPress, and Laravel.
  - icon: 🚀
    title: Multiple Sync Modes
    details: Support for receiver, sender, proxy, dump, import, and sync modes for flexible database operations.
  - icon: 📦
    title: Easy Installation
    details: Install via pip or composer and start syncing databases with a simple configuration file.
  - icon: 🛡️
    title: Host Protection
    details: Protect production databases with the protect flag to prevent accidental overwrites.
  - icon: ⚡
    title: Performance Optimized
    details: Optimized mysqldump with gzip compression and rsync transfer for fast synchronization.
---

## Quick Example

```bash
# Install via pip
pip install db-sync-tool-kmi

# Sync database from remote to local
db_sync_tool production local
```

## Supported Frameworks

| Framework | Version | Config File |
|-----------|---------|-------------|
| [TYPO3](/getting-started/typo3) | >= 7.6 | `LocalConfiguration.php` or `.env` |
| [Symfony](/getting-started/symfony) | >= 2.8 | `.env` or `parameters.yml` |
| [Drupal](/getting-started/drupal) | >= 8.0 | `settings.php` (via drush) |
| [WordPress](/getting-started/wordpress) | >= 5.0 | `wp-config.php` |
| [Laravel](/getting-started/laravel) | >= 4.0 | `.env` |
