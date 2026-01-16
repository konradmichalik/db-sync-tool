"""Unit tests for configuration dataclasses.

Tests for db_sync_tool/utility/config.py - typed configuration handling.
"""
import pytest

from db_sync_tool.utility.config import (
    _get,
    _get_int,
    _get_list,
    DatabaseConfig,
    JumpHostConfig,
    ClientConfig,
)


class TestGetHelper:
    """Tests for _get() - safe dictionary access."""

    @pytest.mark.unit
    def test_existing_key(self):
        """Return value when key exists."""
        assert _get({"key": "value"}, "key", "default") == "value"

    @pytest.mark.unit
    def test_missing_key(self):
        """Return default when key missing."""
        assert _get({}, "key", "default") == "default"

    @pytest.mark.unit
    def test_none_value(self):
        """Return default when value is None."""
        assert _get({"key": None}, "key", "default") == "default"

    @pytest.mark.unit
    def test_empty_string(self):
        """Empty string is returned (not treated as None)."""
        assert _get({"key": ""}, "key", "default") == ""

    @pytest.mark.unit
    def test_false_value(self):
        """False is returned (not treated as None)."""
        assert _get({"key": False}, "key", True) is False

    @pytest.mark.unit
    def test_zero_value(self):
        """Zero is returned (not treated as None)."""
        assert _get({"key": 0}, "key", 42) == 0


class TestGetIntHelper:
    """Tests for _get_int() - integer conversion."""

    @pytest.mark.unit
    def test_integer_value(self):
        """Return integer directly."""
        assert _get_int({"port": 3306}, "port", 22) == 3306

    @pytest.mark.unit
    def test_string_value(self):
        """Convert string to integer."""
        assert _get_int({"port": "3306"}, "port", 22) == 3306

    @pytest.mark.unit
    def test_missing_key(self):
        """Return default when key missing."""
        assert _get_int({}, "port", 22) == 22

    @pytest.mark.unit
    def test_invalid_string(self):
        """Return default for invalid string."""
        assert _get_int({"port": "invalid"}, "port", 22) == 22

    @pytest.mark.unit
    def test_none_value(self):
        """Return default when value is None."""
        assert _get_int({"port": None}, "port", 22) == 22

    @pytest.mark.unit
    def test_float_string(self):
        """Handle float string (truncates)."""
        assert _get_int({"port": "3306.5"}, "port", 22) == 22  # fails int()


class TestGetListHelper:
    """Tests for _get_list() - list access with fallback."""

    @pytest.mark.unit
    def test_existing_list(self):
        """Return list when key exists."""
        assert _get_list({"items": [1, 2, 3]}, "items") == [1, 2, 3]

    @pytest.mark.unit
    def test_missing_key(self):
        """Return empty list when key missing."""
        assert _get_list({}, "items") == []

    @pytest.mark.unit
    def test_fallback_key(self):
        """Use fallback key when primary missing."""
        data = {"ignore_table": ["users"]}
        assert _get_list(data, "ignore_tables", "ignore_table") == ["users"]

    @pytest.mark.unit
    def test_primary_over_fallback(self):
        """Primary key takes precedence over fallback."""
        data = {"ignore_tables": ["a"], "ignore_table": ["b"]}
        assert _get_list(data, "ignore_tables", "ignore_table") == ["a"]

    @pytest.mark.unit
    def test_none_value(self):
        """Return empty list when value is None."""
        assert _get_list({"items": None}, "items") == []


class TestDatabaseConfig:
    """Tests for DatabaseConfig dataclass."""

    @pytest.mark.unit
    def test_from_dict_full(self):
        """Create from complete dictionary."""
        data = {
            "name": "mydb",
            "host": "localhost",
            "port": "3306",
            "user": "admin",
            "password": "secret"
        }
        config = DatabaseConfig.from_dict(data)
        assert config.name == "mydb"
        assert config.host == "localhost"
        assert config.port == 3306
        assert config.user == "admin"
        assert config.password == "secret"

    @pytest.mark.unit
    def test_from_dict_minimal(self):
        """Create from minimal dictionary."""
        config = DatabaseConfig.from_dict({"name": "testdb"})
        assert config.name == "testdb"
        assert config.host == ""  # empty default (frameworks fill in)
        assert config.port == 0  # zero default (frameworks use 3306)

    @pytest.mark.unit
    def test_from_dict_none(self):
        """Create from None returns defaults."""
        config = DatabaseConfig.from_dict(None)
        assert config.name == ""
        assert config.host == ""
        assert config.port == 0

    @pytest.mark.unit
    def test_from_dict_empty(self):
        """Create from empty dict returns defaults."""
        config = DatabaseConfig.from_dict({})
        assert config.name == ""


class TestJumpHostConfig:
    """Tests for JumpHostConfig dataclass."""

    @pytest.mark.unit
    def test_from_dict_full(self):
        """Create from complete dictionary."""
        data = {
            "host": "jump.example.com",
            "user": "jumpuser",
            "port": "2222",
            "password": "secret"
        }
        config = JumpHostConfig.from_dict(data)
        assert config.host == "jump.example.com"
        assert config.user == "jumpuser"
        assert config.port == 2222
        assert config.password == "secret"

    @pytest.mark.unit
    def test_from_dict_none(self):
        """None input returns None."""
        assert JumpHostConfig.from_dict(None) is None

    @pytest.mark.unit
    def test_from_dict_empty(self):
        """Empty dict returns None (no host)."""
        assert JumpHostConfig.from_dict({}) is None

    @pytest.mark.unit
    def test_from_dict_no_host(self):
        """Dict without host returns config with empty host."""
        config = JumpHostConfig.from_dict({"user": "admin"})
        assert config.host == ""
        assert config.user == "admin"


class TestClientConfig:
    """Tests for ClientConfig dataclass."""

    @pytest.mark.unit
    def test_from_dict_local(self):
        """Create local client config."""
        data = {"path": "/var/www/config.php"}
        config = ClientConfig.from_dict(data)
        assert config.path == "/var/www/config.php"
        assert config.host == ""
        assert config.is_remote is False

    @pytest.mark.unit
    def test_from_dict_remote(self):
        """Create remote client config."""
        data = {
            "host": "server.example.com",
            "user": "admin",
            "password": "secret",
            "path": "/var/www/config.php"
        }
        config = ClientConfig.from_dict(data)
        assert config.host == "server.example.com"
        assert config.user == "admin"
        assert config.is_remote is True

    @pytest.mark.unit
    def test_from_dict_with_db(self):
        """Create config with database settings."""
        data = {
            "path": "/var/www",
            "db": {"name": "mydb", "user": "dbuser"}
        }
        config = ClientConfig.from_dict(data)
        assert config.db.name == "mydb"
        assert config.db.user == "dbuser"

    @pytest.mark.unit
    def test_from_dict_with_jump_host(self):
        """Create config with jump host."""
        data = {
            "host": "target.internal",
            "user": "admin",
            "jump_host": {
                "host": "jump.example.com",
                "user": "jumpuser"
            }
        }
        config = ClientConfig.from_dict(data)
        assert config.jump_host is not None
        assert config.jump_host.host == "jump.example.com"

    @pytest.mark.unit
    def test_is_remote_property(self):
        """Test is_remote property."""
        local = ClientConfig(path="/var/www")
        assert local.is_remote is False

        remote = ClientConfig(host="server.com", user="admin")
        assert remote.is_remote is True

    @pytest.mark.unit
    def test_from_dict_none(self):
        """None input returns default config."""
        config = ClientConfig.from_dict(None)
        assert config.path == ""
        assert config.host == ""
