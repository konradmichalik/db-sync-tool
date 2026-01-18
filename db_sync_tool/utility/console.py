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


# Known sync steps for progress tracking
SYNC_STEPS = [
    "Loading host configuration",
    "Validating configuration",
    "Sync mode:",
    "Sync base:",
    "Checking database configuration",  # origin
    "Initialize remote SSH connection",  # origin (optional)
    "Validating database credentials",  # origin
    "Database version:",  # origin
    "Creating database dump",
    "table(s) exported",
    "Downloading database dump",  # or uploading
    "Cleaning up",  # origin
    "Checking database configuration",  # target
    "Initialize remote SSH connection",  # target (optional)
    "Validating database credentials",  # target
    "Database version:",  # target
    "Importing database dump",
    "Cleaning up",  # target
    "Successfully synchronized",
]


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
        verbose: int | bool = 0,
        mute: bool = False,
        total_steps: int = 18,  # Default estimate for typical receiver sync
    ):
        self.format = format
        # Support both bool (legacy) and int (new -v/-vv)
        self.verbose = int(verbose) if isinstance(verbose, (int, bool)) else 0
        self.mute = mute
        self.ci_provider = self._detect_ci_provider()
        self._current_step: StepInfo | None = None
        self._steps_completed = 0
        self._total_steps = total_steps
        self._start_time = time.time()
        self._console: Any = None
        self._escape: Callable[[str], str] | None = None
        self._gitlab_section_id: str | None = None
        self._sync_stats: dict[str, Any] = {}  # Track tables, size, durations

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
            # Ensure output is flushed immediately (especially for \r endings)
            print(plain, flush=True, **kwargs)

    def _route_output(
        self,
        event: str,
        message: str,
        json_data: dict[str, Any] | None = None,
        ci_handler: Callable[[], None] | None = None,
        interactive_handler: Callable[[], None] | None = None,
        force: bool = False,
    ) -> bool:
        """Route output to appropriate handler based on format. Returns True if handled."""
        if self.format == OutputFormat.QUIET and not force:
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

    def _setup_step(self, message: str, subject: str = "INFO", remote: bool = False) -> None:
        """Set up step context without displaying (for legacy API compatibility)."""
        self._current_step = StepInfo(name=message, subject=subject, remote=remote)
        # Auto-extract stats from known message patterns
        self._extract_stats_from_message(message)

    def _extract_stats_from_message(self, message: str) -> None:
        """Extract statistics from known message patterns."""
        import re
        # Extract table count from "X table(s) exported"
        match = re.search(r"(\d+)\s+table\(s\)\s+exported", message)
        if match:
            self._sync_stats["tables"] = int(match.group(1))

        # Extract SSH connection info for origin/target hosts
        # Pattern: "Initialize remote SSH connection user@host"
        match = re.search(r"Initialize remote SSH connection\s+(\S+)@(\S+)", message)
        if match:
            host = match.group(2)
            # Determine if this is origin or target based on current step context
            if self._current_step and "ORIGIN" in self._current_step.subject.upper():
                self._sync_stats["origin_host"] = host
            elif self._current_step and "TARGET" in self._current_step.subject.upper():
                self._sync_stats["target_host"] = host

        # Extract local path info for local hosts
        if "Checking database configuration" in message and not self._sync_stats.get("origin_host"):
            if self._current_step and "ORIGIN" in self._current_step.subject.upper():
                self._sync_stats["origin_host"] = "local"
        if "Checking database configuration" in message and not self._sync_stats.get("target_host"):
            if self._current_step and "TARGET" in self._current_step.subject.upper():
                self._sync_stats["target_host"] = "local"

    def track_stat(self, key: str, value: Any) -> None:
        """Track a sync statistic for the final summary."""
        self._sync_stats[key] = value

    def step(self, message: str, subject: str = "INFO", remote: bool = False, debug: bool = False) -> None:
        """Display a step message with spinner (for long-running operations in progress)."""
        # Debug messages only shown at verbose level 2 (-vv)
        if self.mute or (debug and self.verbose < 2):
            return

        self._current_step = StepInfo(name=message, subject=subject, remote=remote)
        prefix = self._format_prefix(subject, remote)

        def ci() -> None:
            print(f"[INFO] {prefix} {message}")

        def interactive() -> None:
            # Verbose mode prints in success(), compact mode updates progress bar there too
            pass

        self._route_output("step", message, {"subject": subject, "remote": remote}, ci, interactive)

    def _render_progress_bar(self, width: int = 20) -> str:
        """Render a progress bar based on completed steps."""
        if self._total_steps <= 0:
            return "━" * width
        progress = min(self._steps_completed / self._total_steps, 1.0)
        filled = int(width * progress)
        if filled < width:
            return "━" * filled + "╸" + "─" * (width - filled - 1)
        return "━" * width

    def success(self, message: str | None = None, **stats: Any) -> None:
        """Mark current step as successful."""
        if self.mute and not stats:
            return

        self._steps_completed += 1
        step = self._current_step
        display_msg = message or (step.name if step else "Operation")

        # Detect final sync message and show as summary
        is_final = "Successfully synchronized" in display_msg

        def ci() -> None:
            subject = step.subject if step else "INFO"
            prefix = self._format_prefix(subject, step.remote if step else False)
            print(f"[INFO] {prefix} {display_msg}")

        def interactive() -> None:
            subject = step.subject if step else "INFO"
            prefix = self._format_prefix(subject, step.remote if step else False)
            style = self._get_style(subject)
            esc = self._escape or (lambda x: x)

            # Clear line
            print("\033[2K\r", end="")

            if self.verbose >= 1:
                # Verbose (-v/-vv): Plain text output without symbols
                self._print_rich(f"[{style}]{esc(prefix)}[/{style}] {esc(display_msg)}", highlight=False)
                if stats:
                    stats_str = " • ".join(f"{k}: {v}" for k, v in stats.items())
                    self._print_rich(f"  [dim]{stats_str}[/dim]", highlight=False)
            elif is_final:
                # Final message: Show summary-style output
                duration = round(time.time() - self._start_time, 1)

                # Build context info (origin → target)
                context_parts = []
                if self._sync_stats.get("origin_host"):
                    context_parts.append(self._sync_stats["origin_host"])
                if self._sync_stats.get("target_host"):
                    context_parts.append(self._sync_stats["target_host"])
                context = " → ".join(context_parts) if context_parts else ""

                # Build stats
                stats_parts = []
                if self._sync_stats.get("tables"):
                    stats_parts.append(f"{self._sync_stats['tables']} tables")
                if self._sync_stats.get("size"):
                    stats_parts.append(f"{round(self._sync_stats['size'] / 1024 / 1024, 1)} MB")
                stats_parts.append(f"{duration}s")

                # Build summary
                if context:
                    summary_str = f"{context} • " + " • ".join(stats_parts)
                else:
                    summary_str = " • ".join(stats_parts)

                self._print_rich(f"[success]✓ Sync complete:[/success] {summary_str}", highlight=False)
            else:
                # Compact: Single progress bar line (updates in place)
                bar = self._render_progress_bar()
                step_info = f"{self._steps_completed}/{self._total_steps}"
                # Truncate message if too long
                max_msg_len = 50
                short_msg = display_msg[:max_msg_len] + "..." if len(display_msg) > max_msg_len else display_msg
                self._print_rich(
                    f"{bar} {step_info} • [{style}]{esc(prefix)}[/{style}] {esc(short_msg)}",
                    end="\r", highlight=False
                )

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
            self._print_rich(f"[error]✗ [ERROR] {esc(message)}[/error]", highlight=False)
            if exception and self.verbose >= 2:
                self._print_rich(f"  [dim]{esc(str(exception))}[/dim]", highlight=False)

        exc_str = str(exception) if exception else None
        self._route_output("error", message, {"exception": exc_str}, ci, interactive, force=True)

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
            self._print_rich(f"[warning]⚠ [WARNING] {esc(message)}[/warning]", highlight=False)

        self._route_output("warning", message, None, ci, interactive)

    def info(self, message: str) -> None:
        """Display an info message."""
        if self.mute:
            return

        def ci() -> None:
            print(f"[INFO] {message}")

        def interactive() -> None:
            esc = self._escape or (lambda x: x)
            self._print_rich(f"[info]ℹ {esc(message)}[/info]", highlight=False)

        self._route_output("info", message, None, ci, interactive)

    def debug(self, message: str) -> None:
        """Display a debug message (only at -vv level)."""
        if self.verbose < 2:
            return

        def interactive() -> None:
            esc = self._escape or (lambda x: x)
            self._print_rich(f"[debug][DEBUG] {esc(message)}[/debug]", highlight=False)

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
                end="\r", highlight=False
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
            # Clear progress bar line and show summary
            print("\033[2K\r", end="")
            self._print_rich(f"[success]✓ Sync complete: {summary_str}[/success]", highlight=False)

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
            self._gitlab_section_id = title.lower().replace(" ", "_")
            print(f"\033[0Ksection_start:{int(time.time())}:{self._gitlab_section_id}[collapsed=true]\r\033[0K{title}")

    def group_end(self) -> None:
        """End a collapsible group (CI mode only)."""
        if self.format != OutputFormat.CI:
            return
        if self.ci_provider == CIProvider.GITHUB:
            print("::endgroup::")
        elif self.ci_provider == CIProvider.GITLAB and self._gitlab_section_id:
            print(f"\033[0Ksection_end:{int(time.time())}:{self._gitlab_section_id}\r\033[0K")
            self._gitlab_section_id = None


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
    verbose: int | bool = 0,
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
