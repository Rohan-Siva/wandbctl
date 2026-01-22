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
@click.option("--project", "-p", help="Filter by W&B project")
@click.option("--state", "-s", help="Filter by state (running, finished, failed)")
@click.option(
    "--by",
    type=click.Choice(["runtime", "gpu-hours"]),
    default="runtime",
    help="Sort by runtime or GPU-hours"
)
@click.option(
    "-n", "--limit",
    type=int,
    default=10,
    help="Number of runs to show (default: 10)"
)
def top(
    entity: str | None,
    project: str | None,
    state: str | None,
    by: str,
    limit: int,
):
    try:
        cache = Cache()
        
        run_count = cache.get_run_count(entity=entity, project=project)
        if run_count == 0:
            print_info("No cached runs. Run 'wandbctl sync' first.")
            cache.close()
            raise SystemExit(0)
        
        last_sync = cache.get_last_sync(entity=entity, project=project)
        print_data_source("cache", last_sync)
        
        runs = cache.query_runs(entity=entity, project=project, state=state)
        
        if not runs:
            print_info("No runs found matching criteria")
            cache.close()
            return
        
        if by == "runtime":
            sorted_runs = sorted(
                runs,
                key=lambda x: x.get("runtime_seconds") or 0,
                reverse=True
            )
        else:
            sorted_runs = sorted(
                runs,
                key=lambda x: (x.get("runtime_seconds") or 0) * (x.get("gpu_count") or 1),
                reverse=True
            )
        
        top_runs = sorted_runs[:limit]
        
        console.print()
        
        sort_label = "Runtime" if by == "runtime" else "GPU-Hours"
        table = Table(
            title=f"Top {len(top_runs)} Runs by {sort_label}",
            show_header=True,
            header_style="bold cyan"
        )
        table.add_column("#", style="dim", justify="right")
        table.add_column("Run ID", style="cyan", no_wrap=True)
        table.add_column("Project")
        table.add_column("State")
        table.add_column("Runtime", justify="right")
        table.add_column("GPUs", justify="right")
        table.add_column("GPU-Hrs", justify="right")
        
        for i, run in enumerate(top_runs, 1):
            runtime = run.get("runtime_seconds") or 0
            gpu_count = run.get("gpu_count") or 1
            gpu_hours = (runtime * gpu_count) / 3600
            
            state_val = run.get("state", "—")
            if state_val == "finished":
                state_display = f"[green]{state_val}[/green]"
            elif state_val == "running":
                state_display = f"[yellow]{state_val}[/yellow]"
            elif state_val in ("failed", "crashed"):
                state_display = f"[red]{state_val}[/red]"
            else:
                state_display = state_val
            
            table.add_row(
                str(i),
                run["id"][:8],
                run.get("project", "—"),
                state_display,
                format_duration(runtime),
                str(gpu_count),
                f"{gpu_hours:.1f}h"
            )
        
        console.print(table)
        
        if len(sorted_runs) > limit:
            console.print(f"\n[dim]Showing {limit} of {len(sorted_runs)} runs. Use -n to show more.[/dim]")
        
        cache.close()
        
    except SystemExit:
        raise
    except Exception as e:
        print_error(f"Failed to get top runs: {e}")
        raise SystemExit(1)
