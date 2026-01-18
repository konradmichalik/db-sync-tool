#!/usr/bin/env python3

"""
Typer-based CLI for db_sync_tool.

This module provides a modern CLI using typer with type annotations,
automatic documentation, and rich help formatting.
"""

import argparse
import logging
import traceback
from enum import Enum
from typing import Annotated

import typer
from rich.console import Console

from db_sync_tool import sync
from db_sync_tool.utility.config_resolver import ConfigResolver
from db_sync_tool.utility.console import init_output_manager
from db_sync_tool.utility.exceptions import ConfigError, NoConfigFoundError
from db_sync_tool.utility.logging_config import init_logging


class OutputFormat(str, Enum):
    """Output format options."""

    interactive = "interactive"
    ci = "ci"
    json = "json"
    quiet = "quiet"


app = typer.Typer(
    name="db_sync_tool",
    help="A tool for automatic database synchronization from and to host systems.",
    add_completion=True,
    rich_markup_mode="rich",
)


@app.command()
def main(
    # === Positional Arguments ===
    origin: Annotated[
        str | None,
        typer.Argument(help="Origin database defined in host file"),
    ] = None,
    target: Annotated[
        str | None,
        typer.Argument(help="Target database defined in host file"),
    ] = None,
    # === Configuration Files ===
    config_file: Annotated[
        str | None,
        typer.Option(
            "--config-file",
            "-f",
            help="Path to configuration file",
            rich_help_panel="Configuration",
        ),
    ] = None,
    host_file: Annotated[
        str | None,
        typer.Option(
            "--host-file",
            "-o",
            help="Using an additional hosts file for merging hosts information",
            rich_help_panel="Configuration",
        ),
    ] = None,
    log_file: Annotated[
        str | None,
        typer.Option(
            "--log-file",
            "-l",
            help="File path for creating an additional log file",
            rich_help_panel="Configuration",
        ),
    ] = None,
    json_log: Annotated[
        bool,
        typer.Option(
            "--json-log",
            "-jl",
            help="Use JSON format for log file output (structured logging)",
            rich_help_panel="Configuration",
        ),
    ] = False,
    # === Output Options ===
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            count=True,
            help="Enable verbose output (-v) or debug output (-vv)",
            rich_help_panel="Output",
        ),
    ] = 0,
    mute: Annotated[
        bool,
        typer.Option(
            "--mute",
            "-m",
            help="Mute console output",
            rich_help_panel="Output",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress all output except errors (shorthand for --output=quiet)",
            rich_help_panel="Output",
        ),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option(
            "--output",
            help="Output format",
            rich_help_panel="Output",
        ),
    ] = OutputFormat.interactive,
    # === Execution Options ===
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip user confirmation for database import",
            rich_help_panel="Execution",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-dr",
            help="Testing process without running database export, transfer or import",
            rich_help_panel="Execution",
        ),
    ] = False,
    reverse: Annotated[
        bool,
        typer.Option(
            "--reverse",
            "-r",
            help="Reverse origin and target hosts",
            rich_help_panel="Execution",
        ),
    ] = False,
    force_password: Annotated[
        bool,
        typer.Option(
            "--force-password",
            "-fpw",
            help="Force password user query",
            rich_help_panel="Execution",
        ),
    ] = False,
    # === Database Dump Options ===
    import_file: Annotated[
        str | None,
        typer.Option(
            "--import-file",
            "-i",
            help="Import database from a specific file dump",
            rich_help_panel="Database Dump",
        ),
    ] = None,
    dump_name: Annotated[
        str | None,
        typer.Option(
            "--dump-name",
            "-dn",
            help='Set a specific dump file name (default is "_[dbname]_[date]")',
            rich_help_panel="Database Dump",
        ),
    ] = None,
    keep_dump: Annotated[
        str | None,
        typer.Option(
            "--keep-dump",
            "-kd",
            help="Skip target import and save dump file in the given directory",
            rich_help_panel="Database Dump",
        ),
    ] = None,
    clear_database: Annotated[
        bool,
        typer.Option(
            "--clear-database",
            "-cd",
            help="Drop all tables before importing to get a clean database",
            rich_help_panel="Database Dump",
        ),
    ] = False,
    tables: Annotated[
        str | None,
        typer.Option(
            "--tables",
            "-ta",
            help="Define specific tables to export, e.g. --tables=table1,table2",
            rich_help_panel="Database Dump",
        ),
    ] = None,
    where: Annotated[
        str | None,
        typer.Option(
            "--where",
            "-w",
            help="Additional where clause for mysql dump to sync only selected rows",
            rich_help_panel="Database Dump",
        ),
    ] = None,
    additional_mysqldump_options: Annotated[
        str | None,
        typer.Option(
            "--additional-mysqldump-options",
            "-amo",
            help="Additional mysqldump options",
            rich_help_panel="Database Dump",
        ),
    ] = None,
    # === Framework ===
    framework_type: Annotated[
        str | None,
        typer.Option(
            "--type",
            "-t",
            help="Define the framework type [TYPO3, Symfony, Drupal, Wordpress, Laravel]",
            rich_help_panel="Framework",
        ),
    ] = None,
    # === Transfer Options ===
    use_rsync: Annotated[
        bool,
        typer.Option(
            "--use-rsync",
            "-ur",
            help="Use rsync as transfer method",
            rich_help_panel="Transfer",
        ),
    ] = False,
    use_rsync_options: Annotated[
        str | None,
        typer.Option(
            "--use-rsync-options",
            "-uro",
            help="Additional rsync options",
            rich_help_panel="Transfer",
        ),
    ] = None,
    # === File Transfer Options ===
    with_files: Annotated[
        bool,
        typer.Option(
            "--with-files",
            "-wf",
            help="Enable file synchronization (requires 'files' section in config)",
            rich_help_panel="File Transfer",
        ),
    ] = False,
    files_only: Annotated[
        bool,
        typer.Option(
            "--files-only",
            "-fo",
            help="Sync only files, skip database synchronization",
            rich_help_panel="File Transfer",
        ),
    ] = False,
    # === Target Client Options ===
    target_path: Annotated[
        str | None,
        typer.Option(
            "--target-path",
            "-tp",
            help="File path to target database credential file",
            rich_help_panel="Target Client",
        ),
    ] = None,
    target_name: Annotated[
        str | None,
        typer.Option(
            "--target-name",
            "-tn",
            help="Providing a name for the target system",
            rich_help_panel="Target Client",
        ),
    ] = None,
    target_host: Annotated[
        str | None,
        typer.Option(
            "--target-host",
            "-th",
            help="SSH host to target system",
            rich_help_panel="Target Client",
        ),
    ] = None,
    target_user: Annotated[
        str | None,
        typer.Option(
            "--target-user",
            "-tu",
            help="SSH user for target system",
            rich_help_panel="Target Client",
        ),
    ] = None,
    target_password: Annotated[
        str | None,
        typer.Option(
            "--target-password",
            "-tpw",
            help="SSH password for target system",
            rich_help_panel="Target Client",
        ),
    ] = None,
    target_key: Annotated[
        str | None,
        typer.Option(
            "--target-key",
            "-tk",
            help="File path to SSH key for target system",
            rich_help_panel="Target Client",
        ),
    ] = None,
    target_port: Annotated[
        int | None,
        typer.Option(
            "--target-port",
            "-tpo",
            help="SSH port for target system",
            rich_help_panel="Target Client",
        ),
    ] = None,
    target_dump_dir: Annotated[
        str | None,
        typer.Option(
            "--target-dump-dir",
            "-tdd",
            help="Directory path for database dump file on target system",
            rich_help_panel="Target Client",
        ),
    ] = None,
    target_keep_dumps: Annotated[
        int | None,
        typer.Option(
            "--target-keep-dumps",
            "-tkd",
            help="Keep dump file count for target system",
            rich_help_panel="Target Client",
        ),
    ] = None,
    target_db_name: Annotated[
        str | None,
        typer.Option(
            "--target-db-name",
            "-tdn",
            help="Database name for target system",
            rich_help_panel="Target Client - Database",
        ),
    ] = None,
    target_db_host: Annotated[
        str | None,
        typer.Option(
            "--target-db-host",
            "-tdh",
            help="Database host for target system",
            rich_help_panel="Target Client - Database",
        ),
    ] = None,
    target_db_user: Annotated[
        str | None,
        typer.Option(
            "--target-db-user",
            "-tdu",
            help="Database user for target system",
            rich_help_panel="Target Client - Database",
        ),
    ] = None,
    target_db_password: Annotated[
        str | None,
        typer.Option(
            "--target-db-password",
            "-tdpw",
            help="Database password for target system",
            rich_help_panel="Target Client - Database",
        ),
    ] = None,
    target_db_port: Annotated[
        int | None,
        typer.Option(
            "--target-db-port",
            "-tdpo",
            help="Database port for target system",
            rich_help_panel="Target Client - Database",
        ),
    ] = None,
    target_after_dump: Annotated[
        str | None,
        typer.Option(
            "--target-after-dump",
            "-tad",
            help="Additional dump file to insert after regular database import",
            rich_help_panel="Target Client",
        ),
    ] = None,
    # === Origin Client Options ===
    origin_path: Annotated[
        str | None,
        typer.Option(
            "--origin-path",
            "-op",
            help="File path to origin database credential file",
            rich_help_panel="Origin Client",
        ),
    ] = None,
    origin_name: Annotated[
        str | None,
        typer.Option(
            "--origin-name",
            "-on",
            help="Providing a name for the origin system",
            rich_help_panel="Origin Client",
        ),
    ] = None,
    origin_host: Annotated[
        str | None,
        typer.Option(
            "--origin-host",
            "-oh",
            help="SSH host to origin system",
            rich_help_panel="Origin Client",
        ),
    ] = None,
    origin_user: Annotated[
        str | None,
        typer.Option(
            "--origin-user",
            "-ou",
            help="SSH user for origin system",
            rich_help_panel="Origin Client",
        ),
    ] = None,
    origin_password: Annotated[
        str | None,
        typer.Option(
            "--origin-password",
            "-opw",
            help="SSH password for origin system",
            rich_help_panel="Origin Client",
        ),
    ] = None,
    origin_key: Annotated[
        str | None,
        typer.Option(
            "--origin-key",
            "-ok",
            help="File path to SSH key for origin system",
            rich_help_panel="Origin Client",
        ),
    ] = None,
    origin_port: Annotated[
        int | None,
        typer.Option(
            "--origin-port",
            "-opo",
            help="SSH port for origin system",
            rich_help_panel="Origin Client",
        ),
    ] = None,
    origin_dump_dir: Annotated[
        str | None,
        typer.Option(
            "--origin-dump-dir",
            "-odd",
            help="Directory path for database dump file on origin system",
            rich_help_panel="Origin Client",
        ),
    ] = None,
    origin_keep_dumps: Annotated[
        int | None,
        typer.Option(
            "--origin-keep-dumps",
            "-okd",
            help="Keep dump file count for origin system",
            rich_help_panel="Origin Client",
        ),
    ] = None,
    origin_db_name: Annotated[
        str | None,
        typer.Option(
            "--origin-db-name",
            "-odn",
            help="Database name for origin system",
            rich_help_panel="Origin Client - Database",
        ),
    ] = None,
    origin_db_host: Annotated[
        str | None,
        typer.Option(
            "--origin-db-host",
            "-odh",
            help="Database host for origin system",
            rich_help_panel="Origin Client - Database",
        ),
    ] = None,
    origin_db_user: Annotated[
        str | None,
        typer.Option(
            "--origin-db-user",
            "-odu",
            help="Database user for origin system",
            rich_help_panel="Origin Client - Database",
        ),
    ] = None,
    origin_db_password: Annotated[
        str | None,
        typer.Option(
            "--origin-db-password",
            "-odpw",
            help="Database password for origin system",
            rich_help_panel="Origin Client - Database",
        ),
    ] = None,
    origin_db_port: Annotated[
        int | None,
        typer.Option(
            "--origin-db-port",
            "-odpo",
            help="Database port for origin system",
            rich_help_panel="Origin Client - Database",
        ),
    ] = None,
) -> None:
    """
    Synchronize a database from origin to target system.

    Examples:
        db_sync_tool -f config.yaml
        db_sync_tool production local -o hosts.yaml
        db_sync_tool -f config.yaml -v -y
    """
    # Initialize output manager first (needed for config resolver output)
    output_format = "quiet" if quiet else output.value
    init_output_manager(format=output_format, verbose=verbose, mute=mute or quiet)

    # Config resolution: use ConfigResolver if no explicit config file or host file
    resolved_config = None
    resolved_origin = origin
    resolved_target = target

    if config_file is None and import_file is None and host_file is None:
        # Use ConfigResolver for auto-discovery
        # Skip if host_file is provided (use original host linking mechanism)
        console = Console()
        resolver = ConfigResolver(console=console)

        # Check if we should use auto-discovery
        # Allow interactive mode only if running in a TTY and not in quiet/mute mode
        interactive = console.is_terminal and not (quiet or mute)

        try:
            resolved = resolver.resolve(
                config_file=None,
                origin=origin,
                target=target,
                interactive=interactive,
            )

            if resolved.config_file:
                config_file = str(resolved.config_file)

            # Store resolved configs for later merging
            if resolved.origin_config or resolved.target_config:
                resolved_config = resolved
                # Clear origin/target args since we're using resolved configs
                resolved_origin = None
                resolved_target = None

        except NoConfigFoundError:
            # No auto-discovery config found, fall through to original behavior
            # This is expected when no .db-sync-tool/ or ~/.db-sync-tool/ exists
            pass
        except ConfigError:
            # Config was found but has errors (invalid YAML, missing host, etc.)
            # Re-raise to let the user know about the problem
            raise
        except Exception as e:
            # Unexpected error during config resolution
            # Log with details in verbose mode, then re-raise
            logger = logging.getLogger('db_sync_tool')
            error_msg = f"Unexpected error during config resolution: {e}"
            if verbose >= 2:
                logger.error(f"{error_msg}\n{traceback.format_exc()}")
            elif verbose >= 1:
                logger.error(error_msg)
            raise

    # Build args namespace for compatibility with existing code
    args = _build_args_namespace(
        origin=resolved_origin,
        target=resolved_target,
        config_file=config_file,
        host_file=host_file,
        log_file=log_file,
        json_log=json_log,
        verbose=verbose,
        mute=mute,
        quiet=quiet,
        output=output,
        yes=yes,
        dry_run=dry_run,
        reverse=reverse,
        force_password=force_password,
        import_file=import_file,
        dump_name=dump_name,
        keep_dump=keep_dump,
        clear_database=clear_database,
        tables=tables,
        where=where,
        additional_mysqldump_options=additional_mysqldump_options,
        framework_type=framework_type,
        use_rsync=use_rsync,
        use_rsync_options=use_rsync_options,
        with_files=with_files,
        files_only=files_only,
        target_path=target_path,
        target_name=target_name,
        target_host=target_host,
        target_user=target_user,
        target_password=target_password,
        target_key=target_key,
        target_port=target_port,
        target_dump_dir=target_dump_dir,
        target_keep_dumps=target_keep_dumps,
        target_db_name=target_db_name,
        target_db_host=target_db_host,
        target_db_user=target_db_user,
        target_db_password=target_db_password,
        target_db_port=target_db_port,
        target_after_dump=target_after_dump,
        origin_path=origin_path,
        origin_name=origin_name,
        origin_host=origin_host,
        origin_user=origin_user,
        origin_password=origin_password,
        origin_key=origin_key,
        origin_port=origin_port,
        origin_dump_dir=origin_dump_dir,
        origin_keep_dumps=origin_keep_dumps,
        origin_db_name=origin_db_name,
        origin_db_host=origin_db_host,
        origin_db_user=origin_db_user,
        origin_db_password=origin_db_password,
        origin_db_port=origin_db_port,
        resolved_config=resolved_config,
    )

    # Store json_log in system.config for use by log.py and other modules
    # Import here to avoid circular imports at module level
    from db_sync_tool.utility import system as sys_module
    sys_module.config['json_log'] = json_log

    # Initialize structured logging
    init_logging(
        verbose=verbose,
        mute=mute or quiet,
        log_file=log_file,
        json_logging=json_log,
    )

    # Call sync with typed args
    sync.Sync(
        config_file=config_file,
        verbose=verbose,
        yes=yes,
        mute=mute or quiet,
        dry_run=dry_run,
        import_file=import_file,
        dump_name=dump_name,
        keep_dump=keep_dump,
        host_file=host_file,
        clear=clear_database,
        force_password=force_password,
        use_rsync=use_rsync,
        use_rsync_options=use_rsync_options,
        reverse=reverse,
        with_files=with_files,
        files_only=files_only,
        args=args,
    )


def _build_args_namespace(**kwargs: object) -> argparse.Namespace:
    """
    Build an argparse-compatible namespace from typer arguments.

    This enables backward compatibility with existing code that
    expects an argparse.Namespace object.
    """
    args = argparse.Namespace()

    # Map typer parameter names to argparse attribute names
    name_mapping = {
        "framework_type": "type",
    }

    for key, value in kwargs.items():
        # Map to argparse name if different
        attr_name = name_mapping.get(key, key)

        # Handle enum conversion
        if hasattr(value, "value"):
            setattr(args, attr_name, value.value)
        else:
            setattr(args, attr_name, value)

    return args


def run() -> None:
    """Entry point for typer CLI."""
    app()


if __name__ == "__main__":
    run()
