#!/usr/bin/env python3

"""
Modern CLI output using Rich.

This module provides a unified output interface supporting:
- Interactive mode: Compact progress display with status updates
- CI mode: GitHub Actions / GitLab CI annotations
- JSON mode: Machine-readable structured output
- Verbose mode: Detailed multi-line output

Usage:
    from db_sync_tool.utility.console import get_output_manager

    output_manager = get_output_manager()
    output_manager.step("Creating database dump")
    output_manager.success("Dump complete", tables=66, size=2516582, duration=3.2)
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from collections.abc import Callable
from typing import Any


class OutputFormat(Enum):
    """Output format modes."""
    INTERACTIVE = "interactive"
    CI = "ci"
    JSON = "json"
    QUIET = "quiet"


class CIProvider(Enum):
    """CI/CD provider detection."""
    GITHUB = "github"
    GITLAB = "gitlab"
    JENKINS = "jenkins"
    GENERIC = "generic"
    NONE = "none"


# CI provider detection mapping: env_var -> provider
_CI_ENV_MAP = {
    "GITHUB_ACTIONS": CIProvider.GITHUB,
    "GITLAB_CI": CIProvider.GITLAB,
    "JENKINS_URL": CIProvider.JENKINS,
    "CI": CIProvider.GENERIC,
}


@dataclass
class StepInfo:
    """Information about a sync step."""
    name: str
    subject: str = ""
    remote: bool = False
    start_time: float = field(default_factory=time.time)


class OutputManager:
    """
    Unified output manager for CLI operations.

    Handles different output formats and provides a consistent API
    for displaying progress, status, and results.
    """

    # Subject styles for Rich
    _SUBJECT_STYLES = {
        "origin": "origin",
        "target": "target",
        "local": "local",
        "info": "info",
        "warning": "warning",
        "error": "error",
    }

    def __init__(
        self,
        format: OutputFormat = OutputFormat.INTERACTIVE,
        verbose: bool = False,
        mute: bool = False,
    ):
        self.format = format
        self.verbose = verbose
        self.mute = mute
        self.ci_provider = self._detect_ci_provider()
        self._current_step: StepInfo | None = None
        self._steps_completed = 0
        self._start_time = time.time()
        self._console: Any = None
        self._escape: Callable[[str], str] | None = None

        if self.format == OutputFormat.INTERACTIVE:
            self._init_rich()

    def _init_rich(self) -> None:
        """Initialize Rich console."""
        try:
            from rich.console import Console
            from rich.markup import escape
            from rich.theme import Theme

            theme = Theme({
                "info": "cyan", "success": "green", "warning": "yellow",
                "error": "red bold", "origin": "magenta", "target": "blue",
                "local": "cyan", "debug": "dim",
            })
            self._console = Console(theme=theme, force_terminal=True)
            self._escape = escape
        except ImportError:
            self.format = OutputFormat.CI

    @staticmethod
    def _detect_ci_provider() -> CIProvider:
        """Detect CI environment from environment variables."""
        for env_var, provider in _CI_ENV_MAP.items():
            if os.environ.get(env_var):
                return provider
        return CIProvider.NONE

    def _format_prefix(self, subject: str, remote: bool = False) -> str:
        """Format subject prefix with optional remote indicator."""
        subj = subject.upper()
        if subj in ("ORIGIN", "TARGET"):
            return f"[{subj}][{'REMOTE' if remote else 'LOCAL'}]"
        return f"[{subj}]"

    def _get_style(self, subject: str) -> str:
        """Get Rich style for subject."""
        return self._SUBJECT_STYLES.get(subject.lower(), "info")

    def _print_rich(self, text: str, **kwargs: Any) -> None:
        """Print with Rich console or fallback to plain print."""
        if self._console:
            self._console.print(text, **kwargs)
        else:
            # Strip Rich markup for fallback
            import re
            plain = re.sub(r'\[/?[^\]]+\]', '', text)
            print(plain, **kwargs)

    def _route_output(
        self,
        event: str,
        message: str,
        json_data: dict[str, Any] | None = None,
        ci_handler: Callable[[], None] | None = None,
        interactive_handler: Callable[[], None] | None = None,
    ) -> bool:
        """Route output to appropriate handler based on format. Returns True if handled."""
        if self.format == OutputFormat.QUIET:
            return True
        if self.format == OutputFormat.JSON:
            self._json_output(event, message=message, **(json_data or {}))
            return True
        if self.format == OutputFormat.CI and ci_handler:
            ci_handler()
            return True
        if interactive_handler:
            interactive_handler()
            return True
        return False

    # --- Public API ---

    def step(self, message: str, subject: str = "INFO", remote: bool = False, debug: bool = False) -> None:
        """Display a step message."""
        if self.mute or (debug and not self.verbose):
            return

        self._current_step = StepInfo(name=message, subject=subject, remote=remote)
        prefix = self._format_prefix(subject, remote)
        style = self._get_style(subject)
        debug_tag = "[dim][DEBUG][/dim]" if debug else ""

        def ci() -> None:
            print(f"[INFO] {prefix} {message}")

        def interactive() -> None:
            esc = self._escape or (lambda x: x)
            if self.verbose:
                self._print_rich(f"[{style}]{esc(prefix)}[/{style}]{debug_tag} {esc(message)}")
            else:
                self._print_rich(f"⠋ [{style}]{esc(prefix)}[/{style}]{debug_tag} {esc(message)}", end="\r")

        self._route_output("step", message, {"subject": subject, "remote": remote}, ci, interactive)

    def success(self, message: str | None = None, **stats: Any) -> None:
        """Mark current step as successful."""
        if self.mute and not stats:
            return

        self._steps_completed += 1
        step = self._current_step
        display_msg = message or (step.name if step else "Operation")

        def ci() -> None:
            if message:
                print(f"[INFO] {message}")

        def interactive() -> None:
            subject = step.subject if step else "INFO"
            prefix = self._format_prefix(subject, step.remote if step else False)
            style = self._get_style(subject)
            esc = self._escape or (lambda x: x)

            self._print_rich(f"✓ [{style}]{esc(prefix)}[/{style}] {esc(display_msg)}", highlight=False)
            if stats and self.verbose:
                stats_str = " • ".join(f"{k}: {v}" for k, v in stats.items())
                self._print_rich(f"  [dim]{stats_str}[/dim]")

        self._route_output("success", display_msg, stats, ci, interactive)

    def error(self, message: str, exception: Exception | None = None) -> None:
        """Display an error message."""
        def ci() -> None:
            if self.ci_provider == CIProvider.GITHUB:
                print(f"::error::{message}")
            elif self.ci_provider == CIProvider.GITLAB:
                print(f"\033[0;31mERROR: {message}\033[0m")
            else:
                print(f"[ERROR] {message}", file=sys.stderr)

        def interactive() -> None:
            esc = self._escape or (lambda x: x)
            self._print_rich(f"[error]✗ [ERROR] {esc(message)}[/error]")
            if exception and self.verbose:
                self._print_rich(f"  [dim]{esc(str(exception))}[/dim]")

        exc_str = str(exception) if exception else None
        self._route_output("error", message, {"exception": exc_str}, ci, interactive)

    def warning(self, message: str) -> None:
        """Display a warning message."""
        if self.mute:
            return

        def ci() -> None:
            if self.ci_provider == CIProvider.GITHUB:
                print(f"::warning::{message}")
            elif self.ci_provider == CIProvider.GITLAB:
                print(f"\033[0;33mWARNING: {message}\033[0m")
            else:
                print(f"[WARNING] {message}")

        def interactive() -> None:
            esc = self._escape or (lambda x: x)
            self._print_rich(f"[warning]⚠ [WARNING] {esc(message)}[/warning]")

        self._route_output("warning", message, None, ci, interactive)

    def info(self, message: str) -> None:
        """Display an info message."""
        if self.mute:
            return

        def ci() -> None:
            print(f"[INFO] {message}")

        def interactive() -> None:
            esc = self._escape or (lambda x: x)
            self._print_rich(f"[info]ℹ {esc(message)}[/info]")

        self._route_output("info", message, None, ci, interactive)

    def debug(self, message: str) -> None:
        """Display a debug message (only in verbose mode)."""
        if not self.verbose:
            return

        def interactive() -> None:
            esc = self._escape or (lambda x: x)
            self._print_rich(f"[debug][DEBUG] {esc(message)}[/debug]")

        self._route_output("debug", message, None, None, interactive)

    def progress(self, current: int, total: int, message: str = "", speed: float | None = None) -> None:
        """Display transfer progress."""
        if self.mute or self.format == OutputFormat.QUIET:
            return

        percent = int(current / total * 100) if total > 0 else 0
        current_mb = round(current / 1024 / 1024, 1)
        total_mb = round(total / 1024 / 1024, 1)

        def ci() -> None:
            if percent % 10 == 0:
                print(f"[INFO] Transfer: {percent}% of {total_mb} MB")

        def interactive() -> None:
            speed_str = f" • {round(speed / 1024 / 1024, 1)} MB/s" if speed else ""
            step = self._current_step
            subject = step.subject if step else "INFO"
            prefix = self._format_prefix(subject, step.remote if step else False)
            style = self._get_style(subject)
            esc = self._escape or (lambda x: x)

            bar_width = 20
            filled = int(bar_width * current / total) if total > 0 else 0
            bar = "━" * filled + ("╸" + "─" * (bar_width - filled - 1) if filled < bar_width else "")

            msg = message or "Transferring"
            self._print_rich(
                f"{bar} {percent}% [{style}]{esc(prefix)}[/{style}] {esc(msg)}: {current_mb}/{total_mb} MB{speed_str}",
                end="\r"
            )

        self._route_output(
            "progress", message,
            {"current": current, "total": total, "percent": percent, "speed": speed},
            ci, interactive
        )

    def summary(self, **stats: Any) -> None:
        """Display final sync summary."""
        total_duration = round(time.time() - self._start_time, 1)
        stats["total_duration"] = total_duration

        parts = []
        if "tables" in stats:
            parts.append(f"{stats['tables']} tables")
        if "size" in stats:
            parts.append(f"{round(stats['size'] / 1024 / 1024, 1)} MB")
        parts.append(f"{total_duration}s")

        breakdown_keys = ["dump_duration", "transfer_duration", "import_duration"]
        breakdown = [f"{k.replace('_duration', '').title()}: {stats[k]}s" for k in breakdown_keys if k in stats]
        if breakdown:
            parts.append(f"({', '.join(breakdown)})")

        summary_str = " • ".join(parts)

        def ci() -> None:
            print(f"[INFO] Sync complete: {summary_str}")

        def interactive() -> None:
            self._print_rich(f"\n[success]✓ Sync complete: {summary_str}[/success]")

        self._route_output("summary", summary_str, stats, ci, interactive)

    def _json_output(self, event: str, **data: Any) -> None:
        """Output a JSON event."""
        output = {"event": event, "timestamp": time.time()}
        output.update({k: v for k, v in data.items() if v is not None})
        print(json.dumps(output), flush=True)

    def group_start(self, title: str) -> None:
        """Start a collapsible group (CI mode only)."""
        if self.format != OutputFormat.CI:
            return
        if self.ci_provider == CIProvider.GITHUB:
            print(f"::group::{title}")
        elif self.ci_provider == CIProvider.GITLAB:
            section_id = title.lower().replace(" ", "_")
            print(f"\033[0Ksection_start:{int(time.time())}:{section_id}[collapsed=true]\r\033[0K{title}")

    def group_end(self) -> None:
        """End a collapsible group (CI mode only)."""
        if self.format != OutputFormat.CI:
            return
        if self.ci_provider == CIProvider.GITHUB:
            print("::endgroup::")
        elif self.ci_provider == CIProvider.GITLAB:
            print(f"\033[0Ksection_end:{int(time.time())}:section\r\033[0K")


# Global singleton
_output_manager: OutputManager | None = None


def get_output_manager() -> OutputManager:
    """Get the global OutputManager instance."""
    global _output_manager
    if _output_manager is None:
        _output_manager = OutputManager()
    return _output_manager


def init_output_manager(
    format: str | OutputFormat = OutputFormat.INTERACTIVE,
    verbose: bool = False,
    mute: bool = False,
) -> OutputManager:
    """Initialize the global OutputManager with specific settings."""
    global _output_manager

    if isinstance(format, str):
        try:
            format = OutputFormat(format)
        except ValueError:
            format = OutputFormat.INTERACTIVE

    # Auto-detect CI mode
    if format == OutputFormat.INTERACTIVE and os.environ.get("CI"):
        format = OutputFormat.CI

    _output_manager = OutputManager(format=format, verbose=verbose, mute=mute)
    return _output_manager


def reset_output_manager() -> None:
    """Reset the global OutputManager (for testing)."""
    global _output_manager
    _output_manager = None
