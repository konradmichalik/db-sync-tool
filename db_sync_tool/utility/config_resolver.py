#!/usr/bin/env python3

"""
Config Resolver Module

Provides automatic configuration discovery and interactive host selection.

Lookup order:
1. -f specified?                      → Load that file
2. .db-sync-tool/[name].yaml?         → Load project config
3. ~/.db-sync-tool/hosts.yaml + name? → Use host reference
4. No args + .db-sync-tool/?          → Interactive config selection
5. No args + ~/.db-sync-tool/?        → Interactive host selection
6. Nothing found?                     → Error (as before)
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt

from db_sync_tool.utility.exceptions import ConfigError, NoConfigFoundError

logger = logging.getLogger('db_sync_tool.config_resolver')


# Directory names
GLOBAL_CONFIG_DIR = '.db-sync-tool'
PROJECT_CONFIG_DIR = '.db-sync-tool'

# File names
HOSTS_FILE = 'hosts.yaml'
DEFAULTS_FILE = 'defaults.yaml'


@dataclass
class HostDefinition:
    """A single host definition from hosts.yaml."""

    name: str
    host: str | None = None
    user: str | None = None
    path: str | None = None
    port: int | None = None
    ssh_key: str | None = None
    protect: bool = False
    db: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> 'HostDefinition':
        """Create HostDefinition from dictionary."""
        return cls(
            name=name,
            host=data.get('host'),
            user=data.get('user'),
            path=data.get('path'),
            port=data.get('port'),
            ssh_key=data.get('ssh_key'),
            protect=data.get('protect', False),
            db=data.get('db', {}),
        )

    def to_client_config(self) -> dict[str, Any]:
        """Convert to client configuration dictionary."""
        config: dict[str, Any] = {}
        if self.host:
            config['host'] = self.host
        if self.user:
            config['user'] = self.user
        if self.path:
            config['path'] = self.path
        if self.port:
            config['port'] = self.port
        if self.ssh_key:
            config['ssh_key'] = self.ssh_key
        if self.db:
            config['db'] = self.db
        return config

    @property
    def is_remote(self) -> bool:
        """Check if this host is remote (has SSH host)."""
        return self.host is not None

    @property
    def display_name(self) -> str:
        """Get display name for UI."""
        if self.host:
            return f"{self.name} ({self.host})"
        return f"{self.name} (local)"


@dataclass
class ProjectConfig:
    """A project-specific sync configuration."""

    name: str
    file_path: Path
    origin: str | dict[str, Any] | None = None
    target: str | dict[str, Any] | None = None
    config: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_file(cls, file_path: Path) -> 'ProjectConfig':
        """Load project config from YAML file."""
        with open(file_path) as f:
            data = yaml.safe_load(f) or {}

        return cls(
            name=file_path.stem,
            file_path=file_path,
            origin=data.get('origin'),
            target=data.get('target'),
            config=data,
        )

    def get_description(self, hosts: dict[str, HostDefinition]) -> str:
        """Get human-readable description of the sync."""
        origin_name = self._get_endpoint_name(self.origin, hosts)
        target_name = self._get_endpoint_name(self.target, hosts)
        return f"{origin_name} → {target_name}"

    def _get_endpoint_name(
        self, endpoint: str | dict[str, Any] | None, hosts: dict[str, HostDefinition]
    ) -> str:
        """Get display name for an endpoint."""
        if endpoint is None:
            return "?"
        if isinstance(endpoint, str):
            if endpoint in hosts:
                return hosts[endpoint].display_name
            return endpoint
        if isinstance(endpoint, dict):
            if 'host' in endpoint:
                return endpoint.get('name', endpoint['host'])
            return endpoint.get('name', 'local')
        return str(endpoint)


@dataclass
class ResolvedConfig:
    """Result of config resolution."""

    config_file: Path | None = None
    origin_config: dict[str, Any] = field(default_factory=dict)
    target_config: dict[str, Any] = field(default_factory=dict)
    merged_config: dict[str, Any] = field(default_factory=dict)
    source: str = ""  # Description of where config came from


class ConfigResolver:
    """
    Resolves configuration from multiple sources.

    Supports:
    - Explicit config file (-f config.yaml)
    - Project configs (.db-sync-tool/*.yaml)
    - Global hosts (~/.db-sync-tool/hosts.yaml)
    - Interactive selection when no args provided
    """

    def __init__(self, console: Console | None = None):
        """
        Initialize ConfigResolver.

        :param console: Rich console for interactive prompts
        """
        self.console = console or Console()
        self._global_dir: Path | None = None
        self._project_dir: Path | None = None
        self._global_hosts: dict[str, HostDefinition] = {}
        self._global_defaults: dict[str, Any] = {}
        self._project_defaults: dict[str, Any] = {}
        self._project_configs: dict[str, ProjectConfig] = {}

    @property
    def global_config_dir(self) -> Path:
        """Get global config directory (~/.db-sync-tool/)."""
        if self._global_dir is None:
            self._global_dir = Path.home() / GLOBAL_CONFIG_DIR
        return self._global_dir

    @property
    def project_config_dir(self) -> Path | None:
        """Get project config directory (.db-sync-tool/ in cwd or parents)."""
        if self._project_dir is None:
            self._project_dir = self._find_project_config_dir()
        return self._project_dir

    def _find_project_config_dir(self) -> Path | None:
        """Search for .db-sync-tool/ directory in cwd and parents."""
        cwd = Path.cwd()
        for parent in [cwd, *cwd.parents]:
            project_dir = parent / PROJECT_CONFIG_DIR
            if project_dir.is_dir():
                return project_dir
        return None

    def load_global_config(self) -> None:
        """Load global hosts and defaults from ~/.db-sync-tool/."""
        if not self.global_config_dir.is_dir():
            return

        # Load hosts.yaml
        hosts_file = self.global_config_dir / HOSTS_FILE
        if hosts_file.is_file():
            with open(hosts_file) as f:
                data = yaml.safe_load(f) or {}
            self._global_hosts = {
                name: HostDefinition.from_dict(name, config)
                for name, config in data.items()
            }

        # Load defaults.yaml
        defaults_file = self.global_config_dir / DEFAULTS_FILE
        if defaults_file.is_file():
            with open(defaults_file) as f:
                self._global_defaults = yaml.safe_load(f) or {}

    def load_project_config(self) -> None:
        """Load project configs from .db-sync-tool/."""
        if self.project_config_dir is None:
            return

        # Load project defaults.yaml
        defaults_file = self.project_config_dir / DEFAULTS_FILE
        if defaults_file.is_file():
            with open(defaults_file) as f:
                self._project_defaults = yaml.safe_load(f) or {}

        # Load all project config files (*.yaml except defaults.yaml)
        for config_file in self.project_config_dir.glob('*.yaml'):
            if config_file.name == DEFAULTS_FILE:
                continue
            try:
                project_config = ProjectConfig.from_file(config_file)
                self._project_configs[project_config.name] = project_config
            except Exception as e:
                logger.warning(
                    f"Failed to load project config '{config_file}': {e}"
                )
                continue

        # Also check *.yml files
        for config_file in self.project_config_dir.glob('*.yml'):
            if config_file.name == 'defaults.yml':
                continue
            try:
                project_config = ProjectConfig.from_file(config_file)
                self._project_configs[project_config.name] = project_config
            except Exception as e:
                logger.warning(
                    f"Failed to load project config '{config_file}': {e}"
                )
                continue

    def resolve(
        self,
        config_file: str | None = None,
        origin: str | None = None,
        target: str | None = None,
        interactive: bool = True,
    ) -> ResolvedConfig:
        """
        Resolve configuration from available sources.

        Lookup order:
        1. Explicit config file (-f)
        2. Project config by name
        3. Host references (origin/target names)
        4. Interactive selection

        :param config_file: Explicit config file path
        :param origin: Origin host name or None
        :param target: Target host name or None
        :param interactive: Allow interactive prompts
        :return: ResolvedConfig with merged configuration
        """
        # Load available configs
        self.load_global_config()
        self.load_project_config()

        # 1. Explicit config file takes priority
        if config_file:
            return self._resolve_explicit_file(Path(config_file))

        # 2. Check if origin arg matches a project config name
        if origin and not target and origin in self._project_configs:
            return self._resolve_project_config(self._project_configs[origin])

        # 3. Origin and target specified as host names
        if origin and target:
            return self._resolve_host_references(origin, target)

        # 4. Interactive selection
        if interactive:
            return self._resolve_interactive()

        raise NoConfigFoundError(
            'Configuration is missing, use a separate file or provide host parameter'
        )

    def _resolve_explicit_file(self, config_file: Path) -> ResolvedConfig:
        """Resolve configuration from explicit file."""
        if not config_file.is_file():
            raise ConfigError(f'Configuration file not found: {config_file}')

        return ResolvedConfig(
            config_file=config_file,
            source=f"explicit file: {config_file}",
        )

    def _resolve_project_config(self, project: ProjectConfig) -> ResolvedConfig:
        """Resolve configuration from project config."""
        # Start with global defaults, then project defaults, then project config
        merged = self._merge_defaults(project.config)

        # Resolve host references in origin/target
        origin_config = self._resolve_endpoint(project.origin)
        target_config = self._resolve_endpoint(project.target)

        return ResolvedConfig(
            config_file=project.file_path,
            origin_config=origin_config,
            target_config=target_config,
            merged_config=merged,
            source=f"project config: {project.name}",
        )

    def _resolve_host_references(self, origin: str, target: str) -> ResolvedConfig:
        """Resolve configuration from host name references."""
        if origin not in self._global_hosts:
            raise ConfigError(
                f"Host '{origin}' not found in {self.global_config_dir / HOSTS_FILE}"
            )
        if target not in self._global_hosts:
            raise ConfigError(
                f"Host '{target}' not found in {self.global_config_dir / HOSTS_FILE}"
            )

        origin_host = self._global_hosts[origin]
        target_host = self._global_hosts[target]

        # Check protect flag
        if target_host.protect:
            self._warn_protected_target(target_host)

        merged = self._merge_defaults({})

        return ResolvedConfig(
            origin_config=origin_host.to_client_config(),
            target_config=target_host.to_client_config(),
            merged_config=merged,
            source=f"host references: {origin} → {target}",
        )

    def _resolve_endpoint(self, endpoint: str | dict[str, Any] | None) -> dict[str, Any]:
        """Resolve a single endpoint (origin or target)."""
        if endpoint is None:
            return {}
        if isinstance(endpoint, str):
            # Host reference
            if endpoint in self._global_hosts:
                return self._global_hosts[endpoint].to_client_config()
            raise ConfigError(
                f"Host '{endpoint}' not found in {self.global_config_dir / HOSTS_FILE}"
            )
        if isinstance(endpoint, dict):
            return endpoint
        return {}

    def _resolve_interactive(self) -> ResolvedConfig:
        """Interactive config/host selection."""
        # Check for project configs first
        if self._project_configs:
            return self._interactive_project_selection()

        # Fall back to global hosts
        if self._global_hosts:
            return self._interactive_host_selection()

        raise NoConfigFoundError(
            "No configuration found. Create .db-sync-tool/ or ~/.db-sync-tool/ "
            "with config files, or use -f to specify a config file."
        )

    def _interactive_project_selection(self) -> ResolvedConfig:
        """Interactive selection from project configs."""
        self.console.print()
        self.console.print(
            Panel(
                f"Project configs found: [cyan]{self.project_config_dir}[/cyan]",
                title="db-sync-tool",
                border_style="cyan",
            )
        )
        self.console.print()

        # List available configs
        configs = list(self._project_configs.values())
        for i, cfg in enumerate(configs, 1):
            desc = cfg.get_description(self._global_hosts)
            self.console.print(f"  [bold cyan][{i}][/bold cyan] {cfg.name:12} {desc}")

        self.console.print()

        # Get user selection
        choice = IntPrompt.ask(
            "Selection",
            choices=[str(i) for i in range(1, len(configs) + 1)],
            console=self.console,
        )

        selected = configs[choice - 1]
        self.console.print()

        # Show preview and confirm
        self._show_sync_preview(selected)

        if not Confirm.ask("Continue?", default=False, console=self.console):
            raise ConfigError("Aborted by user")

        return self._resolve_project_config(selected)

    def _interactive_host_selection(self) -> ResolvedConfig:
        """Interactive selection from global hosts."""
        self.console.print()
        self.console.print(
            Panel(
                f"Global hosts: [cyan]{self.global_config_dir / HOSTS_FILE}[/cyan]",
                title="db-sync-tool",
                border_style="cyan",
            )
        )
        self.console.print()

        # List available hosts
        hosts = list(self._global_hosts.values())
        for i, host in enumerate(hosts, 1):
            protect_marker = " [red](protected)[/red]" if host.protect else ""
            self.console.print(f"  [bold cyan][{i}][/bold cyan] {host.display_name}{protect_marker}")

        self.console.print()

        # Get origin selection
        self.console.print("[bold]Origin (source):[/bold]")
        origin_choice = IntPrompt.ask(
            "Selection",
            choices=[str(i) for i in range(1, len(hosts) + 1)],
            console=self.console,
        )
        origin_host = hosts[origin_choice - 1]

        self.console.print()

        # Get target selection
        self.console.print("[bold]Target (destination):[/bold]")
        target_choice = IntPrompt.ask(
            "Selection",
            choices=[str(i) for i in range(1, len(hosts) + 1)],
            console=self.console,
        )
        target_host = hosts[target_choice - 1]

        self.console.print()

        # Check protect flag
        if target_host.protect:
            self._warn_protected_target(target_host)

        # Confirm
        self.console.print(
            Panel(
                f"[bold]{origin_host.display_name}[/bold] → [bold]{target_host.display_name}[/bold]",
                title="Sync Preview",
                border_style="yellow",
            )
        )

        if not Confirm.ask("Continue?", default=False, console=self.console):
            raise ConfigError("Aborted by user")

        return self._resolve_host_references(origin_host.name, target_host.name)

    def _show_sync_preview(self, project: ProjectConfig) -> None:
        """Show sync preview panel."""
        desc = project.get_description(self._global_hosts)

        # Check if origin is production
        origin_name = (
            project.origin if isinstance(project.origin, str) else None
        )
        warning = ""
        if origin_name and origin_name in self._global_hosts:
            origin_host = self._global_hosts[origin_name]
            if origin_host.protect:
                warning = "\n[yellow bold]Warning: Production system as source![/yellow bold]"

        self.console.print(
            Panel(
                f"[bold]{desc}[/bold]{warning}",
                title="Sync Preview",
                border_style="yellow",
            )
        )

    def _warn_protected_target(self, host: HostDefinition) -> None:
        """Warn about protected target and require confirmation."""
        self.console.print()
        self.console.print(
            Panel(
                f"[bold red]DANGER![/bold red]\n\n"
                f"Target [bold]{host.display_name}[/bold] is marked as [bold red]protected[/bold red].\n"
                f"This is typically a production system.\n\n"
                f"Syncing to this target will [bold]overwrite[/bold] the database!",
                title="Protected Target",
                border_style="red",
            )
        )
        self.console.print()

        if not Confirm.ask(
            "[bold red]Are you absolutely sure you want to continue?[/bold red]",
            default=False,
            console=self.console,
        ):
            raise ConfigError("Aborted: Target is protected")

    def _merge_defaults(self, config: dict[str, Any]) -> dict[str, Any]:
        """Merge global and project defaults with config."""
        # Start with global defaults
        merged: dict[str, Any] = dict(self._global_defaults)

        # Apply project defaults
        self._deep_merge(merged, self._project_defaults)

        # Apply specific config
        self._deep_merge(merged, config)

        return merged

    def _deep_merge(self, base: dict[str, Any], overlay: dict[str, Any]) -> None:
        """Deep merge overlay into base dict (in-place)."""
        for key, value in overlay.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def has_project_configs(self) -> bool:
        """Check if project configs are available."""
        self.load_project_config()
        return bool(self._project_configs)

    def has_global_hosts(self) -> bool:
        """Check if global hosts are available."""
        self.load_global_config()
        return bool(self._global_hosts)

    def get_project_config_names(self) -> list[str]:
        """Get list of available project config names."""
        self.load_project_config()
        return list(self._project_configs.keys())

    def get_global_host_names(self) -> list[str]:
        """Get list of available global host names."""
        self.load_global_config()
        return list(self._global_hosts.keys())
