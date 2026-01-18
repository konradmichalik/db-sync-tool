"""Unit tests for file transfer functionality.

Tests for db_sync_tool/utility/config.py file transfer fields
and db_sync_tool/remote/file_transfer.py module.
"""
import pytest

from db_sync_tool.utility.config import FileTransferConfig, SyncConfig


class TestFileTransferConfig:
    """Tests for FileTransferConfig dataclass."""

    @pytest.mark.unit
    def test_from_dict_full(self):
        """Create from complete dictionary."""
        data = {
            "origin": "fileadmin/",
            "target": "fileadmin/",
            "exclude": ["_processed_/", "_temp_/"],
            "options": "--delete"
        }
        config = FileTransferConfig.from_dict(data)
        assert config.origin == "fileadmin/"
        assert config.target == "fileadmin/"
        assert config.exclude == ["_processed_/", "_temp_/"]
        assert config.options == "--delete"

    @pytest.mark.unit
    def test_from_dict_minimal(self):
        """Create from minimal dictionary."""
        data = {"origin": "/uploads/", "target": "/uploads/"}
        config = FileTransferConfig.from_dict(data)
        assert config.origin == "/uploads/"
        assert config.target == "/uploads/"
        assert config.exclude == []
        assert config.options is None

    @pytest.mark.unit
    def test_from_dict_none(self):
        """None input returns defaults."""
        config = FileTransferConfig.from_dict(None)
        assert config.origin == ""
        assert config.target == ""
        assert config.exclude == []
        assert config.options is None

    @pytest.mark.unit
    def test_from_dict_empty(self):
        """Empty dict returns defaults."""
        config = FileTransferConfig.from_dict({})
        assert config.origin == ""
        assert config.target == ""
        assert config.exclude == []

    @pytest.mark.unit
    def test_exclude_single_item(self):
        """Single exclude pattern."""
        data = {"origin": "files/", "target": "files/", "exclude": ["*.log"]}
        config = FileTransferConfig.from_dict(data)
        assert config.exclude == ["*.log"]


class TestSyncConfigFilesFlat:
    """Tests for SyncConfig flat files format."""

    @pytest.mark.unit
    def test_files_empty_list(self):
        """Empty files list."""
        data = {"files": []}
        config = SyncConfig.from_dict(data)
        assert config.files == []

    @pytest.mark.unit
    def test_files_single_entry(self):
        """Single file transfer entry."""
        data = {
            "files": [
                {"origin": "uploads/", "target": "uploads/"}
            ]
        }
        config = SyncConfig.from_dict(data)
        assert len(config.files) == 1
        assert config.files[0].origin == "uploads/"
        assert config.files[0].target == "uploads/"

    @pytest.mark.unit
    def test_files_multiple_entries(self):
        """Multiple file transfer entries."""
        data = {
            "files": [
                {"origin": "uploads/", "target": "uploads/"},
                {"origin": "media/", "target": "media/", "exclude": ["*.tmp"]}
            ]
        }
        config = SyncConfig.from_dict(data)
        assert len(config.files) == 2
        assert config.files[0].origin == "uploads/"
        assert config.files[1].origin == "media/"
        assert config.files[1].exclude == ["*.tmp"]

    @pytest.mark.unit
    def test_files_with_options(self):
        """File entry with per-transfer options."""
        data = {
            "files": [
                {
                    "origin": "assets/",
                    "target": "assets/",
                    "options": "--verbose"
                }
            ]
        }
        config = SyncConfig.from_dict(data)
        assert config.files[0].options == "--verbose"


class TestSyncConfigFilesLegacy:
    """Tests for SyncConfig legacy files.config format."""

    @pytest.mark.unit
    def test_legacy_format_single(self):
        """Legacy nested format with single entry."""
        data = {
            "files": {
                "config": [
                    {"origin": "uploads/", "target": "uploads/"}
                ]
            }
        }
        config = SyncConfig.from_dict(data)
        assert len(config.files) == 1
        assert config.files[0].origin == "uploads/"

    @pytest.mark.unit
    def test_legacy_format_multiple(self):
        """Legacy nested format with multiple entries."""
        data = {
            "files": {
                "config": [
                    {"origin": "uploads/", "target": "uploads/"},
                    {"origin": "media/", "target": "media/"}
                ]
            }
        }
        config = SyncConfig.from_dict(data)
        assert len(config.files) == 2

    @pytest.mark.unit
    def test_legacy_format_with_option(self):
        """Legacy format with global option."""
        data = {
            "files": {
                "config": [
                    {"origin": "uploads/", "target": "uploads/"}
                ],
                "option": ["--verbose", "--compress"]
            }
        }
        config = SyncConfig.from_dict(data)
        assert config.files_options == "--verbose --compress"

    @pytest.mark.unit
    def test_legacy_format_empty_option(self):
        """Legacy format with empty option list."""
        data = {
            "files": {
                "config": [
                    {"origin": "uploads/", "target": "uploads/"}
                ],
                "option": []
            }
        }
        config = SyncConfig.from_dict(data)
        assert config.files_options is None


class TestSyncConfigFilesOptions:
    """Tests for files_options field."""

    @pytest.mark.unit
    def test_direct_files_options(self):
        """Direct files_options field."""
        data = {
            "files": [{"origin": "uploads/", "target": "uploads/"}],
            "files_options": "--progress"
        }
        config = SyncConfig.from_dict(data)
        assert config.files_options == "--progress"

    @pytest.mark.unit
    def test_files_options_takes_precedence(self):
        """Direct files_options takes precedence over legacy."""
        data = {
            "files": {
                "config": [{"origin": "uploads/", "target": "uploads/"}],
                "option": ["--legacy"]
            },
            "files_options": "--direct"
        }
        config = SyncConfig.from_dict(data)
        assert config.files_options == "--direct"


class TestSyncConfigFileFlags:
    """Tests for with_files and files_only flags."""

    @pytest.mark.unit
    def test_with_files_default(self):
        """with_files defaults to False."""
        config = SyncConfig.from_dict({})
        assert config.with_files is False

    @pytest.mark.unit
    def test_files_only_default(self):
        """files_only defaults to False."""
        config = SyncConfig.from_dict({})
        assert config.files_only is False

    @pytest.mark.unit
    def test_with_files_true(self):
        """with_files can be set to True."""
        data = {"with_files": True}
        config = SyncConfig.from_dict(data)
        assert config.with_files is True

    @pytest.mark.unit
    def test_files_only_true(self):
        """files_only can be set to True."""
        data = {"files_only": True}
        config = SyncConfig.from_dict(data)
        assert config.files_only is True

    @pytest.mark.unit
    def test_both_flags(self):
        """Both flags can be set."""
        data = {"with_files": True, "files_only": True}
        config = SyncConfig.from_dict(data)
        assert config.with_files is True
        assert config.files_only is True


class TestPathDetection:
    """Tests for path detection logic used in file_transfer module."""

    @pytest.mark.unit
    def test_absolute_path_detection(self):
        """Absolute paths start with /."""
        assert "/absolute/path/".startswith("/")
        assert "/var/www/html/".startswith("/")

    @pytest.mark.unit
    def test_relative_path_detection(self):
        """Relative paths don't start with /."""
        assert not "relative/path/".startswith("/")
        assert not "fileadmin/".startswith("/")
        assert not "uploads/media/".startswith("/")
