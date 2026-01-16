"""Unit tests for framework recipe parsing functions.

Tests for db_sync_tool/recipes/parsing.py - pure parsing functions for
framework-specific database configuration files.

These tests verify that database credentials are correctly parsed from
various configuration file formats used by popular PHP frameworks:
- TYPO3 (LocalConfiguration.php with Connections or legacy format)
- Symfony (.env with DATABASE_URL)
- Drupal (Drush JSON output)

The parsing module has no dependencies on other project modules,
allowing proper import and code coverage measurement.
"""
import pytest

from db_sync_tool.recipes.parsing import (
    parse_symfony_database_url,
    parse_drupal_drush_credentials,
    parse_typo3_database_credentials,
)


class TestParseSymfonyDatabaseUrl:
    """Tests for parse_symfony_database_url() - DATABASE_URL parsing."""

    @pytest.mark.unit
    def test_parse_mysql_url(self):
        """Parse standard MySQL DATABASE_URL."""
        db_url = "DATABASE_URL=mysql://db_user:db_password@db_host:3306/db_name"
        result = parse_symfony_database_url(db_url)

        assert result['user'] == 'db_user'
        assert result['password'] == 'db_password'
        assert result['host'] == 'db_host'
        assert result['port'] == '3306'
        assert result['name'] == 'db_name'
        assert result['db_type'] == 'mysql'

    @pytest.mark.unit
    def test_parse_mariadb_url(self):
        """Parse MariaDB DATABASE_URL."""
        db_url = "DATABASE_URL=mariadb://admin:secret@localhost:3307/myapp"
        result = parse_symfony_database_url(db_url)

        assert result['db_type'] == 'mariadb'
        assert result['user'] == 'admin'
        assert result['password'] == 'secret'
        assert result['host'] == 'localhost'
        assert result['port'] == '3307'
        assert result['name'] == 'myapp'

    @pytest.mark.unit
    def test_parse_postgresql_url(self):
        """Parse PostgreSQL DATABASE_URL."""
        db_url = "DATABASE_URL=postgresql://pguser:pgpass@pghost:5432/pgdb"
        result = parse_symfony_database_url(db_url)

        assert result['db_type'] == 'postgresql'
        assert result['port'] == '5432'

    @pytest.mark.unit
    def test_parse_url_with_query_params(self):
        """Parse DATABASE_URL with query parameters (stripped)."""
        db_url = "DATABASE_URL=mysql://user:pass@host:3306/dbname?serverVersion=5.7&charset=utf8mb4"
        result = parse_symfony_database_url(db_url)

        assert result['name'] == 'dbname'
        assert result['user'] == 'user'
        # Query params are not included in result

    @pytest.mark.unit
    def test_parse_url_with_numeric_password(self):
        """Parse DATABASE_URL with numeric password."""
        db_url = "DATABASE_URL=mysql://user:12345678@host:3306/db"
        result = parse_symfony_database_url(db_url)

        assert result['password'] == '12345678'

    @pytest.mark.unit
    def test_parse_url_with_special_chars_in_password(self):
        """Parse DATABASE_URL with alphanumeric password."""
        db_url = "DATABASE_URL=mysql://user:p4ssw0rd@host:3306/db"
        result = parse_symfony_database_url(db_url)

        assert result['password'] == 'p4ssw0rd'

    @pytest.mark.unit
    def test_parse_url_with_at_sign_in_password(self):
        """Parse DATABASE_URL with @ in password (URL-encoded as %40)."""
        db_url = "DATABASE_URL=mysql://user:p%40ssword@host:3306/db"
        result = parse_symfony_database_url(db_url)

        assert result['password'] == 'p@ssword'

    @pytest.mark.unit
    def test_parse_url_with_multiple_special_chars_in_password(self):
        """Parse DATABASE_URL with multiple special chars (URL-encoded)."""
        # Password: P@ss:word/test -> URL-encoded: P%40ss%3Aword%2Ftest
        db_url = "DATABASE_URL=mysql://user:P%40ss%3Aword%2Ftest@host:3306/db"
        result = parse_symfony_database_url(db_url)

        assert result['password'] == 'P@ss:word/test'

    @pytest.mark.unit
    def test_parse_url_with_newline_escapes(self):
        """Handle DATABASE_URL with trailing newline escape."""
        db_url = "DATABASE_URL=mysql://user:pass@host:3306/db\\n'"
        result = parse_symfony_database_url(db_url)

        assert result['name'] == 'db'

    @pytest.mark.unit
    def test_parse_url_non_standard_port(self):
        """Parse DATABASE_URL with non-standard port."""
        db_url = "DATABASE_URL=mysql://user:pass@host:33060/db"
        result = parse_symfony_database_url(db_url)

        assert result['port'] == '33060'

    @pytest.mark.unit
    def test_parse_invalid_url_raises_error(self):
        """Invalid DATABASE_URL raises ValueError."""
        with pytest.raises(ValueError, match="Mismatch"):
            parse_symfony_database_url("INVALID_FORMAT")

    @pytest.mark.unit
    def test_parse_empty_url_raises_error(self):
        """Empty DATABASE_URL raises ValueError."""
        with pytest.raises(ValueError, match="Mismatch"):
            parse_symfony_database_url("")

    @pytest.mark.unit
    def test_parse_url_missing_port_raises_error(self):
        """DATABASE_URL without port raises ValueError."""
        with pytest.raises(ValueError, match="Mismatch"):
            parse_symfony_database_url("DATABASE_URL=mysql://user:pass@host/db")

    @pytest.mark.unit
    def test_parse_url_missing_password_raises_error(self):
        """DATABASE_URL without password raises ValueError."""
        with pytest.raises(ValueError, match="Mismatch"):
            parse_symfony_database_url("DATABASE_URL=mysql://user@host:3306/db")


