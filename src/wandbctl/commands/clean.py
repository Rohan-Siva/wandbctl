from datetime import datetime, timedelta, timezone

import click

from wandbctl.cache import Cache
from wandbctl.utils.display import (
    console,
    print_error,
    print_info,
    print_success,
    print_warning,
)


@click.command()
@click.option(
    "--older-than",
    "days",
    type=int,
    default=90,
    help="Delete runs older than N days (default: 90)"
)
@click.option("--dry-run", is_flag=True, help="Show what would be deleted without deleting")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
def clean(days: int, dry_run: bool, force: bool):
    try:
        cache = Cache()
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        runs = cache.query_runs()
        old_runs = []
        for run in runs:
            created = run.get("created_at")
            if created:
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                if created < cutoff:
                    old_runs.append(run)
        
        if not old_runs:
            print_success(f"No runs older than {days} days found")
            cache.close()
            return
        
        print_info(f"Found {len(old_runs)} runs older than {days} days")
        
        if dry_run:
            console.print("\n[dim]Dry run - no changes made[/dim]")
            for run in old_runs[:10]:
                console.print(f"  Would delete: {run['id'][:8]} ({run['project']})")
            if len(old_runs) > 10:
                console.print(f"  ... and {len(old_runs) - 10} more")
            cache.close()
            return
        
        if not force:
            print_warning(f"This will delete {len(old_runs)} runs from the cache")
            if not click.confirm("Continue?"):
                print_info("Aborted")
                cache.close()
                return
        
        deleted = cache.delete_runs_before(cutoff)
        print_success(f"Deleted {deleted} runs from cache")
        
        cache.close()
        
    except SystemExit:
        raise
    except Exception as e:
        print_error(f"Failed to clean cache: {e}")
        raise SystemExit(1)
