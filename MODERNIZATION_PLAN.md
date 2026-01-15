# db-sync-tool Modernisierungsplan v3.0

**Erstellt:** 2026-01-14
**Prioritäten:** Sicherheit > Performance > Code-Qualität
**Python-Version:** 3.8+
**Breaking Changes:** Erlaubt (Major Version)

---

## Übersicht gefundener Probleme

| Kategorie | Kritisch | Hoch | Mittel | Niedrig |
|-----------|----------|------|--------|---------|
| **Sicherheit** | 4 | 4 | 4 | 2 |
| **Performance** | 3 | 1 | 4 | 4 |
| **KISS/DRY** | 4 | 4 | 4 | 5 |

---

# Phase 1: Sicherheit (KRITISCH)

## Task 1.1: MySQL Credentials aus Kommandozeile entfernen ⏳ IN PROGRESS
**Priorität:** KRITISCH | **Aufwand:** Mittel | **Dateien:** `database/utility.py`, `database/process.py`

**Problem:** Passwörter sind in `ps aux` sichtbar via `-p'password'`

**Status:** Implementierung gestartet, im Git-Stash gespeichert:
```bash
git stash pop  # Zum Wiederherstellen
```

**Lösung:** MySQL `--defaults-file` Option verwenden:
```python
def create_mysql_config_file(client: str) -> str:
    """Create temporary MySQL config file with credentials."""
    # Config-Datei mit chmod 600 erstellen
    # Automatisches Cleanup im finally-Block
```

---

## Task 1.2: Command Injection Prevention
**Priorität:** KRITISCH | **Aufwand:** Hoch | **Dateien:** `utility/mode.py`

**Problem:** `shell=True` mit unescapten Strings in `subprocess.Popen()`

**Lösung:**
```python
import shlex
# Option A: shlex.split für shell=False
cmd_list = shlex.split(command)
res = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
```

---

## Task 1.3: SQL Injection in Tabellennamen verhindern
**Priorität:** HOCH | **Aufwand:** Niedrig | **Dateien:** `database/utility.py`

**Problem:** Tabellennamen werden ungefiltert in SQL eingefügt (Zeile 75-79)

**Lösung:**
```python
import re

def sanitize_table_name(table: str) -> str:
    if not re.match(r'^[a-zA-Z0-9_]+$', table):
        raise ValueError(f"Invalid table name: {table}")
    return f"`{table}`"
```

---

## Task 1.4: SSH Host Key Verifizierung aktivieren
**Priorität:** HOCH | **Aufwand:** Niedrig | **Dateien:** `remote/client.py`

**Problem:** `AutoAddPolicy()` erlaubt MITM-Angriffe (Zeile 47)

**Lösung:**
```python
_ssh_client.load_system_host_keys()
_ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy())
```

---

## Task 1.5: Sichere Temp-Datei Handhabung
**Priorität:** HOCH | **Aufwand:** Niedrig | **Dateien:** `utility/system.py`

**Problem:** Vorhersehbare Pfade `/tmp/db_sync_tool/`

**Lösung:**
```python
import tempfile
import secrets

def get_secure_temp_dir() -> str:
    random_suffix = secrets.token_hex(8)
    temp_dir = tempfile.mkdtemp(prefix=f'db_sync_tool_{random_suffix}_')
    os.chmod(temp_dir, 0o700)
    return temp_dir
```

---

## Task 1.6: Credentials aus Logs entfernen
**Priorität:** HOCH | **Aufwand:** Niedrig | **Dateien:** `utility/mode.py`

**Problem:** Verbose-Modus zeigt Passwörter (Zeile 295-300)

**Lösung:**
```python
def sanitize_command_for_logging(cmd: str) -> str:
    patterns = [
        (r"-p'[^']*'", "-p'***'"),
        (r"SSHPASS='[^']*'", "SSHPASS='***'"),
    ]
    for pattern, replacement in patterns:
        cmd = re.sub(pattern, replacement, cmd)
    return cmd
```

---

# Phase 2: Performance

## Task 2.1: mysqldump Optimierungen
**Priorität:** HOCH | **Aufwand:** Niedrig | **Dateien:** `database/process.py`

**Lösung:**
```python
_mysqldump_options = (
    '--single-transaction '  # Konsistenter Snapshot ohne Locks
    '--quick '               # Row-by-row streaming
    '--extended-insert '     # Multi-row INSERTs (50% kleiner)
    '--no-tablespaces '
)
```
**Ergebnis:** 50-80% schnellere Dumps, 30-60% kleinere Dateien

---

## Task 2.2: rsync als Standard-Transfer
**Priorität:** HOCH | **Aufwand:** Niedrig | **Dateien:** `utility/system.py`

**Änderung:** `'use_rsync': True` als Default setzen

**Ergebnis:** 5-10x schnellere Transfers (vs. Paramiko SFTP)

---

## Task 2.3: Streaming Kompression/Dekompression
**Priorität:** MITTEL | **Aufwand:** Mittel | **Dateien:** `database/process.py`

