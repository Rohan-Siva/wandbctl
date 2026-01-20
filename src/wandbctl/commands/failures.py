import json
from collections import defaultdict
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


@click.command()
@click.option("--entity", "-e", help="Filter by W&B entity")
@click.option("--project", "-p", help="Filter by W&B project")
@click.option(
    "--last",
    "duration",
    help="Only analyze runs from last N days (e.g., '7d', '30d')"
)
def failures(entity: str | None, project: str | None, duration: str | None):
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
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                if unit == "d":
                    delta = timedelta(days=value)
                else:
                    delta = timedelta(weeks=value)
                since = datetime.now(timezone.utc) - delta
        
        runs = cache.query_runs(entity=entity, project=project, since=since)
        
        failed_runs = [r for r in runs if r.get("state") in ("failed", "crashed")]
        
        if not failed_runs:
            print_info("No failed runs found")
            cache.close()
            return
        
        console.print()
        
        total_runs = len(runs)
        failure_rate = (len(failed_runs) / total_runs) * 100 if total_runs > 0 else 0
        
        console.print(f"[bold]Failure Analysis[/bold]")
        console.print(f"Total runs: {total_runs}")
        console.print(f"Failed runs: {len(failed_runs)} ({failure_rate:.1f}%)")
        console.print()
        
        early_failures = [r for r in failed_runs if (r.get("runtime_seconds") or 0) < 300]
        medium_failures = [r for r in failed_runs if 300 <= (r.get("runtime_seconds") or 0) < 3600]
        late_failures = [r for r in failed_runs if (r.get("runtime_seconds") or 0) >= 3600]
        
        table = Table(title="Failure Breakdown", show_header=True, header_style="bold red")
        table.add_column("Category", style="dim")
        table.add_column("Count", justify="right")
        table.add_column("Description")
        
        table.add_row("Early (<5min)", str(len(early_failures)), "Config/setup issues")
        table.add_row("Medium (5min-1hr)", str(len(medium_failures)), "Runtime errors")
        table.add_row("Late (>1hr)", str(len(late_failures)), "OOM/timeout issues")
        
        console.print(table)
        console.print()
        
        by_project = defaultdict(int)
        for run in failed_runs:
            by_project[run.get("project", "unknown")] += 1
        
        if by_project:
            proj_table = Table(title="Failures by Project", show_header=True, header_style="bold yellow")
            proj_table.add_column("Project", style="dim")
            proj_table.add_column("Failures", justify="right")
            
            for proj, count in sorted(by_project.items(), key=lambda x: x[1], reverse=True)[:5]:
                proj_table.add_row(proj, str(count))
            
            console.print(proj_table)
        
        cache.close()
        
    except SystemExit:
        raise
    except Exception as e:
        print_error(f"Failed to analyze failures: {e}")
        raise SystemExit(1)
