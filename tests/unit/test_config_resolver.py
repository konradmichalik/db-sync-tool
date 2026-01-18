"""Unit tests for ConfigResolver - auto-discovery and interactive config selection.

Tests for db_sync_tool/utility/config_resolver.py

Note: These tests require pyyaml and rich to be installed.
When running via pipx without dependencies, tests are automatically skipped.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock

# Skip all tests in this module if dependencies aren't available
try:
    import yaml  # noqa: F401
    import rich  # noqa: F401
    from db_sync_tool.utility.config_resolver import (
        ConfigResolver,
        HostDefinition,
        ProjectConfig,
        ResolvedConfig,
        GLOBAL_CONFIG_DIR,
        PROJECT_CONFIG_DIR,
        HOSTS_FILE,
        DEFAULTS_FILE,
    )
    from db_sync_tool.utility.exceptions import ConfigError, NoConfigFoundError
    DEPS_AVAILABLE = True
except ImportError:
    DEPS_AVAILABLE = False
    # Define placeholders to avoid NameError
    ConfigResolver = None
    HostDefinition = None
    ProjectConfig = None
    ResolvedConfig = None
    GLOBAL_CONFIG_DIR = '.db-sync-tool'
    PROJECT_CONFIG_DIR = '.db-sync-tool'
    HOSTS_FILE = 'hosts.yaml'
    DEFAULTS_FILE = 'defaults.yaml'
    ConfigError = Exception
    NoConfigFoundError = Exception

pytestmark = pytest.mark.skipif(
    not DEPS_AVAILABLE,
    reason="config_resolver tests require pyyaml and rich packages"
)


class TestHostDefinition:
    """Tests for HostDefinition dataclass."""

    @pytest.mark.unit
    def test_from_dict_full(self):
        """Create HostDefinition with all fields."""
        data = {
            "host": "prod.example.com",
            "user": "deploy",
            "path": "/var/www/html/LocalConfiguration.php",
            "port": 22,
            "ssh_key": "/home/user/.ssh/id_rsa",
            "protect": True,
            "db": {"name": "production", "host": "localhost"},
        }
        host = HostDefinition.from_dict("production", data)

        assert host.name == "production"
        assert host.host == "prod.example.com"
        assert host.user == "deploy"
        assert host.path == "/var/www/html/LocalConfiguration.php"
        assert host.port == 22
        assert host.ssh_key == "/home/user/.ssh/id_rsa"
        assert host.protect is True
        assert host.db == {"name": "production", "host": "localhost"}

    @pytest.mark.unit
    def test_from_dict_minimal(self):
        """Create HostDefinition with minimal fields."""
        data = {"path": "/var/www/local/config.php"}
        host = HostDefinition.from_dict("local", data)

        assert host.name == "local"
        assert host.host is None
        assert host.user is None
        assert host.path == "/var/www/local/config.php"
        assert host.protect is False

    @pytest.mark.unit
    def test_from_dict_empty(self):
        """Create HostDefinition from empty dict."""
        host = HostDefinition.from_dict("empty", {})

        assert host.name == "empty"
        assert host.host is None
        assert host.protect is False
        assert host.db == {}

    @pytest.mark.unit
    def test_to_client_config_remote(self):
        """Convert remote host to client config."""
        host = HostDefinition(
            name="production",
            host="prod.example.com",
            user="deploy",
            path="/var/www/html/config.php",
            port=22,
        )
        config = host.to_client_config()

        assert config == {
            "host": "prod.example.com",
            "user": "deploy",
            "path": "/var/www/html/config.php",
            "port": 22,
        }

    @pytest.mark.unit
    def test_to_client_config_local(self):
        """Convert local host to client config."""
        host = HostDefinition(
            name="local",
            path="/var/www/local/config.php",
        )
        config = host.to_client_config()

        assert config == {"path": "/var/www/local/config.php"}
        assert "host" not in config

    @pytest.mark.unit
    def test_is_remote_property(self):
        """Test is_remote property."""
        remote = HostDefinition(name="prod", host="prod.example.com")
        local = HostDefinition(name="local")

        assert remote.is_remote is True
        assert local.is_remote is False

    @pytest.mark.unit
    def test_display_name_remote(self):
        """Test display_name for remote host."""
        host = HostDefinition(name="production", host="prod.example.com")
        assert host.display_name == "production (prod.example.com)"

    @pytest.mark.unit
    def test_display_name_local(self):
        """Test display_name for local host."""
        host = HostDefinition(name="local")
        assert host.display_name == "local (local)"


class TestProjectConfig:
    """Tests for ProjectConfig dataclass."""

    @pytest.mark.unit
    def test_from_file(self, tmp_path):
        """Load project config from YAML file."""
        config_file = tmp_path / "prod.yaml"
        config_file.write_text(
            """
