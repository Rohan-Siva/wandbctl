"""Display utilities for rich terminal output."""

from datetime import datetime, timezone
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


console = Console()


def format_duration(seconds: Optional[int]) -> str:
    """Format seconds into human-readable duration."""
    if seconds is None:
        return "—"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return f"{seconds}s"


def format_time_ago(dt: Optional[datetime]) -> str:
    """Format datetime as 'X ago' string."""
    if dt is None:
        return "—"
    
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    diff = now - dt
    total_seconds = int(diff.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds}s ago"
    elif total_seconds < 3600:
        return f"{total_seconds // 60}m ago"
    elif total_seconds < 86400:
        return f"{total_seconds // 3600}h ago"
    else:
        return f"{total_seconds // 86400}d ago"


def format_bytes(size_bytes: int) -> str:
    """Format bytes into human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def print_data_source(
    source: str,
    last_sync: Optional[datetime] = None,
) -> None:
    """Print data source indicator."""
    if source == "cache" and last_sync:
        age = format_time_ago(last_sync)
        text = Text()
        text.append("Data source: ", style="dim")
        text.append("cache", style="cyan")
        text.append(f" (last sync: {age})", style="dim")
        console.print(text)
    elif source == "live":
        text = Text()
        text.append("Data source: ", style="dim")
        text.append("live", style="green")
        text.append(" (fetched now)", style="dim")
        console.print(text)
    else:
        console.print(f"[dim]Data source: {source}[/dim]")


def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"[red bold]✗[/red bold] {message}")


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[green bold]✓[/green bold] {message}")


def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[yellow bold]⚠[/yellow bold] {message}")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[blue]ℹ[/blue] {message}")


def create_usage_table(stats: dict) -> Table:
    """Create usage statistics table."""
    table = Table(title="Usage Summary", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")
    
    table.add_row("Total runs", str(stats["total_runs"]))
    table.add_row("  Finished", f"[green]{stats['finished_runs']}[/green]")
    table.add_row("  Running", f"[yellow]{stats['running_runs']}[/yellow]")
    table.add_row("  Failed", f"[red]{stats['failed_runs']}[/red]")
    table.add_row("  Crashed", f"[red]{stats['crashed_runs']}[/red]")
    table.add_row("", "")
    table.add_row("Total runtime", format_duration(stats["total_runtime_seconds"]))
    table.add_row(
        "Est. GPU-hours",
        f"{stats['total_gpu_seconds'] / 3600:.1f}h"
    )
    table.add_row("Projects", str(stats["project_count"]))
    
    return table


def create_zombies_table(zombies: list[dict]) -> Table:
    """Create zombie runs table."""
    table = Table(title="Zombie Runs", show_header=True, header_style="bold red")
    table.add_column("Run ID", style="cyan", no_wrap=True)
    table.add_column("Project")
    table.add_column("Runtime", justify="right")
    table.add_column("Last Update", justify="right")
    table.add_column("Confidence", justify="center")
    
    for z in zombies:
        confidence_style = "red bold" if z["confidence"] == "high" else "yellow"
        table.add_row(
            z["id"][:8],
            z["project"],
            format_duration(z["runtime_seconds"]),
            format_time_ago(z["updated_at"]),
            f"[{confidence_style}]{z['confidence'].upper()}[/{confidence_style}]"
        )
    
    return table


def create_status_table(
    run_count: int,
    cache_size: int,
    last_sync: Optional[datetime],
    cache_path: str,
) -> Table:
    """Create cache status table."""
    table = Table(title="Cache Status", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="dim")
    table.add_column("Value")
    
    table.add_row("Cache location", cache_path)
    table.add_row("Cache size", format_bytes(cache_size))
    table.add_row("Cached runs", str(run_count))
    table.add_row("Last sync", format_time_ago(last_sync) if last_sync else "never")
    
    return table


def print_preflight_result(
    passed: bool,
    checks: list[dict],
) -> None:
    """Print preflight check results."""
    if passed:
        panel = Panel(
            "[green bold]✓ Preflight passed[/green bold]\n\nAll checks passed. Safe to launch.",
            border_style="green"
        )
    else:
        lines = ["[red bold]✗ Preflight failed[/red bold]\n"]
        for check in checks:
            if not check["passed"]:
                lines.append(f"• {check['message']}")
        lines.append("\n[dim]Fix issues or run with --force[/dim]")
        panel = Panel("\n".join(lines), border_style="red")
    
    console.print(panel)
