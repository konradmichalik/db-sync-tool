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


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    name: str = ''
    host: str = 'localhost'
    user: str = ''
    password: str = ''
    port: int = 3306

    @classmethod
    def from_dict(cls, data: dict | None) -> 'DatabaseConfig':
        """Create DatabaseConfig from dict."""
        if not data:
            return cls()
        return cls(
            name=data.get('name', ''),
            host=data.get('host', 'localhost'),
            user=data.get('user', ''),
            password=data.get('password', ''),
            port=int(data.get('port', 3306)),
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
            host=data.get('host', ''),
            user=data.get('user', ''),
            password=data.get('password'),
            ssh_key=data.get('ssh_key'),
            port=int(data.get('port', 22)),
            private=data.get('private'),
            name=data.get('name'),
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

    @classmethod
    def from_dict(cls, data: dict | None) -> 'ClientConfig':
        """Create ClientConfig from dict."""
        if not data:
            return cls()
        return cls(
            path=data.get('path', ''),
            name=data.get('name', ''),
            host=data.get('host', ''),
            user=data.get('user', ''),
            password=data.get('password'),
            ssh_key=data.get('ssh_key'),
            port=int(data.get('port', 22)),
            dump_dir=data.get('dump_dir', '/tmp/'),
            keep_dumps=data.get('keep_dumps'),
            db=DatabaseConfig.from_dict(data.get('db')),
            jump_host=JumpHostConfig.from_dict(data.get('jump_host')),
            after_dump=data.get('after_dump'),
            post_sql=data.get('post_sql', []),
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

    # SSH options
    ssh_agent: bool = False
    force_password: bool = False

    # Host linking
    link_hosts: str = ''
    link_origin: str | None = None
    link_target: str | None = None

    # Internal state
    config_file_path: str | None = None
    is_same_client: bool = False
    default_origin_dump_dir: bool = True
    default_target_dump_dir: bool = True

    # Framework type
    type: str | None = None

    # Client configurations
    origin: ClientConfig = field(default_factory=ClientConfig)
    target: ClientConfig = field(default_factory=ClientConfig)

    @classmethod
    def from_dict(cls, data: dict) -> 'SyncConfig':
        """
        Create SyncConfig from legacy config dict.

        :param data: Legacy config dictionary
        :return: SyncConfig instance
        """
        return cls(
            verbose=data.get('verbose', False),
            mute=data.get('mute', False),
            dry_run=data.get('dry_run', False),
            yes=data.get('yes', False),
            keep_dump=data.get('keep_dump', False),
            dump_name=data.get('dump_name', ''),
            check_dump=data.get('check_dump', True),
            clear_database=data.get('clear_database', False),
            import_file=data.get('import', ''),
            tables=data.get('tables', ''),
            where=data.get('where', ''),
            additional_mysqldump_options=data.get('additional_mysqldump_options', ''),
            ignore_tables=data.get('ignore_tables', data.get('ignore_table', [])),
            truncate_tables=data.get('truncate_tables', data.get('truncate_table', [])),
            use_rsync=data.get('use_rsync', True),
            use_rsync_options=data.get('use_rsync_options'),
            use_sshpass=data.get('use_sshpass', False),
            ssh_agent=data.get('ssh_agent', False),
            force_password=data.get('force_password', False),
            link_hosts=data.get('link_hosts', ''),
            link_origin=data.get('link_origin'),
            link_target=data.get('link_target'),
            config_file_path=data.get('config_file_path'),
            is_same_client=data.get('is_same_client', False),
            default_origin_dump_dir=data.get('default_origin_dump_dir', True),
            default_target_dump_dir=data.get('default_target_dump_dir', True),
            type=data.get('type'),
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
