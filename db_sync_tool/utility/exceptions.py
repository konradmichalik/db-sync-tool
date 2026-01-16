"""Custom exception hierarchy for db-sync-tool."""


class DbSyncError(Exception):
    """Base exception for all db-sync-tool errors."""
    pass


class ConfigError(DbSyncError):
    """Configuration and file access errors."""
    pass


class ParsingError(DbSyncError):
    """Framework configuration parsing errors."""
    pass


class ValidationError(DbSyncError):
    """Input validation errors."""
    pass
