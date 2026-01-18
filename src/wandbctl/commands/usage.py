from datetime import datetime, timedelta, timezone
import re

import click

from wandbctl.cache import Cache
from wandbctl.utils.display import (
    console,
    print_error,
    print_info,
    print_data_source,
    create_usage_table,
)


def parse_duration(duration_str: str) -> timedelta:
    match = re.match(r"^(\d+)([hdwm])$", duration_str.lower())
    if not match:
        raise ValueError(f"Invalid duration format: {duration_str}. Use format like '24h', '7d', '1w'")
    
    value = int(match.group(1))
    unit = match.group(2)
    
    if unit == "h":
        return timedelta(hours=value)
    elif unit == "d":
        return timedelta(days=value)
    elif unit == "w":
        return timedelta(weeks=value)
    elif unit == "m":
        return timedelta(days=value * 30)
    else:
        raise ValueError(f"Unknown duration unit: {unit}")


@click.command()
@click.option("--entity", "-e", help="Filter by W&B entity")
@click.option("--project", "-p", help="Filter by W&B project")
@click.option(
    "--last",
    "duration",
    help="Only include runs from last N hours/days (e.g., '24h', '7d')"
)
@click.option("--refresh", is_flag=True, help="Force sync before showing usage")
def usage(entity: str | None, project: str | None, duration: str | None, refresh: bool):
    try:
        cache = Cache()
        
        if refresh:
            from wandbctl.api import WandbClient
            from wandbctl.commands.sync import sync
            ctx = click.Context(sync)
            ctx.invoke(sync, entity=entity, project=project, since=None)
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
            try:
                delta = parse_duration(duration)
                since = datetime.now(timezone.utc) - delta
                print_info(f"Filtering runs from last {duration}")
            except ValueError as e:
                print_error(str(e))
                cache.close()
                raise SystemExit(1)
        
        stats = cache.get_usage_stats(entity=entity, project=project, since=since)
        
        console.print()
        table = create_usage_table(stats)
        console.print(table)
        
        cache.close()
        
    except SystemExit:
        raise
    except Exception as e:
        print_error(f"Failed to get usage: {e}")
        raise SystemExit(1)
