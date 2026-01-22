from collections import defaultdict

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


@click.command()
@click.option("--entity", "-e", help="Filter by W&B entity")
def projects(entity: str | None):
    try:
        cache = Cache()
        
        run_count = cache.get_run_count(entity=entity)
        if run_count == 0:
            print_info("No cached runs. Run 'wandbctl sync' first.")
            cache.close()
            raise SystemExit(0)
        
        last_sync = cache.get_last_sync(entity=entity)
        print_data_source("cache", last_sync)
        
        runs = cache.query_runs(entity=entity)
        
        project_stats = defaultdict(lambda: {
            "runs": 0,
            "finished": 0,
            "failed": 0,
            "running": 0,
            "runtime": 0,
            "gpu_hours": 0,
        })
        
        for run in runs:
            proj = run.get("project", "unknown")
            state = run.get("state", "unknown")
            runtime = run.get("runtime_seconds") or 0
            gpu_count = run.get("gpu_count") or 1
            
            project_stats[proj]["runs"] += 1
            project_stats[proj]["runtime"] += runtime
            project_stats[proj]["gpu_hours"] += (runtime * gpu_count) / 3600
            
            if state == "finished":
                project_stats[proj]["finished"] += 1
            elif state in ("failed", "crashed"):
                project_stats[proj]["failed"] += 1
            elif state == "running":
                project_stats[proj]["running"] += 1
        
        console.print()
        
        table = Table(title="Projects Overview", show_header=True, header_style="bold cyan")
        table.add_column("Project", style="dim")
        table.add_column("Runs", justify="right")
        table.add_column("OK", justify="right")
        table.add_column("Fail", justify="right")
        table.add_column("Run", justify="right")
        table.add_column("Runtime", justify="right")
        table.add_column("GPU-Hrs", justify="right")
        
        sorted_projects = sorted(
            project_stats.items(),
            key=lambda x: x[1]["runs"],
            reverse=True
        )
        
        for proj, stats in sorted_projects:
            table.add_row(
                proj,
                str(stats["runs"]),
                f"[green]{stats['finished']}[/green]",
                f"[red]{stats['failed']}[/red]" if stats["failed"] > 0 else "0",
                f"[yellow]{stats['running']}[/yellow]" if stats["running"] > 0 else "0",
                format_duration(stats["runtime"]),
                f"{stats['gpu_hours']:.1f}h"
            )
        
        console.print(table)
        
        cache.close()
        
    except SystemExit:
        raise
    except Exception as e:
        print_error(f"Failed to list projects: {e}")
        raise SystemExit(1)
