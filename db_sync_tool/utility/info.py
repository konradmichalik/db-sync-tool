#!/usr/bin/env python3

"""

"""
import requests
import semantic_version
import random
from db_sync_tool.utility import mode, system, output
from db_sync_tool import info


def print_header(mute, verbose=0):
    """
    Printing console header
    :param mute: Boolean
    :param verbose: int - 0=compact, 1+=full header
    :return:
    """
    if mute is False:
        _colors = get_random_colors()
        if verbose >= 1:
            # Full header for verbose mode using Rich Panel
            _print_rich_header(_colors)
        else:
            # Compact header for default mode
            print(
                output.CliFormat.BLACK + _colors[0] + '⥣ ' + _colors[1] + '⥥ ' + output.CliFormat.ENDC +
                output.CliFormat.BLACK + 'db-sync-tool v' + info.__version__ + output.CliFormat.ENDC)
        check_updates()


def _print_rich_header(_colors):
    """Print header using Rich if available, fallback to ASCII."""
    try:
        from rich.console import Console
        from rich.text import Text

        console = Console(force_terminal=True)

        # Build simple header line
        header = Text()
        header.append("⥣ ", style=_color_to_rich(_colors[0]))
        header.append("⥥ ", style=_color_to_rich(_colors[1]))
        header.append("db-sync-tool ", style="bold")
        header.append(f"v{info.__version__}", style="dim")

        console.print(header)
        console.print()  # Empty line after header
    except ImportError:
        # Fallback to simple ASCII header
        print(
            _colors[0] + '⥣ ' + _colors[1] + '⥥ ' + output.CliFormat.ENDC +
            output.CliFormat.BOLD + 'db-sync-tool ' + output.CliFormat.ENDC +
            output.CliFormat.BLACK + 'v' + info.__version__ + output.CliFormat.ENDC
        )
        print()


def _color_to_rich(cli_color):
    """Convert CliFormat color to Rich style."""
    color_map = {
        output.CliFormat.BEIGE: "cyan",
        output.CliFormat.PURPLE: "magenta",
        output.CliFormat.BLUE: "blue",
        output.CliFormat.YELLOW: "yellow",
        output.CliFormat.GREEN: "green",
        output.CliFormat.RED: "red",
    }
    return color_map.get(cli_color, "white")


def check_updates():
    """
    Check for updates of the db_sync_tool
    :return:
    """
    try:
        response = requests.get(f'{info.__pypi_package_url__}/json')
        latest_version = response.json()['info']['version']
        if semantic_version.Version(info.__version__) < semantic_version.Version(latest_version):
            output.message(
                output.Subject.WARNING,
                f'A new version {output.CliFormat.BOLD}v{latest_version}{output.CliFormat.ENDC} is '
                f'available for the db-sync-tool: {info.__pypi_package_url__}',
                True
            )
    finally:
        return


def print_footer():
    """
    Printing console footer
    :return:
    """
    cfg = system.get_typed_config()
    if cfg.dry_run:
        _message = 'Successfully executed dry run'
    elif not cfg.keep_dump and not cfg.is_same_client and not mode.is_import():
        _message = 'Successfully synchronized databases'
    elif mode.is_import():
        _message = 'Successfully imported database dump'
    else:
        _message = 'Successfully created database dump'

    output.message(
        output.Subject.INFO,
        _message,
        True,
        True
    )


def get_random_colors():
    """
    Generate a tuple of random console colors
    :return:
    """
    _colors = [output.CliFormat.BEIGE, output.CliFormat.PURPLE, output.CliFormat.BLUE, output.CliFormat.YELLOW, output.CliFormat.GREEN, output.CliFormat.RED]
    return random.sample(_colors, 2)