origin: production
target: local
ignore_table:
  - tx_solr_*
"""
        )

        project = ProjectConfig.from_file(config_file)

        assert project.name == "prod"
        assert project.file_path == config_file
        assert project.origin == "production"
        assert project.target == "local"
        assert project.config["ignore_table"] == ["tx_solr_*"]

    @pytest.mark.unit
    def test_from_file_with_dict_origin(self, tmp_path):
        """Load project config with inline origin config."""
        config_file = tmp_path / "custom.yaml"
        config_file.write_text(
            """
origin:
  host: custom.example.com
  user: deploy
  path: /var/www/html/config.php
target: local
"""
        )

        project = ProjectConfig.from_file(config_file)

        assert isinstance(project.origin, dict)
        assert project.origin["host"] == "custom.example.com"
        assert project.target == "local"

    @pytest.mark.unit
    def test_get_description_with_host_refs(self):
        """Get description with host references."""
        hosts = {
            "production": HostDefinition(name="production", host="prod.example.com"),
            "local": HostDefinition(name="local"),
        }
        project = ProjectConfig(
            name="prod",
            file_path=Path("/test/prod.yaml"),
            origin="production",
            target="local",
        )

        desc = project.get_description(hosts)
        assert desc == "production (prod.example.com) → local (local)"

    @pytest.mark.unit
    def test_get_description_with_inline_config(self):
        """Get description with inline endpoint config."""
        hosts = {}
        project = ProjectConfig(
            name="custom",
            file_path=Path("/test/custom.yaml"),
            origin={"host": "custom.example.com", "name": "Custom Server"},
            target={"name": "Local Dev"},
        )

        desc = project.get_description(hosts)
        assert desc == "Custom Server → Local Dev"


class TestResolvedConfig:
    """Tests for ResolvedConfig dataclass."""

    @pytest.mark.unit
    def test_default_values(self):
        """ResolvedConfig has correct defaults."""
        resolved = ResolvedConfig()

        assert resolved.config_file is None
        assert resolved.origin_config == {}
        assert resolved.target_config == {}
        assert resolved.merged_config == {}
        assert resolved.source == ""

    @pytest.mark.unit
    def test_with_values(self):
        """ResolvedConfig stores values correctly."""
        resolved = ResolvedConfig(
            config_file=Path("/test/config.yaml"),
            origin_config={"host": "origin.example.com"},
            target_config={"path": "/local/path"},
            merged_config={"type": "TYPO3"},
            source="test source",
        )

        assert resolved.config_file == Path("/test/config.yaml")
        assert resolved.origin_config == {"host": "origin.example.com"}
        assert resolved.target_config == {"path": "/local/path"}
        assert resolved.merged_config == {"type": "TYPO3"}
        assert resolved.source == "test source"


class TestConfigResolverInit:
    """Tests for ConfigResolver initialization."""

    @pytest.mark.unit
    def test_init_default(self):
        """Create ConfigResolver with defaults."""
        resolver = ConfigResolver()

        assert resolver.console is not None
        assert resolver._global_hosts == {}
        assert resolver._project_configs == {}

    @pytest.mark.unit
    def test_init_with_console(self):
        """Create ConfigResolver with custom console."""
        mock_console = MagicMock()
        resolver = ConfigResolver(console=mock_console)

        assert resolver.console is mock_console


class TestConfigResolverGlobalDir:
    """Tests for global config directory handling."""

    @pytest.mark.unit
    def test_global_config_dir_path(self):
        """Global config dir is in home directory."""
        resolver = ConfigResolver()

        expected = Path.home() / GLOBAL_CONFIG_DIR
        assert resolver.global_config_dir == expected

    @pytest.mark.unit
    def test_load_global_config_no_dir(self, tmp_path, monkeypatch):
        """Handle missing global config dir gracefully."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        resolver = ConfigResolver()
        resolver._global_dir = tmp_path / GLOBAL_CONFIG_DIR

        # Should not raise
        resolver.load_global_config()
        assert resolver._global_hosts == {}

    @pytest.mark.unit
    def test_load_global_hosts(self, tmp_path):
        """Load hosts from global hosts.yaml."""
        global_dir = tmp_path / GLOBAL_CONFIG_DIR
        global_dir.mkdir()

        hosts_file = global_dir / HOSTS_FILE
        hosts_file.write_text(
            """
production:
  host: prod.example.com
  user: deploy
  protect: true

local:
  path: /var/www/local/config.php
"""
        )

        resolver = ConfigResolver()
        resolver._global_dir = global_dir
        resolver.load_global_config()

        assert "production" in resolver._global_hosts
        assert "local" in resolver._global_hosts
        assert resolver._global_hosts["production"].host == "prod.example.com"
        assert resolver._global_hosts["production"].protect is True
        assert resolver._global_hosts["local"].is_remote is False

    @pytest.mark.unit
    def test_load_global_defaults(self, tmp_path):
        """Load defaults from global defaults.yaml."""
        global_dir = tmp_path / GLOBAL_CONFIG_DIR
        global_dir.mkdir()

        defaults_file = global_dir / DEFAULTS_FILE
        defaults_file.write_text(
            """
type: TYPO3
ignore_table:
  - cache_*
  - cf_*
"""
        )

        resolver = ConfigResolver()
        resolver._global_dir = global_dir
        resolver.load_global_config()

        assert resolver._global_defaults["type"] == "TYPO3"
        assert "cache_*" in resolver._global_defaults["ignore_table"]


