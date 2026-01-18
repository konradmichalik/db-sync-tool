#!/usr/bin/env python3

"""
Configuration dataclasses for db-sync-tool.

Provides typed configuration objects that can be created from the legacy
config dict. This enables gradual migration to typed configuration while
maintaining backwards compatibility.

Usage:
    from db_sync_tool.utility import system
    from db_sync_tool.utility.config import SyncConfig

    # Convert legacy config to typed object
    cfg = SyncConfig.from_dict(system.config)

    # Access with type safety
    print(cfg.origin.db.host)
    print(cfg.verbose)
"""

from dataclasses import dataclass, field


def _get(data: dict, key: str, default):
    """Get value from dict, treating None as missing (returns default)."""
    value = data.get(key)
    return default if value is None else value


def _get_int(data: dict, key: str, default: int) -> int:
    """Get int value from dict, with safe conversion."""
    value = data.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_list(data: dict, key: str, fallback_key: str | None = None) -> list:
    """Get list value from dict, with optional fallback key."""
    value = data.get(key)
    if value is not None:
        return value
    if fallback_key:
        return data.get(fallback_key) or []
    return []


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    name: str = ''
    host: str = ''
    user: str = ''
    password: str = ''
    port: int = 0  # 0 means use default (3306 for MySQL)

    @classmethod
    def from_dict(cls, data: dict | None) -> 'DatabaseConfig':
        """Create DatabaseConfig from dict."""
        if not data:
            return cls()
        return cls(
            name=_get(data, 'name', ''),
            host=_get(data, 'host', ''),
            user=_get(data, 'user', ''),
            password=_get(data, 'password', ''),
            port=_get_int(data, 'port', 0),
        )


@dataclass
class JumpHostConfig:
    """SSH jump host configuration."""
    host: str = ''
    user: str = ''
    password: str | None = None
    ssh_key: str | None = None
    port: int = 22
    private: str | None = None
    name: str | None = None

    @classmethod
    def from_dict(cls, data: dict | None) -> 'JumpHostConfig | None':
        """Create JumpHostConfig from dict."""
        if not data:
            return None
        return cls(
            host=_get(data, 'host', ''),
            user=_get(data, 'user', ''),
            password=data.get('password'),  # None is valid
            ssh_key=data.get('ssh_key'),  # None is valid
            port=_get_int(data, 'port', 22),
            private=data.get('private'),  # None is valid
            name=data.get('name'),  # None is valid
        )


@dataclass
class FileTransferConfig:
    """Configuration for a single file transfer entry."""
    origin: str = ''
    target: str = ''
    exclude: list[str] = field(default_factory=list)
    options: str | None = None  # Per-transfer rsync options

    @classmethod
    def from_dict(cls, data: dict | None) -> 'FileTransferConfig':
        """Create FileTransferConfig from dict."""
        if not data:
            return cls()
        return cls(
            origin=_get(data, 'origin', ''),
            target=_get(data, 'target', ''),
            exclude=_get_list(data, 'exclude'),
            options=data.get('options'),  # None is valid
        )


@dataclass
class ClientConfig:
    """Configuration for origin or target client."""
    path: str = ''
    name: str = ''
    host: str = ''
    user: str = ''
    password: str | None = None
    ssh_key: str | None = None
    port: int = 22
    dump_dir: str = '/tmp/'
    keep_dumps: int | None = None
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    jump_host: JumpHostConfig | None = None
    after_dump: str | None = None
    post_sql: list[str] = field(default_factory=list)
    # Dynamic fields for framework-specific features
    console: dict[str, str] = field(default_factory=dict)
    scripts: dict[str, str] = field(default_factory=dict)
    protect: bool = False
    link: str = ''

    @classmethod
    def from_dict(cls, data: dict | None) -> 'ClientConfig':
        """Create ClientConfig from dict."""
        if not data:
            return cls()
        return cls(
            path=_get(data, 'path', ''),
            name=_get(data, 'name', ''),
            host=_get(data, 'host', ''),
            user=_get(data, 'user', ''),
            password=data.get('password'),  # None is valid
            ssh_key=data.get('ssh_key'),  # None is valid
            port=_get_int(data, 'port', 22),
            dump_dir=_get(data, 'dump_dir', '/tmp/'),
            keep_dumps=data.get('keep_dumps'),  # None is valid
            db=DatabaseConfig.from_dict(data.get('db')),
            jump_host=JumpHostConfig.from_dict(data.get('jump_host')),
            after_dump=data.get('after_dump'),  # None is valid
            post_sql=_get_list(data, 'post_sql'),
            console=data.get('console') or {},
            scripts=data.get('scripts') or {},
            protect=_get(data, 'protect', False),
            link=_get(data, 'link', ''),
        )

    @property
    def is_remote(self) -> bool:
        """Check if this client is remote (has host configured)."""
        return bool(self.host)


