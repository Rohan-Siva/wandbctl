import click

from wandbctl.cache import Cache
from wandbctl.utils.display import (
    console,
    print_error,
    print_info,
    format_duration,
)


@click.command()
@click.option("--entity", "-e", help="Filter by W&B entity")
@click.option("--project", "-p", help="Filter by W&B project")
def summary(entity: str | None, project: str | None):
    try:
        cache = Cache()
        
        run_count = cache.get_run_count(entity=entity, project=project)
        if run_count == 0:
            print_info("No cached runs. Run 'wandbctl sync' first.")
            cache.close()
            raise SystemExit(0)
        
        stats = cache.get_usage_stats(entity=entity, project=project)
        
        total = stats["total_runs"]
        finished = stats["finished_runs"]
        failed = stats["failed_runs"]
        running = stats["running_runs"]
        runtime = format_duration(stats["total_runtime_seconds"])
        gpu_hrs = stats["total_gpu_seconds"] / 3600
        
        success_rate = (finished / total) * 100 if total > 0 else 0
        
        line = f"[bold]{total}[/bold] runs"
        line += f" | [green]{finished}[/green] ok"
        line += f" | [red]{failed}[/red] fail"
        if running > 0:
            line += f" | [yellow]{running}[/yellow] running"
        line += f" | {runtime} runtime"
        line += f" | {gpu_hrs:.0f} GPU-hrs"
        line += f" | {success_rate:.0f}% success"
        
        console.print(line)
        
        cache.close()
        
    except SystemExit:
        raise
    except Exception as e:
        print_error(f"Failed to get summary: {e}")
        raise SystemExit(1)