class TestConfigResolverProjectDir:
    """Tests for project config directory handling."""

    @pytest.mark.unit
    def test_find_project_config_dir_in_cwd(self, tmp_path, monkeypatch):
        """Find project config dir in current directory."""
        project_dir = tmp_path / PROJECT_CONFIG_DIR
        project_dir.mkdir()

        monkeypatch.chdir(tmp_path)
        resolver = ConfigResolver()

        assert resolver.project_config_dir == project_dir

    @pytest.mark.unit
    def test_find_project_config_dir_in_parent(self, tmp_path, monkeypatch):
        """Find project config dir in parent directory."""
        project_dir = tmp_path / PROJECT_CONFIG_DIR
        project_dir.mkdir()

        subdir = tmp_path / "subdir" / "deep"
        subdir.mkdir(parents=True)

        monkeypatch.chdir(subdir)
        resolver = ConfigResolver()

        assert resolver.project_config_dir == project_dir

    @pytest.mark.unit
    def test_project_config_dir_not_found(self, tmp_path, monkeypatch):
        """Handle missing project config dir."""
        monkeypatch.chdir(tmp_path)
        resolver = ConfigResolver()

        assert resolver.project_config_dir is None

    @pytest.mark.unit
    def test_load_project_configs(self, tmp_path, monkeypatch):
        """Load project configs from directory."""
        project_dir = tmp_path / PROJECT_CONFIG_DIR
        project_dir.mkdir()

        prod_config = project_dir / "prod.yaml"
        prod_config.write_text(
            """
origin: production
target: local
"""
        )

        staging_config = project_dir / "staging.yaml"
        staging_config.write_text(
            """
origin: staging
target: local
"""
        )

        monkeypatch.chdir(tmp_path)
        resolver = ConfigResolver()
        resolver.load_project_config()

        assert "prod" in resolver._project_configs
        assert "staging" in resolver._project_configs
        assert resolver._project_configs["prod"].origin == "production"

    @pytest.mark.unit
    def test_load_project_defaults(self, tmp_path, monkeypatch):
        """Load project-specific defaults."""
        project_dir = tmp_path / PROJECT_CONFIG_DIR
        project_dir.mkdir()

        defaults = project_dir / DEFAULTS_FILE
        defaults.write_text(
            """
type: Symfony
ignore_table:
  - messenger_messages
"""
        )

        monkeypatch.chdir(tmp_path)
        resolver = ConfigResolver()
        resolver.load_project_config()

        assert resolver._project_defaults["type"] == "Symfony"


