# Installation

## Prerequisites

- Python **3.10** or higher
- [pip](https://pypi.org/project/pip/) for package installation

## pip (Recommended)

Install db-sync-tool from [PyPI](https://pypi.org/project/db-sync-tool-kmi/):

```bash
pip install db-sync-tool-kmi
```

After installation, run:

```bash
db_sync_tool --help
```

## Composer (PHP Projects)

For PHP framework projects, install via [Packagist](https://packagist.org/packages/kmi/db-sync-tool):

```bash
composer require kmi/db-sync-tool
```

Then install Python dependencies:

```bash
pip install -e vendor/kmi/db-sync-tool/
```

Run using:

```bash
python3 vendor/kmi/db-sync-tool/db_sync_tool
```

## Shell Completion

db-sync-tool supports automatic shell completion for bash, zsh, fish, and PowerShell:

```bash
# Install completion for your shell
db_sync_tool --install-completion

# Restart your shell, then use tab completion
db_sync_tool --config<TAB>  # completes to --config-file
```

## Verify Installation

```bash
# Check version
db_sync_tool --version

# View help
db_sync_tool --help
```

## Next Steps

- [Quick Start](/getting-started/quickstart) - Your first database sync
- [Configuration](/configuration/) - Learn about configuration options