class TestParseDrupalDrushCredentials:
    """Tests for parse_drupal_drush_credentials() - Drush output parsing."""

    @pytest.mark.unit
    def test_parse_drush_output(self):
        """Parse standard Drush core-status JSON output."""
        drush_output = {
            'db-name': 'drupal_db',
            'db-hostname': 'localhost',
            'db-password': 'secret123',
            'db-port': 3306,
            'db-username': 'drupal_user'
        }

        result = parse_drupal_drush_credentials(drush_output)

        assert result['name'] == 'drupal_db'
        assert result['host'] == 'localhost'
        assert result['password'] == 'secret123'
        assert result['port'] == 3306
        assert result['user'] == 'drupal_user'

    @pytest.mark.unit
    def test_parse_drush_output_string_port(self):
        """Parse Drush output with string port value."""
        drush_output = {
            'db-name': 'mydb',
            'db-hostname': '127.0.0.1',
            'db-password': 'pass',
            'db-port': '3307',
            'db-username': 'user'
        }

        result = parse_drupal_drush_credentials(drush_output)

        assert result['port'] == '3307'

    @pytest.mark.unit
    def test_parse_drush_output_empty_password(self):
        """Parse Drush output with empty password."""
        drush_output = {
            'db-name': 'drupal',
            'db-hostname': 'db',
            'db-password': '',
            'db-port': 3306,
            'db-username': 'root'
        }

        result = parse_drupal_drush_credentials(drush_output)

        assert result['password'] == ''

    @pytest.mark.unit
    def test_parse_drush_output_ipv6_host(self):
        """Parse Drush output with IPv6 host."""
        drush_output = {
            'db-name': 'drupal',
            'db-hostname': '::1',
            'db-password': 'pass',
            'db-port': 3306,
            'db-username': 'user'
        }

        result = parse_drupal_drush_credentials(drush_output)

        assert result['host'] == '::1'

    @pytest.mark.unit
    def test_parse_drush_missing_key_raises_error(self):
        """Missing key in Drush output raises KeyError."""
        incomplete_output = {
            'db-name': 'mydb',
            # Missing other keys
        }

        with pytest.raises(KeyError):
            parse_drupal_drush_credentials(incomplete_output)


