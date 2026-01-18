"""Custom exception hierarchy for db-sync-tool."""


class DbSyncError(Exception):
    """Base exception for all db-sync-tool errors."""
    pass


class ConfigError(DbSyncError):
    """Configuration and file access errors."""
    pass


class NoConfigFoundError(ConfigError):
    """No configuration found during auto-discovery.

    This is raised when ConfigResolver cannot find any configuration
    (no project configs, no global hosts, no explicit file).
    This is distinct from ConfigError which indicates a problem with
    an existing config file (parse error, invalid format, etc.).
    """
    pass


class ParsingError(DbSyncError):
    """Framework configuration parsing errors."""
    pass


class ValidationError(DbSyncError):
    """Input validation errors."""
    pass
