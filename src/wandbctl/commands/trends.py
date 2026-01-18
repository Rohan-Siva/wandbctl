from datetime import datetime, timedelta, timezone
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


SPARKLINE_CHARS = " ▁▂▃▄▅▆▇█"


def get_sparkline(values: list[int]) -> str:
    if not values or max(values) == 0:
        return "▁" * len(values)
    
    max_val = max(values)
    result = []
    for v in values:
        idx = int((v / max_val) * (len(SPARKLINE_CHARS) - 1))
        result.append(SPARKLINE_CHARS[idx])
    return "".join(result)


@click.command()
@click.option("--entity", "-e", help="Filter by W&B entity")
@click.option("--project", "-p", help="Filter by W&B project")
@click.option(
    "--last",
    "duration",
    default="30d",
    help="Time period to analyze (e.g., '7d', '30d', '90d')"
)
@click.option(
    "--group",
    type=click.Choice(["day", "week"]),
    default="day",
    help="Group by day or week"
)
def trends(entity: str | None, project: str | None, duration: str, group: str):
    try:
        cache = Cache()
        
        run_count = cache.get_run_count(entity=entity, project=project)
        if run_count == 0:
            print_info("No cached runs. Run 'wandbctl sync' first.")
            cache.close()
            raise SystemExit(0)
        
        last_sync = cache.get_last_sync(entity=entity, project=project)
        print_data_source("cache", last_sync)
        
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
        runs = cache.query_runs(entity=entity, project=project, since=since)
        
        if not runs:
            print_info(f"No runs found in the last {duration}")
            cache.close()
            return
        
        run_counts = defaultdict(int)
        runtime_totals = defaultdict(int)
        
        for run in runs:
            created = run.get("created_at")
            if not created:
                continue
            
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            
            if group == "day":
                key = created.strftime("%Y-%m-%d")
            else:
                key = created.strftime("%Y-W%W")
            
            run_counts[key] += 1
            runtime_totals[key] += run.get("runtime_seconds") or 0
        
        if group == "day":
            current = since.date()
            end = datetime.now(timezone.utc).date()
            all_keys = []
            while current <= end:
                all_keys.append(current.strftime("%Y-%m-%d"))
                current += timedelta(days=1)
        else:
            all_keys = sorted(run_counts.keys())
        
        count_values = [run_counts.get(k, 0) for k in all_keys]
        runtime_values = [runtime_totals.get(k, 0) for k in all_keys]
        
        console.print()
        console.print(f"[bold]Trends for last {duration}[/bold]")
        console.print()
        
        console.print(f"[cyan]Runs:[/cyan]      {get_sparkline(count_values)}  ({sum(count_values)} total)")
        console.print(f"[cyan]Runtime:[/cyan]   {get_sparkline(runtime_values)}  ({format_duration(sum(runtime_values))} total)")
        
        console.print()
        
        if count_values:
            avg_runs = sum(count_values) / len([v for v in count_values if v > 0]) if any(count_values) else 0
            max_runs = max(count_values)
            peak_idx = count_values.index(max_runs)
            peak_date = all_keys[peak_idx] if peak_idx < len(all_keys) else "N/A"
            
            console.print(f"[dim]Avg runs/{group}:[/dim] {avg_runs:.1f}")
            console.print(f"[dim]Peak:[/dim] {max_runs} runs on {peak_date}")
        
        cache.close()
        
    except SystemExit:
        raise
    except Exception as e:
        print_error(f"Failed to get trends: {e}")
        raise SystemExit(1)
