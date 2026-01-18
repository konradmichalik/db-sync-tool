#!/usr/bin/env python3

"""
Unit tests for the typer CLI implementation.

Tests CLI argument parsing, help output, and argument namespace building.
"""

import argparse

import pytest

# Skip all tests in this module if typer is not installed
typer = pytest.importorskip("typer", reason="typer not installed")
from typer.testing import CliRunner

from db_sync_tool.cli import OutputFormat, _build_args_namespace, app

runner = CliRunner()


class TestTyperHelpOutput:
    """Test that help output shows all argument groups correctly."""

    def test_help_shows_configuration_panel(self):
        """Test --help shows Configuration panel."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Configuration" in result.output

    def test_help_shows_output_panel(self):
        """Test --help shows Output panel."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Output" in result.output

    def test_help_shows_execution_panel(self):
        """Test --help shows Execution panel."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Execution" in result.output

    def test_help_shows_database_dump_panel(self):
        """Test --help shows Database Dump panel."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Database Dump" in result.output

    def test_help_shows_origin_client_panel(self):
        """Test --help shows Origin Client panel."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Origin Client" in result.output

    def test_help_shows_target_client_panel(self):
        """Test --help shows Target Client panel."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Target Client" in result.output


class TestShortOptions:
    """Test that all short options are recognized."""

    @pytest.mark.parametrize(
        "short_opt",
        [
            "-f",
            "-o",
            "-l",
            "-v",
            "-m",
            "-q",
            "-y",
            "-dr",
            "-r",
            "-i",
            "-dn",
            "-kd",
            "-cd",
            "-ta",
            "-w",
            "-amo",
            "-t",
            "-fpw",
            "-ur",
            "-uro",
            "-tp",
            "-tn",
            "-th",
            "-tu",
            "-tpw",
            "-tk",
            "-tpo",
            "-tdd",
            "-tkd",
            "-tdn",
            "-tdh",
            "-tdu",
            "-tdpw",
            "-tdpo",
            "-tad",
            "-op",
            "-on",
            "-oh",
            "-ou",
            "-opw",
            "-ok",
            "-opo",
            "-odd",
            "-okd",
            "-odn",
            "-odh",
            "-odu",
            "-odpw",
            "-odpo",
        ],
    )
    def test_short_option_recognized(self, short_opt):
        """Test that short option is recognized (appears in help)."""
        result = runner.invoke(app, ["--help"])
        assert short_opt in result.output, f"Short option {short_opt} not found in help"


class TestBuildArgsNamespace:
    """Test the _build_args_namespace helper function."""

    def test_basic_string_args(self):
        """Test basic string arguments are passed through."""
        ns = _build_args_namespace(
            config_file="config.yaml",
            origin="prod",
            target="local",
        )
        assert isinstance(ns, argparse.Namespace)
        assert ns.config_file == "config.yaml"
        assert ns.origin == "prod"
        assert ns.target == "local"

    def test_boolean_args(self):
        """Test boolean arguments are passed through."""
        ns = _build_args_namespace(
            verbose=0,
            mute=True,
            quiet=False,
            yes=True,
            dry_run=False,
        )
        assert ns.mute is True
        assert ns.quiet is False
        assert ns.yes is True
        assert ns.dry_run is False

    def test_integer_args(self):
        """Test integer arguments are passed through."""
        ns = _build_args_namespace(
            verbose=2,
            target_port=2222,
            origin_db_port=3307,
        )
        assert ns.verbose == 2
        assert ns.target_port == 2222
        assert ns.origin_db_port == 3307

    def test_enum_conversion(self):
        """Test enum values are converted to their string value."""
        ns = _build_args_namespace(
            output=OutputFormat.ci,
        )
        assert ns.output == "ci"

    def test_none_values(self):
        """Test None values are passed through."""
        ns = _build_args_namespace(
            config_file=None,
            import_file=None,
        )
        assert ns.config_file is None
        assert ns.import_file is None

    def test_framework_type_mapping(self):
        """Test framework_type is mapped to 'type' attribute."""
        ns = _build_args_namespace(
            framework_type="TYPO3",
        )
        assert ns.type == "TYPO3"

    def test_all_client_options(self):
        """Test all client options are passed through."""
        ns = _build_args_namespace(
            origin_host="origin.example.com",
            origin_user="deploy",
            origin_password="secret",
            origin_key="/path/to/key",
            origin_port=22,
            origin_path="/var/www",
            origin_name="Production",
            origin_dump_dir="/tmp",
            origin_keep_dumps=5,
            origin_db_name="prod_db",
            origin_db_host="localhost",
            origin_db_user="root",
            origin_db_password="dbpass",
            origin_db_port=3306,
            target_host="target.example.com",
            target_user="deploy",
            target_password="secret",
            target_key="/path/to/key",
            target_port=22,
            target_path="/var/www",
            target_name="Staging",
            target_dump_dir="/tmp",
            target_keep_dumps=3,
            target_db_name="staging_db",
            target_db_host="localhost",
            target_db_user="root",
            target_db_password="dbpass",
            target_db_port=3306,
            target_after_dump="/path/to/after.sql",
        )
        # Origin
        assert ns.origin_host == "origin.example.com"
        assert ns.origin_user == "deploy"
        assert ns.origin_port == 22
        assert ns.origin_db_name == "prod_db"
        # Target
        assert ns.target_host == "target.example.com"
        assert ns.target_name == "Staging"
        assert ns.target_after_dump == "/path/to/after.sql"


class TestOutputFormatEnum:
    """Test the OutputFormat enum."""

    def test_enum_values(self):
        """Test all enum values are defined."""
        assert OutputFormat.interactive.value == "interactive"
        assert OutputFormat.ci.value == "ci"
        assert OutputFormat.json.value == "json"
        assert OutputFormat.quiet.value == "quiet"

    def test_enum_is_string(self):
        """Test enum inherits from str for comparison."""
        assert OutputFormat.interactive == "interactive"
        assert OutputFormat.ci == "ci"
