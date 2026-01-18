#!/usr/bin/env python3

"""
Main entry point for db_sync_tool CLI.

Uses typer for modern CLI with grouped help output and shell completion.
"""

from db_sync_tool.cli import run


def main() -> None:
    """Main entry point for the command line."""
    run()


if __name__ == "__main__":
    main()
