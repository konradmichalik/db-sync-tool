"""Unit tests for pure utility functions.

Tests for db_sync_tool/utility/pure.py - helper functions with no dependencies.
"""
import pytest

from db_sync_tool.utility.pure import (
    parse_version,
    get_file_from_path,
    remove_surrounding_quotes,
    clean_db_config,
    dict_to_args,
    remove_multiple_elements_from_string,
)


class TestParseVersion:
    """Tests for parse_version() - version string extraction."""

    @pytest.mark.unit
    def test_rsync_version(self):
        """Extract version from rsync output."""
        output = "rsync  version 3.2.7  protocol version 31"
        assert parse_version(output) == "3.2.7"

    @pytest.mark.unit
    def test_sshpass_version(self):
        """Extract version from sshpass output."""
        output = "sshpass 1.10"
        assert parse_version(output) == "1.10"

    @pytest.mark.unit
    def test_mysql_version(self):
        """Extract version from mysql output."""
        output = "mysql  Ver 8.0.32 for Linux on x86_64"
        assert parse_version(output) == "8.0.32"

    @pytest.mark.unit
    def test_mariadb_version(self):
        """Extract version from MariaDB output."""
        output = "mariadb from 11.4.2-MariaDB, client 15.2"
        assert parse_version(output) == "11.4.2"

    @pytest.mark.unit
    def test_simple_version(self):
        """Extract simple version number."""
        assert parse_version("Version 1.0") == "1.0"

    @pytest.mark.unit
    def test_none_input(self):
        """None input returns None."""
        assert parse_version(None) is None

    @pytest.mark.unit
    def test_empty_string(self):
        """Empty string returns None."""
        assert parse_version("") is None

    @pytest.mark.unit
    def test_no_version(self):
        """String without version returns None."""
        assert parse_version("no version here") is None


class TestGetFileFromPath:
    """Tests for get_file_from_path() - filename extraction."""

    @pytest.mark.unit
    def test_absolute_path(self):
        """Extract filename from absolute path."""
        assert get_file_from_path("/home/user/documents/file.txt") == "file.txt"

    @pytest.mark.unit
    def test_relative_path(self):
        """Extract filename from relative path."""
        assert get_file_from_path("./config/settings.yml") == "settings.yml"

    @pytest.mark.unit
    def test_just_filename(self):
        """Return filename when no path."""
        assert get_file_from_path("dump.sql.gz") == "dump.sql.gz"

    @pytest.mark.unit
    def test_path_with_dots(self):
        """Handle paths with dots."""
        assert get_file_from_path("/var/www/html/app.config.php") == "app.config.php"

    @pytest.mark.unit
    def test_trailing_slash(self):
        """Handle path with trailing slash - returns last component."""
        assert get_file_from_path("/var/www/") == "www"


class TestRemoveSurroundingQuotes:
    """Tests for remove_surrounding_quotes() - quote removal."""

    @pytest.mark.unit
    def test_double_quotes(self):
        """Remove surrounding double quotes."""
        assert remove_surrounding_quotes('"hello"') == "hello"

    @pytest.mark.unit
    def test_single_quotes(self):
        """Remove surrounding single quotes."""
        assert remove_surrounding_quotes("'world'") == "world"

    @pytest.mark.unit
    def test_no_quotes(self):
        """No change when no surrounding quotes."""
        assert remove_surrounding_quotes("plain") == "plain"

    @pytest.mark.unit
    def test_mismatched_quotes(self):
        """No change when quotes don't match."""
        assert remove_surrounding_quotes("'mixed\"") == "'mixed\""

    @pytest.mark.unit
    def test_only_start_quote(self):
        """No change with only starting quote."""
        assert remove_surrounding_quotes('"start') == '"start'

    @pytest.mark.unit
    def test_only_end_quote(self):
        """No change with only ending quote."""
        assert remove_surrounding_quotes('end"') == 'end"'

    @pytest.mark.unit
    def test_empty_quoted(self):
        """Handle empty quoted string."""
        assert remove_surrounding_quotes('""') == ""
        assert remove_surrounding_quotes("''") == ""

    @pytest.mark.unit
    def test_integer(self):
        """Non-string types returned unchanged."""
        assert remove_surrounding_quotes(123) == 123

    @pytest.mark.unit
    def test_none(self):
        """None returned unchanged."""
        assert remove_surrounding_quotes(None) is None

    @pytest.mark.unit
    def test_nested_quotes(self):
        """Only outer quotes removed."""
        assert remove_surrounding_quotes("'\"inner\"'") == '"inner"'


