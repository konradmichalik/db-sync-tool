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


# Badge color palette - consistent styling for all badges
# Format: (background_color, text_color)
# Colors match the original Rich theme for consistency
BADGE_COLORS = {
    "origin": ("magenta", "white"),   # Magenta (same as original)
    "target": ("blue", "white"),      # Blue (same as original)
    "local": ("cyan", "black"),       # Cyan (same as original)
    "remote": ("bright_black", "white"),  # Gray
    "info": ("cyan", "black"),        # Cyan (same as original)
    "success": ("green", "white"),    # Green (same as original)
    "warning": ("yellow", "black"),   # Yellow (same as original)
    "error": ("red", "white"),        # Red (same as original)
    "debug": ("bright_black", "white"),  # Dim gray (same as original)
}

# Consistent icons
ICONS = {
    "success": "✓",
    "error": "✗",
    "warning": "⚠",
    "info": "ℹ",
    "progress": "⋯",
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
        self._text_class: Any = None
        self._style_class: Any = None
        self._panel_class: Any = None

        if self.format == OutputFormat.INTERACTIVE:
            self._init_rich()

    def _init_rich(self) -> None:
        """Initialize Rich console."""
        try:
            from rich.console import Console
            from rich.markup import escape
            from rich.theme import Theme
            from rich.text import Text
            from rich.style import Style
            from rich.panel import Panel

            theme = Theme({
                "info": "cyan", "success": "green", "warning": "yellow",
                "error": "red bold", "origin": "magenta", "target": "blue",
                "local": "cyan", "debug": "dim",
            })
            self._console = Console(theme=theme, force_terminal=True)
            self._escape = escape
            self._text_class = Text
            self._style_class = Style
            self._panel_class = Panel
        except ImportError:
            self.format = OutputFormat.CI

    def _render_badge(self, label: str, badge_type: str | None = None) -> Any:
        """
        Render a styled badge with background color.

        Args:
            label: Badge text (e.g., "ORIGIN", "REMOTE")
            badge_type: Badge type for color lookup, defaults to label.lower()

        Returns:
            Rich Text object with styled badge
        """
        if not self._text_class or not self._style_class:
            # Fallback for when Rich is not available
            return f"[{label}]"  # type: ignore[return-value]

        badge_key = (badge_type or label).lower()
        bg_color, fg_color = BADGE_COLORS.get(badge_key, ("#7f8c8d", "white"))

        style = self._style_class(color=fg_color, bgcolor=bg_color, bold=True)
        return self._text_class(f" {label} ", style=style)

    def _render_badges(self, subject: str, remote: bool = False) -> Any:
        """
        Render subject + location badges.

        Args:
            subject: Subject type (ORIGIN, TARGET, INFO, etc.)
            remote: Whether operation is on remote host

        Returns:
            Rich Text object with styled badges
        """
        if not self._text_class:
            # Fallback
            subj = subject.upper()
            if subj in ("ORIGIN", "TARGET"):
                return f"[{subj}][{'REMOTE' if remote else 'LOCAL'}]"  # type: ignore[return-value]
            return f"[{subj}]"  # type: ignore[return-value]

        result = self._text_class()
        subj = subject.upper()

        if subj in ("ORIGIN", "TARGET"):
            result.append_text(self._render_badge(subj, subj.lower()))
            result.append(" ")
            location = "REMOTE" if remote else "LOCAL"
            result.append_text(self._render_badge(location, location.lower()))
        elif subj in ("WARNING", "ERROR", "INFO", "DEBUG"):
            result.append_text(self._render_badge(subj, subj.lower()))
        else:
            result.append_text(self._render_badge(subj, "info"))

        return result

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

        # Extract host info from "Checking database configuration" message
        # Use the remote flag from current step to determine local vs remote
        if "Checking database configuration" in message and self._current_step:
            location = "remote" if self._current_step.remote else "local"
            if "ORIGIN" in self._current_step.subject.upper() and not self._sync_stats.get("origin_host"):
                self._sync_stats["origin_host"] = location
            elif "TARGET" in self._current_step.subject.upper() and not self._sync_stats.get("target_host"):
                self._sync_stats["target_host"] = location

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
            remote = step.remote if step else False
            esc = self._escape or (lambda x: x)

            # Clear line
            print("\033[2K\r", end="")

            if is_final:
                # Final message: Always show summary line
                self._print_summary_line()
            elif self.verbose >= 1:
                # Verbose (-v/-vv): Table-based output with badge
                if self._console and self._text_class:
                    self._print_table_row(subject, remote, display_msg)
                    if stats:
                        stats_str = " • ".join(f"{k}: {v}" for k, v in stats.items())
                        self._print_rich(f"           [dim]{stats_str}[/dim]", highlight=False)
                else:
                    prefix = self._format_prefix(subject, remote)
                    self._print_rich(f"{prefix} {esc(display_msg)}", highlight=False)
            else:
                # Compact: Single progress bar line (updates in place)
                bar = self._render_progress_bar()
                step_info = f"{self._steps_completed}/{self._total_steps}"
                # Truncate message if too long
                max_msg_len = 50
                short_msg = display_msg[:max_msg_len] + "..." if len(display_msg) > max_msg_len else display_msg

                if self._console and self._text_class:
                    badge = self._render_badge(subject.upper(), subject.lower())
                    line = self._text_class()
                    line.append(f"{bar} {step_info} ")
                    line.append_text(badge)
                    line.append(f"  {short_msg}")
                    self._console.print(line, end="\r", highlight=False)
                else:
                    prefix = self._format_prefix(subject, remote)
                    self._print_rich(f"{bar} {step_info} {prefix} {esc(short_msg)}", end="\r", highlight=False)

        self._route_output("success", display_msg, stats, ci, interactive)

    def _print_table_row(self, subject: str, remote: bool, message: str) -> None:
        """Print a table-style row with badge, optional location, and message."""
        if not self._console or not self._text_class:
            return

        subj = subject.upper()

        # Determine badge color
        if subj == "ORIGIN":
            badge = self._render_badge("ORIGIN", "origin")
        elif subj == "TARGET":
            badge = self._render_badge("TARGET", "target")
        else:
            badge = self._render_badge(subj, subj.lower())

        line = self._text_class()
        line.append_text(badge)

        # Only show location column for ORIGIN/TARGET
        if subj in ("ORIGIN", "TARGET"):
            location = "remote" if remote else "local"
            line.append(f"  ", style="dim")
            line.append(f"{location:<8}", style="dim")
        else:
            line.append("  ")

        line.append(message)
        self._console.print(line, highlight=False)

    def _print_summary_line(self) -> None:
        """Print the final sync summary as a simple line."""
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
        stats_str = " • ".join(stats_parts)

        # Build summary line
        if context:
            summary = f"{context} • {stats_str}"
        else:
            summary = stats_str

        # Escape summary to prevent Rich markup interpretation (e.g., IPv6 addresses with brackets)
        esc = self._escape or (lambda x: x)
        self._console.print()  # Empty line before summary
        self._print_rich(f"[green]{ICONS['success']} Sync complete:[/green] {esc(summary)}", highlight=False)

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
            # Clear line to prevent leftover characters from previous output
            print("\033[2K\r", end="")
            esc = self._escape or (lambda x: x)
            if self._console and self._text_class:
                line = self._text_class()
                line.append_text(self._render_badge("ERROR", "error"))
                line.append(f"  {ICONS['error']} {message}")
                self._console.print(line, highlight=False)
                if exception and self.verbose >= 2:
                    self._print_rich(f"  [dim]{esc(str(exception))}[/dim]", highlight=False)
            else:
                self._print_rich(f"[error]{ICONS['error']} [ERROR] {esc(message)}[/error]", highlight=False)

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
            # Clear line to prevent leftover characters from previous output
            print("\033[2K\r", end="")
            esc = self._escape or (lambda x: x)
            if self._console and self._text_class:
                line = self._text_class()
                line.append_text(self._render_badge("WARNING", "warning"))
                line.append(f"  {ICONS['warning']} {message}")
                self._console.print(line, highlight=False)
            else:
                self._print_rich(f"[warning]{ICONS['warning']} [WARNING] {esc(message)}[/warning]", highlight=False)

        self._route_output("warning", message, None, ci, interactive)

    def info(self, message: str) -> None:
        """Display an info message."""
        if self.mute:
            return

        def ci() -> None:
            print(f"[INFO] {message}")

        def interactive() -> None:
            esc = self._escape or (lambda x: x)
            if self._console and self._text_class:
                line = self._text_class()
                line.append_text(self._render_badge("INFO", "info"))
                line.append(f"  {ICONS['info']} {message}")
                self._console.print(line, highlight=False)
            else:
                self._print_rich(f"[info]{ICONS['info']} {esc(message)}[/info]", highlight=False)

        self._route_output("info", message, None, ci, interactive)

    def debug(self, message: str) -> None:
        """Display a debug message (only at -vv level)."""
        if self.verbose < 2:
            return

        def interactive() -> None:
            esc = self._escape or (lambda x: x)
            if self._console and self._text_class:
                line = self._text_class()
                line.append_text(self._render_badge("DEBUG", "debug"))
                line.append(f"  {message}")
                self._console.print(line, highlight=False)
            else:
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
            remote = step.remote if step else False

            bar_width = 20
            filled = int(bar_width * current / total) if total > 0 else 0
            bar = "━" * filled + ("╸" + "─" * (bar_width - filled - 1) if filled < bar_width else "")

            msg = message or "Transferring"

            if self._console and self._text_class:
                badges = self._render_badges(subject, remote)
                line = self._text_class()
                line.append(f"{bar} {percent}% ")
                line.append_text(badges)
                line.append(f"  {msg}: {current_mb}/{total_mb} MB{speed_str}")
                self._console.print(line, end="\r", highlight=False)
            else:
                prefix = self._format_prefix(subject, remote)
                esc = self._escape or (lambda x: x)
                style = self._get_style(subject)
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

        # Update internal stats for summary rendering
        if "tables" in stats:
            self._sync_stats["tables"] = stats["tables"]
        if "size" in stats:
            self._sync_stats["size"] = stats["size"]

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
            self._print_summary_line()

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