class TestParseTYPO3DatabaseCredentials:
    """Tests for parse_typo3_database_credentials() - LocalConfiguration parsing."""

    @pytest.mark.unit
    def test_parse_typo3_v8_config(self):
        """Parse TYPO3 v8+ LocalConfiguration format (Connections/Default)."""
        db_config = {
            'Connections': {
                'Default': {
                    'dbname': 'typo3_db',
                    'host': 'localhost',
                    'password': 'typo3pass',
                    'port': 3306,
                    'user': 'typo3user'
                }
            }
        }

        result = parse_typo3_database_credentials(db_config)

        assert result['name'] == 'typo3_db'
        assert result['host'] == 'localhost'
        assert result['password'] == 'typo3pass'
        assert result['port'] == 3306
        assert result['user'] == 'typo3user'

    @pytest.mark.unit
    def test_parse_typo3_v7_config(self):
        """Parse TYPO3 v7- LocalConfiguration format (legacy)."""
        db_config = {
            'database': 'old_typo3',
            'host': 'db.server.com',
            'password': 'oldpass',
            'username': 'olduser'
        }

        result = parse_typo3_database_credentials(db_config)

        assert result['name'] == 'old_typo3'
        assert result['user'] == 'olduser'
        assert result['host'] == 'db.server.com'
        assert result['port'] == 3306  # default added

    @pytest.mark.unit
    def test_parse_typo3_v8_with_explicit_port(self):
        """Parse TYPO3 v8 config with explicit port."""
        db_config = {
            'Connections': {
                'Default': {
                    'dbname': 'mydb',
                    'host': 'remote.db',
                    'password': 'pass',
                    'port': 3307,
                    'user': 'user'
                }
            }
        }

        result = parse_typo3_database_credentials(db_config)

        assert result['port'] == 3307

    @pytest.mark.unit
    def test_parse_typo3_v8_without_port_adds_default(self):
        """Parse TYPO3 v8 config without port adds default 3306."""
        db_config = {
            'Connections': {
                'Default': {
                    'dbname': 'mydb',
                    'host': 'localhost',
                    'password': 'pass',
                    'user': 'user'
                    # No port
                }
            }
        }

        result = parse_typo3_database_credentials(db_config)

        assert result['port'] == 3306

    @pytest.mark.unit
    def test_parse_typo3_v7_without_port_adds_default(self):
        """Parse TYPO3 v7 config without port adds default 3306."""
        db_config = {
            'database': 'old_db',
            'host': 'localhost',
            'password': 'pass',
            'username': 'user'
            # No port
        }

        result = parse_typo3_database_credentials(db_config)

        assert result['port'] == 3306

    @pytest.mark.unit
    def test_parse_typo3_v8_preserves_extra_fields(self):
        """Parse TYPO3 v8 config preserves extra fields from Default."""
        db_config = {
            'Connections': {
                'Default': {
                    'dbname': 'mydb',
                    'host': 'localhost',
                    'password': 'pass',
                    'port': 3306,
                    'user': 'user',
                    'charset': 'utf8mb4',
                    'driver': 'mysqli'
                }
            }
        }

        result = parse_typo3_database_credentials(db_config)

        assert result.get('charset') == 'utf8mb4'
        assert result.get('driver') == 'mysqli'

    @pytest.mark.unit
    def test_parse_typo3_v7_with_port(self):
        """Parse TYPO3 v7 config with explicit port."""
        db_config = {
            'database': 'old_db',
            'host': 'localhost',
            'password': 'pass',
            'username': 'user',
            'port': 3308
        }

        result = parse_typo3_database_credentials(db_config)

        assert result['port'] == 3308

    @pytest.mark.unit
    def test_parse_typo3_v8_socket_connection(self):
        """Parse TYPO3 v8 config with socket connection."""
        db_config = {
            'Connections': {
                'Default': {
                    'dbname': 'mydb',
                    'host': 'localhost',
                    'password': 'pass',
                    'port': 3306,
                    'user': 'user',
                    'unix_socket': '/var/run/mysqld/mysqld.sock'
                }
            }
        }

        result = parse_typo3_database_credentials(db_config)

        assert result.get('unix_socket') == '/var/run/mysqld/mysqld.sock'


class TestEdgeCases:
    """Tests for edge cases across all parsing functions."""

    @pytest.mark.unit
    def test_symfony_url_with_underscore_in_dbname(self):
        """Symfony URL with underscore in database name."""
        db_url = "DATABASE_URL=mysql://user:pass@host:3306/my_database_name"
        result = parse_symfony_database_url(db_url)

        assert result['name'] == 'my_database_name'

    @pytest.mark.unit
    def test_symfony_url_with_hyphen_in_host(self):
        """Symfony URL with hyphen in hostname."""
        db_url = "DATABASE_URL=mysql://user:pass@db-server-01:3306/db"
        result = parse_symfony_database_url(db_url)

        assert result['host'] == 'db-server-01'

    @pytest.mark.unit
    def test_drupal_special_chars_in_values(self):
        """Drupal credentials with special characters."""
        drush_output = {
            'db-name': 'drupal-site_2024',
            'db-hostname': 'db.example.com',
            'db-password': 'P@ssw0rd!',
            'db-port': 3306,
            'db-username': 'admin_user'
        }

        result = parse_drupal_drush_credentials(drush_output)

        assert result['name'] == 'drupal-site_2024'
        assert result['password'] == 'P@ssw0rd!'

    @pytest.mark.unit
    def test_typo3_unicode_in_password(self):
        """TYPO3 config with unicode in password."""
        db_config = {
            'Connections': {
                'Default': {
                    'dbname': 'mydb',
                    'host': 'localhost',
                    'password': 'pässwörd',
                    'port': 3306,
                    'user': 'user'
                }
            }
        }

        result = parse_typo3_database_credentials(db_config)

        assert result['password'] == 'pässwörd'

    @pytest.mark.unit
    def test_symfony_long_credentials(self):
        """Symfony URL with long username and password."""
        long_user = 'user' * 10
        long_pass = 'pass' * 20
        db_url = f"DATABASE_URL=mysql://{long_user}:{long_pass}@host:3306/db"
        result = parse_symfony_database_url(db_url)

        assert result['user'] == long_user
        assert result['password'] == long_pass