**Aktuell:** Dump → Datei → Komprimieren → Datei (doppelte I/O)
**Neu:** `mysqldump ... | gzip > dump.sql.gz`

**Ergebnis:** 50% weniger I/O, 40% schnellerer Start

---

## Task 2.4: Batch-Operationen für Tabellen
**Priorität:** MITTEL | **Aufwand:** Niedrig | **Dateien:** `database/utility.py`

**Problem:** Einzelne SQL-Queries pro Tabelle bei truncate/ignore

**Lösung:** Alle Tabellen in einer SQL-Query verarbeiten

**Ergebnis:** 80-90% weniger Netzwerk-Roundtrips

---

## Task 2.5: Effizienter Database Clear
**Priorität:** NIEDRIG | **Aufwand:** Mittel | **Dateien:** `database/process.py`

**Aktuell:** Komplexe Shell-Pipeline mit 3 Prozessen (Zeile 195-222)
**Neu:** Einzelne SQL-Query via `information_schema`

---

# Phase 3: Architektur & DRY

## Task 3.1: Configuration Dataclass einführen
**Priorität:** HOCH | **Aufwand:** Hoch | **Dateien:** Neue Datei + alle Module

**Problem:** Globaler `config` Dict überall (`utility/system.py`)

**Lösung:**
```python
from dataclasses import dataclass, field

@dataclass
class DatabaseConfig:
    name: str
    host: str = 'localhost'
    user: str = ''
    password: str = ''
    port: int = 3306

@dataclass
class SyncConfig:
    verbose: bool = False
    origin: ClientConfig = field(default_factory=ClientConfig)
    target: ClientConfig = field(default_factory=ClientConfig)
```

---

## Task 3.2: build_config() Refactoring
**Priorität:** HOCH | **Aufwand:** Mittel | **Dateien:** `utility/system.py`

**Problem:** ~120 Zeilen fast identischer if-Statements (Zeile 138-260)

**Lösung:** Mapping-basierter Ansatz
```python
ARG_MAPPINGS = {
    'target_path': (Client.TARGET, 'path'),
    'target_host': (Client.TARGET, 'host'),
    # ...
}
for arg_name, (config_key, nested_key) in ARG_MAPPINGS.items():
    # ...
```
**Ergebnis:** ~120 Zeilen → ~30 Zeilen

---

## Task 3.3: Recipe Base Class
**Priorität:** MITTEL | **Aufwand:** Mittel | **Dateien:** `recipes/*.py`

**Problem:** 5 Recipe-Dateien mit identischer Struktur

**Lösung:** Abstract Base Class mit `parse_credentials()` Methode

---

## Task 3.4: SSH Client Manager Class
**Priorität:** MITTEL | **Aufwand:** Mittel | **Dateien:** `remote/client.py`

**Problem:** Globale Variablen für SSH Clients (Zeile 12-14)

**Lösung:** Context Manager für SSH-Verbindungen

---

## Task 3.5: Transfer Status Funktion vereinheitlichen
**Priorität:** NIEDRIG | **Aufwand:** Niedrig | **Dateien:** `remote/transfer.py`

**Problem:** `download_status()` und `upload_status()` sind 90% identisch

---

# Phase 4: Python Modernisierung

## Task 4.1: Type Hints hinzufügen
**Priorität:** MITTEL | **Aufwand:** Hoch | **Dateien:** Alle

## Task 4.2: pathlib statt String-Manipulation
**Priorität:** NIEDRIG | **Aufwand:** Mittel

## Task 4.3: f-strings konsequent verwenden
**Priorität:** NIEDRIG | **Aufwand:** Niedrig

## Task 4.4: `# -*- coding: future_fstrings -*-` entfernen
**Priorität:** NIEDRIG | **Aufwand:** Niedrig | **Dateien:** Alle Python-Dateien

---

# Phase 5: Testing & Dokumentation

## Task 5.1: Unit Test Framework aufsetzen
**Priorität:** HOCH | **Aufwand:** Mittel

## Task 5.2: Integration Tests für Security-Fixes
**Priorität:** HOCH | **Aufwand:** Mittel

---

# Empfohlene Reihenfolge

| Phase | Tasks | Priorität | Aufwand |
|-------|-------|-----------|---------|
| **1. Sicherheit** | 1.1-1.6 | KRITISCH | Mittel |
| **2. Performance** | 2.1-2.2 | HOCH | Niedrig |
| **3.1 Config Dataclass** | 3.1 | HOCH | Hoch |
| **3.2 DRY Refactoring** | 3.2-3.5 | MITTEL | Mittel |
| **4. Modernisierung** | 4.1-4.4 | NIEDRIG | Mittel |
| **5. Testing** | 5.1-5.2 | HOCH | Mittel |

---

# Fortschritt

- [x] Analyse abgeschlossen
- [ ] Task 1.1: MySQL Credentials (in Stash)
- [ ] Task 1.2-1.6: Weitere Security-Fixes
- [ ] Task 2.x: Performance
- [ ] Task 3.x: Architektur
- [ ] Task 4.x: Modernisierung
- [ ] Task 5.x: Testing