class TestConfigResolverResolve:
    """Tests for config resolution logic."""

    @pytest.mark.unit
    def test_resolve_explicit_file(self, tmp_path):
        """Resolve from explicit config file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
origin:
  host: prod.example.com
target:
  path: /local/path
"""
        )

        resolver = ConfigResolver()
        result = resolver.resolve(
            config_file=str(config_file), interactive=False
        )

        assert result.config_file == config_file
        assert result.source == f"explicit file: {config_file}"

    @pytest.mark.unit
    def test_resolve_explicit_file_not_found(self, tmp_path):
        """Raise error for missing explicit config file."""
        resolver = ConfigResolver()

        with pytest.raises(ConfigError) as exc:
            resolver.resolve(
                config_file=str(tmp_path / "missing.yaml"), interactive=False
            )

        assert "not found" in str(exc.value)

    @pytest.mark.unit
    def test_resolve_project_config_by_name(self, tmp_path, monkeypatch):
        """Resolve project config by name (origin arg matches config name)."""
        # Setup global hosts
        global_dir = tmp_path / "home" / GLOBAL_CONFIG_DIR
        global_dir.mkdir(parents=True)
        (global_dir / HOSTS_FILE).write_text(
            """
production:
  host: prod.example.com
local:
  path: /local
"""
        )

        # Setup project config
        project_dir = tmp_path / PROJECT_CONFIG_DIR
        project_dir.mkdir()
        (project_dir / "prod.yaml").write_text(
            """
origin: production
target: local
"""
        )

        monkeypatch.chdir(tmp_path)
        resolver = ConfigResolver()
        resolver._global_dir = global_dir

        result = resolver.resolve(origin="prod", interactive=False)

        assert "project config: prod" in result.source
        assert result.origin_config["host"] == "prod.example.com"
        assert result.target_config["path"] == "/local"

    @pytest.mark.unit
    def test_resolve_host_references(self, tmp_path):
        """Resolve from host name references."""
        global_dir = tmp_path / GLOBAL_CONFIG_DIR
        global_dir.mkdir()
        (global_dir / HOSTS_FILE).write_text(
            """
production:
  host: prod.example.com
  user: deploy
staging:
  host: staging.example.com
  user: deploy
"""
        )

        resolver = ConfigResolver()
        resolver._global_dir = global_dir

        result = resolver.resolve(
            origin="production", target="staging", interactive=False
        )

        assert result.origin_config["host"] == "prod.example.com"
        assert result.target_config["host"] == "staging.example.com"
        assert "production → staging" in result.source

    @pytest.mark.unit
    def test_resolve_host_not_found(self, tmp_path):
        """Raise error when host not found."""
        global_dir = tmp_path / GLOBAL_CONFIG_DIR
        global_dir.mkdir()
        (global_dir / HOSTS_FILE).write_text(
            """
production:
  host: prod.example.com
"""
        )

        resolver = ConfigResolver()
        resolver._global_dir = global_dir

        with pytest.raises(ConfigError) as exc:
            resolver.resolve(
                origin="production", target="missing", interactive=False
            )

        assert "missing" in str(exc.value)

    @pytest.mark.unit
    def test_resolve_no_config_non_interactive(self, tmp_path, monkeypatch):
        """Raise NoConfigFoundError when no config found and interactive disabled."""
        monkeypatch.chdir(tmp_path)
        resolver = ConfigResolver()
        resolver._global_dir = tmp_path / "empty"

        with pytest.raises(NoConfigFoundError) as exc:
            resolver.resolve(interactive=False)

        assert "Configuration is missing" in str(exc.value)


