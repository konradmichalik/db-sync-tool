# Upgrade to v3.0

This guide covers migrating from db-sync-tool v2.x to v3.0. Version 3.0 includes significant improvements in security, performance, and developer experience, but also introduces breaking changes that may require action.

## Breaking Changes

### 1. Python 3.10+ Required

**What changed:** Support for Python < 3.10 has been removed.

**Action required:**
```bash
# Check your Python version
python3 --version

# If below 3.10, upgrade Python first
# macOS (Homebrew)
brew install python@3.12

# Ubuntu/Debian
sudo apt update && sudo apt install python3.12

# Then reinstall db-sync-tool
pip3 install --upgrade db-sync-tool-kmi
```

### 2. Typer CLI (argparse removed)

**What changed:** The CLI now uses [Typer](https://typer.tiangolo.com/) instead of argparse. Most commands remain compatible, but there are subtle differences.

**Key differences:**
- Boolean flags now use `--flag` / `--no-flag` syntax
- Shell completion is now built-in via `--install-completion`
- Help output has a different format

**Action required:** Update any scripts using the old CLI:

```bash
# Old (v2.x) - still works
db_sync_tool -f config.yaml -v -y

# New feature - shell completion
db_sync_tool --install-completion
```

Most existing scripts should continue to work without changes.

### 3. rsync is Default Transfer Method

**What changed:** rsync is now the default transfer method instead of SFTP, providing 5-10x faster transfers.

**Action required:**

If rsync is **not available** on your systems, db-sync-tool will automatically fall back to SFTP. No action needed.

If you experience issues:
```bash
# Check if rsync is available
which rsync

# Install rsync if missing
# macOS
brew install rsync

# Ubuntu/Debian
sudo apt install rsync

# Or explicitly use SFTP in your config
# (add to config file)
transfer:
  method: sftp
```

### 4. SSH Host Key Verification Enabled

**What changed:** SSH connections now verify host keys by default to prevent man-in-the-middle attacks. This is a security improvement but may cause connection failures if host keys are not in your `known_hosts` file.

**Symptoms:**
```
Error: Host key for server 'example.com' not found
```

**Action required:**

Option A - Add host keys (recommended):
```bash
# Add host key to known_hosts
ssh-keyscan -H example.com >> ~/.ssh/known_hosts

# Or connect manually once to accept the key
ssh user@example.com
# Type 'yes' when prompted, then exit
```

Option B - For multiple hosts, scan all at once:
```bash
# Add multiple hosts
ssh-keyscan -H host1.example.com host2.example.com >> ~/.ssh/known_hosts
```

Option C - Verify existing keys:
```bash
# Check if host is already known
ssh-keygen -F example.com
```

::: warning Security Note
Do NOT disable host key verification. It protects you from attackers intercepting your database credentials and data.
:::

## New Features in v3.0

After upgrading, you can take advantage of these new features:

### Rich CLI Output

Modern terminal output with colors and progress indicators:
```bash
db_sync_tool -f config.yaml
```

Output formats for different environments:
```bash
# Interactive (default) - colored with spinners
db_sync_tool -f config.yaml --output=interactive

# CI/CD - GitHub Actions / GitLab CI compatible
db_sync_tool -f config.yaml --output=ci

# JSON - for parsing/automation
db_sync_tool -f config.yaml --output=json

# Quiet - minimal output
db_sync_tool -f config.yaml --output=quiet
```

### Structured JSON Logging

For log aggregation systems (ELK, Splunk, etc.):
```bash
db_sync_tool -f config.yaml -l /var/log/sync.log --json-log
```

### File Synchronization

Sync files alongside your database:
```yaml
# config.yaml
origin:
  host: production.example.com
  path: /var/www/html/typo3conf/LocalConfiguration.php
  files:
    - /var/www/html/fileadmin
    - /var/www/html/uploads

target:
  path: /var/www/local/typo3conf/LocalConfiguration.php
  files:
    - /var/www/local/fileadmin
    - /var/www/local/uploads
```

```bash
# Sync database AND files
db_sync_tool -f config.yaml --with-files

# Sync only files (skip database)
db_sync_tool -f config.yaml --files-only
```

### Auto-Discovery Configuration

No more specifying config file paths:
```bash
# Automatically finds config in current directory
cd /path/to/project
db_sync_tool production local
```

Searches for configs in:
- `.db-sync-tool/`
- `db-sync.yaml` / `db-sync.json`
- `.db-sync.yaml` / `.db-sync.json`

See [Auto-Discovery](/configuration/auto-discovery) for details.

## Migration Checklist

- [ ] Python version is 3.10 or higher
- [ ] SSH host keys added to `~/.ssh/known_hosts` for all remote hosts
- [ ] rsync installed (or SFTP fallback is acceptable)
- [ ] Updated any custom scripts using the CLI
- [ ] Tested sync in dry-run mode: `db_sync_tool -f config.yaml --dry-run`

## Troubleshooting

### "Host key verification failed"

See [SSH Host Key Verification](#_4-ssh-host-key-verification-enabled) above.

### "rsync: command not found"

Install rsync or let it fall back to SFTP automatically.

### "Python version not supported"

Upgrade to Python 3.10+. See [Python 3.10+ Required](#_1-python-3-10-required).

### Deprecation Warnings

If you see deprecation warnings from dependencies (e.g., Blowfish from paramiko), ensure you have the latest versions:
```bash
pip3 install --upgrade db-sync-tool-kmi
```

## Getting Help

- [GitHub Issues](https://github.com/konradmichalik/db-sync-tool/issues)
- [Documentation](/)
