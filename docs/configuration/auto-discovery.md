# Auto-Discovery Configuration

The tool supports automatic configuration discovery for faster and more convenient workflows. Instead of always specifying `-f config.yaml`, you can organize your configurations for quick access.

## Configuration Lookup Order

When you run `db_sync_tool`, it searches for configuration in this order:

1. **Explicit file** (`-f config.yaml`) - Uses that file directly
2. **Project config by name** (`db_sync_tool prod`) - Loads `.db-sync-tool/prod.yaml`
3. **Host references** (`db_sync_tool production local`) - Uses hosts from `~/.db-sync-tool/hosts.yaml`
4. **Interactive selection** (no args) - Prompts user to select from available configs
5. **Error** - If nothing found

## Global Hosts

Define reusable host configurations in your home directory. These can be referenced from any project.

### Directory Structure

```text
~/.db-sync-tool/
├── hosts.yaml       # Host definitions
└── defaults.yaml    # Global defaults (optional)
```

### Example hosts.yaml

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

### Example defaults.yaml

```yaml
type: TYPO3
ignore_table:
  - cache_*
  - cf_*
  - sys_log
use_rsync: true
```

### Usage

```bash
# Sync production → local using host definitions
db_sync_tool production local

# Interactive host selection
db_sync_tool
```

## Project Configs

Create project-specific sync configurations in a `.db-sync-tool/` directory within your project. The tool searches the current directory and parent directories.

### Directory Structure

```text
myproject/
├── .db-sync-tool/
│   ├── prod.yaml       # Sync production → local
│   ├── staging.yaml    # Sync staging → local
│   └── defaults.yaml   # Project-specific defaults (optional)
├── src/
└── ...
```

### Example prod.yaml

```yaml
origin: production      # Reference to host in ~/.db-sync-tool/hosts.yaml
target: local
ignore_table:
  - tx_solr_*          # Project-specific tables to ignore
```

### Inline Configuration

```yaml
origin:
  host: custom.example.com
  user: deploy
  path: /var/www/app/.env
target:
  path: /home/dev/project/.env
type: Symfony
```

### Usage

```bash
# Load .db-sync-tool/prod.yaml
db_sync_tool prod

# Load .db-sync-tool/staging.yaml
db_sync_tool staging

# Interactive selection if multiple configs exist
db_sync_tool
```

## Configuration Merging

Configurations are merged in this order (later values override earlier):

1. **Global defaults** (`~/.db-sync-tool/defaults.yaml`)
2. **Project defaults** (`.db-sync-tool/defaults.yaml`)
3. **Project config** (`.db-sync-tool/[name].yaml`)
4. **CLI arguments** (`--target-host`, etc.)

This allows you to define common settings once and override them per-project or per-sync.

## Protected Hosts

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

## Interactive Mode

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
