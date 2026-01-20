# v3.0.0

A major release focused on **security hardening**, **performance improvements**, and **modern Python practices**.

## Highlights

**5-10x faster transfers** - rsync is now the default transfer method with streaming compression

**Modern CLI** - Rich terminal output with colors, progress indicators, and multiple output formats

**File synchronization** - Sync files alongside your database with `--with-files`

**Auto-discovery** - No more `-f config.yaml` needed in project directories

**Security hardened** - SSH host key verification, credential protection, injection prevention

## Breaking Changes

| Change | Migration |
|--------|-----------|
| Python 3.10+ required | Upgrade Python before updating |
| Typer CLI (argparse removed) | Most scripts work unchanged |
| rsync is default transfer | Falls back to SFTP automatically |
| SSH host key verification | Run `ssh-keyscan -H host >> ~/.ssh/known_hosts` |

See the [Upgrade Guide](https://konradmichalik.github.io/db-sync-tool/getting-started/upgrade-v3) for detailed migration steps.

## New Features

- **Rich CLI output** with `--output=interactive|ci|json|quiet`
- **Structured JSON logging** via `--json-log` for log aggregation
- **File sync** via `--with-files` and `--files-only` flags
- **Auto-discovery** for config files in project directories
- **Python 3.14 support**
- **Custom exceptions** for better error handling

## Performance

- Streaming compression (`mysqldump | gzip`)
- Batch truncate operations (80-90% fewer DB roundtrips)
- mysqldump optimization flags

## Security

- SSH host key verification (MITM protection)
- MySQL credentials via `--defaults-file` (hidden from process lists)
- Shell argument quoting (command injection prevention)
- Table name validation (SQL injection prevention)
- Credentials sanitized from logs

## Installation

```bash
pip install --upgrade db-sync-tool-kmi
```

## Full Changelog

See [CHANGELOG.md](https://github.com/konradmichalik/db-sync-tool/blob/main/CHANGELOG.md) for all changes.
