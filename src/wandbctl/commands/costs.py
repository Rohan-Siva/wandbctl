from datetime import datetime, timedelta, timezone

import click

from wandbctl.cache import Cache
from wandbctl.utils.display import (
    console,
    print_error,
    print_info,
    print_data_source,
    format_duration,
)
from rich.table import Table


DEFAULT_GPU_RATE = 2.50


@click.command()
@click.option("--entity", "-e", help="Filter by W&B entity")
@click.option("--project", "-p", help="Filter by W&B project")
@click.option(
    "--rate",
    type=float,
    default=DEFAULT_GPU_RATE,
    help=f"GPU hourly rate in USD (default: ${DEFAULT_GPU_RATE})"
)
@click.option(
    "--last",
    "duration",
    help="Only include runs from last N days (e.g., '7d', '30d')"
)
def costs(entity: str | None, project: str | None, rate: float, duration: str | None):
    try:
        cache = Cache()
        
        run_count = cache.get_run_count(entity=entity, project=project)
        if run_count == 0:
            print_info("No cached runs. Run 'wandbctl sync' first.")
            cache.close()
            raise SystemExit(0)
        
        last_sync = cache.get_last_sync(entity=entity, project=project)
        print_data_source("cache", last_sync)
        
        since = None
        if duration:
            import re
            match = re.match(r"^(\d+)([dw])$", duration.lower())
            if not match:
                print_error(f"Invalid duration format: {duration}")
                cache.close()
                raise SystemExit(1)
            
            value = int(match.group(1))
            unit = match.group(2)
            if unit == "d":
                delta = timedelta(days=value)
            else:
                delta = timedelta(weeks=value)
            since = datetime.now(timezone.utc) - delta
            print_info(f"Filtering runs from last {duration}")
        
        runs = cache.query_runs(entity=entity, project=project, since=since)
        
        if not runs:
            print_info("No runs found matching criteria")
            cache.close()
            return
        
        project_stats = {}
        
        for run in runs:
            proj = run.get("project", "unknown")
            if proj not in project_stats:
                project_stats[proj] = {
                    "runs": 0,
                    "runtime_seconds": 0,
                    "gpu_seconds": 0,
                }
            
            project_stats[proj]["runs"] += 1
            runtime = run.get("runtime_seconds") or 0
            gpu_count = run.get("gpu_count") or 1
            project_stats[proj]["runtime_seconds"] += runtime
            project_stats[proj]["gpu_seconds"] += runtime * gpu_count
        
        total_gpu_hours = sum(s["gpu_seconds"] for s in project_stats.values()) / 3600
        total_cost = total_gpu_hours * rate
        
        console.print()
        
        table = Table(title=f"Cost Estimate @ ${rate:.2f}/GPU-hr", show_header=True, header_style="bold cyan")
        table.add_column("Project", style="dim")
        table.add_column("Runs", justify="right")
        table.add_column("GPU-Hours", justify="right")
        table.add_column("Est. Cost", justify="right")
        
        sorted_projects = sorted(
            project_stats.items(),
            key=lambda x: x[1]["gpu_seconds"],
            reverse=True
        )
        
        for proj, stats in sorted_projects:
            gpu_hours = stats["gpu_seconds"] / 3600
            cost = gpu_hours * rate
            table.add_row(
                proj,
                str(stats["runs"]),
                f"{gpu_hours:.1f}h",
                f"${cost:.2f}"
            )
        
        table.add_row("", "", "", "")
        table.add_row(
            "[bold]Total[/bold]",
            f"[bold]{sum(s['runs'] for s in project_stats.values())}[/bold]",
            f"[bold]{total_gpu_hours:.1f}h[/bold]",
            f"[bold green]${total_cost:.2f}[/bold green]"
        )
        
        console.print(table)
        
        console.print()
        console.print(f"[dim]Rate: ${rate:.2f}/GPU-hour | Change with --rate[/dim]")
        
        cache.close()
        
    except SystemExit:
        raise
    except Exception as e:
        print_error(f"Failed to calculate costs: {e}")
        raise SystemExit(1)