@dataclass
class SyncConfig:
    """Main configuration for database synchronization."""
    # General options
    verbose: bool = False
    mute: bool = False
    dry_run: bool = False
    yes: bool = False
    reverse: bool = False

    # Dump options
    keep_dump: bool = False
    dump_name: str = ''
    check_dump: bool = True
    clear_database: bool = False

    # Import options
    import_file: str = ''

    # Table options
    tables: str = ''
    where: str = ''
    additional_mysqldump_options: str = ''
    ignore_tables: list[str] = field(default_factory=list)
    truncate_tables: list[str] = field(default_factory=list)

    # Transfer options
    use_rsync: bool = True
    use_rsync_options: str | None = None
    use_sshpass: bool = False

    # File transfer options
    files: list[FileTransferConfig] = field(default_factory=list)
    files_options: str | None = None  # Global rsync options for file transfer
    with_files: bool = False  # Enable file sync (opt-in)
    files_only: bool = False  # Sync only files, skip database

    # SSH options
    ssh_agent: bool = False
    force_password: bool = False
    ssh_password_origin: str | None = None
    ssh_password_target: str | None = None

    # Host linking
    link_hosts: str = ''
    link_origin: str | None = None
    link_target: str | None = None

    # Internal state
    config_file_path: str | None = None
    is_same_client: bool = False
    default_origin_dump_dir: bool = True
    default_target_dump_dir: bool = True
    log_file: str | None = None
    json_log: bool = False  # Use JSON format for log file output

    # Framework type
    type: str | None = None

    # Global scripts
    scripts: dict[str, str] = field(default_factory=dict)

    # Client configurations
    origin: ClientConfig = field(default_factory=ClientConfig)
    target: ClientConfig = field(default_factory=ClientConfig)

    def get_client(self, client: str) -> ClientConfig:
        """Get origin or target config by client identifier."""
        if client == 'origin':
            return self.origin
        elif client == 'target':
            return self.target
        raise ValueError(f"Unknown client: {client}")

    @staticmethod
    def _parse_files_config(files_data) -> list['FileTransferConfig']:
        """
        Parse files configuration, supporting both new and legacy formats.

        New format (flat list):
            files:
              - origin: fileadmin/
                target: fileadmin/

        Legacy format (nested):
            files:
              config:
                - origin: fileadmin/
                  target: fileadmin/
        """
        if not files_data:
            return []
        if isinstance(files_data, dict) and 'config' in files_data:
            # Legacy format: files.config[]
            return [FileTransferConfig.from_dict(f) for f in files_data.get('config', [])]
        if isinstance(files_data, list):
            # New format: files[]
            return [FileTransferConfig.from_dict(f) for f in files_data]
        return []

    @staticmethod
    def _parse_files_options(files_data, files_options_direct) -> str | None:
        """
        Parse files_options, supporting both direct and legacy formats.

        Direct: files_options: '--verbose'
        Legacy: files: { option: ['--verbose', '--compress'] }
        """
        # Direct files_options takes precedence (explicit "" overrides legacy)
        if files_options_direct is not None:
            return files_options_direct
        # Check legacy format
        if isinstance(files_data, dict) and 'option' in files_data:
            options = files_data.get('option', [])
            if options:
                return ' '.join(options)
        return None

    @classmethod
    def from_dict(cls, data: dict) -> 'SyncConfig':
        """
        Create SyncConfig from legacy config dict.

        :param data: Legacy config dictionary
        :return: SyncConfig instance
        """
        # Extract SSH passwords from nested dict if present
        ssh_passwords = data.get('ssh_password', {})
        return cls(
            # General options
            verbose=_get(data, 'verbose', False),
            mute=_get(data, 'mute', False),
            dry_run=_get(data, 'dry_run', False),
            yes=_get(data, 'yes', False),
            reverse=_get(data, 'reverse', False),
            # Dump options
            keep_dump=_get(data, 'keep_dump', False),
            dump_name=_get(data, 'dump_name', ''),
            check_dump=_get(data, 'check_dump', True),
            clear_database=_get(data, 'clear_database', False),
            import_file=_get(data, 'import', ''),
            # Table options
            tables=_get(data, 'tables', ''),
            where=_get(data, 'where', ''),
            additional_mysqldump_options=_get(data, 'additional_mysqldump_options', ''),
            ignore_tables=_get_list(data, 'ignore_tables', 'ignore_table'),
            truncate_tables=_get_list(data, 'truncate_tables', 'truncate_table'),
            # Transfer options
            use_rsync=_get(data, 'use_rsync', True),
            use_rsync_options=data.get('use_rsync_options'),  # None is valid
            use_sshpass=_get(data, 'use_sshpass', False),
            # File transfer options
            files=cls._parse_files_config(data.get('files')),
            files_options=cls._parse_files_options(data.get('files'), data.get('files_options')),
            with_files=_get(data, 'with_files', False),
            files_only=_get(data, 'files_only', False),
            # SSH options
            ssh_agent=_get(data, 'ssh_agent', False),
            force_password=_get(data, 'force_password', False),
            ssh_password_origin=ssh_passwords.get('origin'),
            ssh_password_target=ssh_passwords.get('target'),
            # Host linking
            link_hosts=_get(data, 'link_hosts', ''),
            link_origin=data.get('link_origin'),  # None is valid
            link_target=data.get('link_target'),  # None is valid
            # Internal state
            config_file_path=data.get('config_file_path'),  # None is valid
            is_same_client=_get(data, 'is_same_client', False),
            default_origin_dump_dir=_get(data, 'default_origin_dump_dir', True),
            default_target_dump_dir=_get(data, 'default_target_dump_dir', True),
            log_file=data.get('log_file'),  # None is valid
            json_log=_get(data, 'json_log', False),
            # Framework type
            type=data.get('type'),  # None is valid
            # Global scripts
            scripts=data.get('scripts') or {},
            # Client configurations
            origin=ClientConfig.from_dict(data.get('origin')),
            target=ClientConfig.from_dict(data.get('target')),
        )


def get_config() -> SyncConfig:
    """
    Get current configuration as typed SyncConfig object.

    Convenience function that imports system.config and converts it.

    :return: SyncConfig instance
    """
    from db_sync_tool.utility import system
    return SyncConfig.from_dict(system.config)
