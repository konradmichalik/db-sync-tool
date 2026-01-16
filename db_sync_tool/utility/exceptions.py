"""Custom exception hierarchy for db-sync-tool.

This module provides a structured exception hierarchy to replace
mixed use of ValueError, RuntimeError, and sys.exit() calls.

Exception Hierarchy:
    DbSyncError (base)
    ├── ConfigError - Configuration and setup errors
    ├── ValidationError - Input validation errors
    ├── RemoteError - SSH/SFTP connection errors
    ├── DatabaseError - Database operation errors
    ├── ParsingError - Framework config parsing errors
    ├── CommandError - Shell command execution errors
    └── FileAccessError - File not found/access errors
"""


class DbSyncError(Exception):
    """Base exception for all db-sync-tool errors.

    All custom exceptions inherit from this class, allowing
    callers to catch all db-sync-tool errors with a single
    except clause if desired.
    """

    pass


class ConfigError(DbSyncError):
    """Configuration-related errors.

    Raised when:
    - Config file has unsupported format
    - Required config parameters are missing
    - Invalid framework type specified
    - Host configuration is invalid
    """

    pass


class ValidationError(DbSyncError):
    """Input validation errors.

    Raised when:
    - Table names contain invalid characters
    - Database credentials are incomplete
    - Required values are empty or null
    """

    pass


class RemoteError(DbSyncError):
    """SSH/SFTP connection and operation errors.

    Raised when:
    - SSH authentication fails
    - SSH key file not found
    - Remote command execution fails
    - Target host is protected
    """

    pass


class DatabaseError(DbSyncError):
    """Database operation errors.

    Raised when:
    - Database credentials not found
    - Dump file is corrupted
    - Database commands fail
    """

    pass


class ParsingError(DbSyncError):
    """Framework configuration parsing errors.

    Raised when:
    - TYPO3 LocalConfiguration.php cannot be parsed
    - Symfony DATABASE_URL format is invalid
    - Drupal drush output cannot be parsed
    - WordPress wp-config.php parsing fails
    - Laravel .env parsing fails
    """

    pass


class CommandError(DbSyncError):
    """Shell command execution errors.

    Raised when:
    - SSH command returns non-zero exit code
    - Local shell command fails
    - Script execution fails
    """

    pass


class FileAccessError(DbSyncError):
    """File access and path errors.

    Raised when:
    - Config file not found
    - Database config file not found
    - SSH key file not found
    - Hosts file not found

    Note: Named FileAccessError to avoid shadowing
    the built-in FileNotFoundError.
    """

    pass
