"""Sync and status commands for cache management."""

from datetime import datetime, timezone

import click
from rich.progress import Progress, SpinnerColumn, TextColumn

from wandbctl.api import WandbClient
from wandbctl.cache import Cache
from wandbctl.utils.display import (
    console,
    print_success,
    print_error,
    print_info,
    create_status_table,
)


@click.command()
@click.option("--entity", "-e", help="W&B entity (username or team)")
@click.option("--project", "-p", help="W&B project name")
@click.option(
    "--since",
    type=click.DateTime(),
    help="Only sync runs created after this date"
)
def sync(entity: str | None, project: str | None, since: datetime | None):
    """Pull latest run data from W&B into local cache.
    
    Examples:
    
        wandbctl sync
        
        wandbctl sync --entity my-team --project my-project
        
        wandbctl sync --since 2024-01-01
    """
    try:
        client = WandbClient()
        cache = Cache()
        
        entity = entity or client.default_entity
        if not entity:
            print_error("No entity specified and no default entity found. Set WANDB_API_KEY or use --entity.")
            raise SystemExit(1)
        
        print_info(f"Syncing runs from {entity}" + (f"/{project}" if project else ""))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching runs...", total=None)
            
            runs = []
            filters = {}
            if since:
                filters["created_at"] = {"$gte": since.isoformat()}
            
            for run_meta in client.list_runs(entity=entity, project=project, filters=filters if filters else None):
                runs.append(run_meta)
                progress.update(task, description=f"Fetched {len(runs)} runs...")
            
            progress.update(task, description="Saving to cache...")
            count = cache.upsert_runs(runs)
            cache.log_sync(entity, project, count)
        
        print_success(f"Synced {count} runs to cache")
        cache.close()
        
    except ConnectionError as e:
        print_error(str(e))
        raise SystemExit(1)
    except Exception as e:
        print_error(f"Sync failed: {e}")
        raise SystemExit(1)


@click.command()
@click.option("--entity", "-e", help="Filter by entity")
@click.option("--project", "-p", help="Filter by project")
def status(entity: str | None, project: str | None):
    """Show cache status and freshness information.
    
    Examples:
    
        wandbctl status
        
        wandbctl status --entity my-team
    """
    try:
        cache = Cache()
        
        run_count = cache.get_run_count(entity=entity, project=project)
        cache_size = cache.get_cache_size_bytes()
        last_sync = cache.get_last_sync(entity=entity, project=project)
        
        table = create_status_table(
            run_count=run_count,
            cache_size=cache_size,
            last_sync=last_sync,
            cache_path=str(cache.path),
        )
        
        console.print(table)
        
        if run_count == 0:
            print_info("No cached runs. Run 'wandbctl sync' to populate cache.")
        
        cache.close()
        
    except Exception as e:
        print_error(f"Failed to get status: {e}")
        raise SystemExit(1)