class TestCleanDbConfig:
    """Tests for clean_db_config() - config cleanup."""

    @pytest.mark.unit
    def test_removes_quotes_from_values(self):
        """Remove quotes from all values."""
        config = {"user": '"admin"', "password": "'secret'", "host": "localhost"}
        result = clean_db_config(config)
        assert result == {"user": "admin", "password": "secret", "host": "localhost"}

    @pytest.mark.unit
    def test_empty_config(self):
        """Handle empty config."""
        assert clean_db_config({}) == {}

    @pytest.mark.unit
    def test_mixed_types(self):
        """Handle mixed value types."""
        config = {"port": 3306, "name": '"mydb"', "ssl": True}
        result = clean_db_config(config)
        assert result == {"port": 3306, "name": "mydb", "ssl": True}


class TestDictToArgs:
    """Tests for dict_to_args() - argument list generation."""

    @pytest.mark.unit
    def test_boolean_true(self):
        """True values become flags."""
        assert dict_to_args({"verbose": True}) == ["--verbose"]

    @pytest.mark.unit
    def test_boolean_false(self):
        """False values are omitted."""
        assert dict_to_args({"verbose": False}) is None

    @pytest.mark.unit
    def test_string_value(self):
        """String values become key-value pairs."""
        assert dict_to_args({"output": "file.txt"}) == ["--output", "file.txt"]

    @pytest.mark.unit
    def test_integer_value(self):
        """Integer values are converted to strings."""
        assert dict_to_args({"port": 3306}) == ["--port", "3306"]

    @pytest.mark.unit
    def test_none_value(self):
        """None values are omitted."""
        assert dict_to_args({"config": None}) is None

    @pytest.mark.unit
    def test_mixed_args(self):
        """Handle mixed argument types."""
        result = dict_to_args({
            "verbose": True,
            "quiet": False,
            "output": "dump.sql",
            "port": 3306,
            "config": None
        })
        assert "--verbose" in result
        assert "--quiet" not in result
        assert "--output" in result
        assert "dump.sql" in result
        assert "--port" in result
        assert "3306" in result

    @pytest.mark.unit
    def test_empty_dict(self):
        """Empty dict returns None."""
        assert dict_to_args({}) is None

    @pytest.mark.unit
    def test_all_false(self):
        """All False values returns None."""
        assert dict_to_args({"a": False, "b": False}) is None


class TestRemoveMultipleElementsFromString:
    """Tests for remove_multiple_elements_from_string() - string cleaning."""

    @pytest.mark.unit
    def test_remove_single_element(self):
        """Remove single element from string."""
        assert remove_multiple_elements_from_string(["a"], "abcabc") == "bcbc"

    @pytest.mark.unit
    def test_remove_multiple_elements(self):
        """Remove multiple elements from string."""
        assert remove_multiple_elements_from_string(["a", "b"], "abcabc") == "cc"

    @pytest.mark.unit
    def test_empty_list(self):
        """Empty list returns unchanged string."""
        assert remove_multiple_elements_from_string([], "hello") == "hello"

    @pytest.mark.unit
    def test_element_not_found(self):
        """Missing elements don't cause errors."""
        assert remove_multiple_elements_from_string(["x"], "hello") == "hello"

    @pytest.mark.unit
    def test_empty_string(self):
        """Handle empty string input."""
        assert remove_multiple_elements_from_string(["a"], "") == ""

    @pytest.mark.unit
    def test_remove_substrings(self):
        """Remove substring elements."""
        assert remove_multiple_elements_from_string(["foo", "bar"], "foobarfoo") == ""