class TestConfigResolverMerge:
    """Tests for config merging logic."""

    @pytest.mark.unit
    def test_merge_global_defaults(self, tmp_path):
        """Global defaults are applied to config."""
        global_dir = tmp_path / GLOBAL_CONFIG_DIR
        global_dir.mkdir()
        (global_dir / DEFAULTS_FILE).write_text(
            """
type: TYPO3
ignore_table:
  - cache_*
"""
        )
        (global_dir / HOSTS_FILE).write_text(
            """
production:
  host: prod.example.com
local:
  path: /local
"""
        )

        resolver = ConfigResolver()
        resolver._global_dir = global_dir

        result = resolver.resolve(
            origin="production", target="local", interactive=False
        )

        assert result.merged_config["type"] == "TYPO3"
        assert "cache_*" in result.merged_config["ignore_table"]

    @pytest.mark.unit
    def test_merge_project_overrides_global(self, tmp_path, monkeypatch):
        """Project defaults override global defaults."""
        # Global defaults
        global_dir = tmp_path / "home" / GLOBAL_CONFIG_DIR
        global_dir.mkdir(parents=True)
        (global_dir / DEFAULTS_FILE).write_text(
            """
type: TYPO3
use_rsync: true
"""
        )
        (global_dir / HOSTS_FILE).write_text(
            """
production:
  host: prod.example.com
local:
  path: /local
"""
        )

        # Project defaults
        project_dir = tmp_path / PROJECT_CONFIG_DIR
        project_dir.mkdir()
        (project_dir / DEFAULTS_FILE).write_text(
            """
type: Symfony
"""
        )
        (project_dir / "prod.yaml").write_text(
            """
origin: production
target: local
"""
        )

        monkeypatch.chdir(tmp_path)
        resolver = ConfigResolver()
        resolver._global_dir = global_dir

        result = resolver.resolve(origin="prod", interactive=False)

        # Project type overrides global
        assert result.merged_config["type"] == "Symfony"
        # Global use_rsync is preserved
        assert result.merged_config["use_rsync"] is True

    @pytest.mark.unit
    def test_deep_merge(self):
        """Deep merge handles nested dictionaries."""
        resolver = ConfigResolver()

        base = {
            "db": {"host": "localhost", "port": 3306},
            "other": "value",
        }
        overlay = {
            "db": {"user": "root"},
        }

        resolver._deep_merge(base, overlay)

        assert base["db"]["host"] == "localhost"  # preserved
        assert base["db"]["port"] == 3306  # preserved
        assert base["db"]["user"] == "root"  # added
        assert base["other"] == "value"  # preserved


class TestConfigResolverProtect:
    """Tests for protect feature."""

    @pytest.mark.unit
    def test_protected_target_detection(self, tmp_path):
        """Protected targets are detected."""
        global_dir = tmp_path / GLOBAL_CONFIG_DIR
        global_dir.mkdir()
        (global_dir / HOSTS_FILE).write_text(
            """
production:
  host: prod.example.com
  protect: true
local:
  path: /local
"""
        )

        resolver = ConfigResolver()
        resolver._global_dir = global_dir
        resolver.load_global_config()

        assert resolver._global_hosts["production"].protect is True
        assert resolver._global_hosts["local"].protect is False


class TestConfigResolverHelpers:
    """Tests for helper methods."""

    @pytest.mark.unit
    def test_has_project_configs(self, tmp_path, monkeypatch):
        """Check for available project configs."""
        project_dir = tmp_path / PROJECT_CONFIG_DIR
        project_dir.mkdir()
        (project_dir / "prod.yaml").write_text("origin: prod\n")

        monkeypatch.chdir(tmp_path)
        resolver = ConfigResolver()

        assert resolver.has_project_configs() is True

    @pytest.mark.unit
    def test_has_project_configs_empty(self, tmp_path, monkeypatch):
        """Return False when no project configs."""
        monkeypatch.chdir(tmp_path)
        resolver = ConfigResolver()

        assert resolver.has_project_configs() is False

    @pytest.mark.unit
    def test_has_global_hosts(self, tmp_path):
        """Check for available global hosts."""
        global_dir = tmp_path / GLOBAL_CONFIG_DIR
        global_dir.mkdir()
        (global_dir / HOSTS_FILE).write_text("production:\n  host: prod.example.com\n")

        resolver = ConfigResolver()
        resolver._global_dir = global_dir

        assert resolver.has_global_hosts() is True

    @pytest.mark.unit
    def test_get_project_config_names(self, tmp_path, monkeypatch):
        """Get list of project config names."""
        project_dir = tmp_path / PROJECT_CONFIG_DIR
        project_dir.mkdir()
        (project_dir / "prod.yaml").write_text("origin: prod\n")
        (project_dir / "staging.yaml").write_text("origin: staging\n")

        monkeypatch.chdir(tmp_path)
        resolver = ConfigResolver()

        names = resolver.get_project_config_names()
        assert "prod" in names
        assert "staging" in names

    @pytest.mark.unit
    def test_get_global_host_names(self, tmp_path):
        """Get list of global host names."""
        global_dir = tmp_path / GLOBAL_CONFIG_DIR
        global_dir.mkdir()
        (global_dir / HOSTS_FILE).write_text(
            """
production:
  host: prod.example.com
staging:
  host: staging.example.com
"""
        )

        resolver = ConfigResolver()
        resolver._global_dir = global_dir

        names = resolver.get_global_host_names()
        assert "production" in names
        assert "staging" in names
