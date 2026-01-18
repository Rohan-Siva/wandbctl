"""Zombie run detection command."""

from datetime import datetime, timezone

import click
from rich.progress import Progress, SpinnerColumn, TextColumn

from wandbctl.api import WandbClient
from wandbctl.cache import Cache
from wandbctl.utils.display import (
    console,
    print_error,
    print_info,
    print_success,
    print_warning,
    print_data_source,
    create_zombies_table,
)


def classify_zombie(
    run: dict,
    threshold_minutes: int,
    avg_runtime: float | None,
) -> dict | None:
    """
    Classify if a run is a zombie.
    
    Returns zombie info dict if zombie, None otherwise.
    """
    updated_at = run.get("updated_at")
    runtime = run.get("runtime_seconds")
    
    if not updated_at:
        return None
    
    now = datetime.now(timezone.utc)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    
    minutes_since_update = (now - updated_at).total_seconds() / 60
    
    if minutes_since_update < threshold_minutes:
        return None
    
    confidence = "medium"
    reasons = []
    
    if minutes_since_update > threshold_minutes * 2:
        confidence = "high"
        reasons.append(f"no updates for {int(minutes_since_update)}m")
    else:
        reasons.append(f"no updates for {int(minutes_since_update)}m")
    
    if avg_runtime and runtime:
        if runtime > avg_runtime * 3:
            confidence = "high"
            reasons.append("runtime 3× above average")
        elif runtime > avg_runtime * 2:
            reasons.append("runtime 2× above average")
    
    return {
        "id": run["id"],
        "entity": run["entity"],
        "project": run["project"],
        "name": run.get("name", run["id"]),
        "state": run["state"],
        "runtime_seconds": runtime,
        "updated_at": updated_at,
        "confidence": confidence,
        "reasons": reasons,
    }


@click.command()
@click.option("--entity", "-e", help="Filter by W&B entity")
@click.option("--project", "-p", help="Filter by W&B project")
@click.option(
    "--threshold",
    "-t",
    type=int,
    default=15,
    help="Minutes without updates to flag as zombie (default: 15)"
)
def zombies(entity: str | None, project: str | None, threshold: int):
    """Detect stalled/zombie runs that are active but not progressing.
    
    A zombie run is a run that:
    
    \b
    - Has state = "running"
    - Has not logged metrics/updates for N minutes
    - May have abnormally long runtime compared to similar runs
    
    Runs are classified with confidence levels:
    
    \b
    - HIGH: No updates for 2× threshold, or runtime 3× average
    - MEDIUM: No updates for threshold minutes
    
    Examples:
    
        wandbctl zombies
        
        wandbctl zombies --threshold 30
        
        wandbctl zombies --entity my-team --project my-project
    """
    try:
        client = WandbClient()
        cache = Cache()
        
        entity = entity or client.default_entity
        if not entity:
            print_error("No entity specified and no default entity found.")
            raise SystemExit(1)
        
        print_data_source("live", None)
        print_info(f"Checking running runs (threshold: {threshold}m)...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching running runs...", total=None)
            
            running_runs = []
            for run_meta in client.list_running_runs(entity=entity, project=project):
                running_runs.append({
                    "id": run_meta.id,
                    "entity": run_meta.entity,
                    "project": run_meta.project,
                    "name": run_meta.name,
                    "state": run_meta.state,
                    "runtime_seconds": run_meta.runtime_seconds,
                    "updated_at": run_meta.updated_at,
                })
            
            progress.update(task, description=f"Found {len(running_runs)} running runs")
        
        if not running_runs:
            print_success("No running runs found.")
            cache.close()
            return
        
        stats = cache.get_usage_stats(entity=entity, project=project)
        total_runs = stats.get("finished_runs", 0)
        total_runtime = stats.get("total_runtime_seconds", 0)
        avg_runtime = total_runtime / total_runs if total_runs > 0 else None
        
        zombie_runs = []
        for run in running_runs:
            zombie = classify_zombie(run, threshold, avg_runtime)
            if zombie:
                zombie_runs.append(zombie)
        
        console.print()
        
        if not zombie_runs:
            print_success(f"No zombies detected among {len(running_runs)} running runs.")
        else:
            print_warning(f"Found {len(zombie_runs)} potential zombie run(s)")
            console.print()
            table = create_zombies_table(zombie_runs)
            console.print(table)
            console.print()
            console.print("[dim]Verify these runs manually before terminating.[/dim]")
        
        cache.close()
        
    except SystemExit:
        raise
    except Exception as e:
        print_error(f"Failed to detect zombies: {e}")
        raise SystemExit(1)
