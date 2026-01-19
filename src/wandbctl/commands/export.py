import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import click

from wandbctl.cache import Cache
from wandbctl.utils.display import (
    console,
    print_error,
    print_info,
    print_success,
    print_data_source,
)


@click.command()
@click.option("--entity", "-e", help="Filter by W&B entity")
@click.option("--project", "-p", help="Filter by W&B project")
@click.option("--state", "-s", help="Filter by state (running, finished, failed)")
@click.option(
    "--last",
    "duration",
    help="Only include runs from last N days (e.g., '7d', '30d')"
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output file path (default: stdout)"
)
@click.option("--pretty", is_flag=True, help="Pretty print JSON output")
def export(
    entity: str | None,
    project: str | None,
    state: str | None,
    duration: str | None,
    output: str | None,
    pretty: bool,
):
    try:
        cache = Cache()
        
        run_count = cache.get_run_count(entity=entity, project=project)
        if run_count == 0:
            print_info("No cached runs. Run 'wandbctl sync' first.")
            cache.close()
            raise SystemExit(0)
        
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
        
        runs = cache.query_runs(entity=entity, project=project, state=state, since=since)
        
        if not runs:
            print_info("No runs found matching criteria")
            cache.close()
            return
        
        export_data = []
        for run in runs:
            run_export = {
                "id": run["id"],
                "entity": run["entity"],
                "project": run["project"],
                "name": run["name"],
                "state": run["state"],
                "runtime_seconds": run["runtime_seconds"],
                "gpu_count": run["gpu_count"],
            }
            
            if run.get("created_at"):
                run_export["created_at"] = run["created_at"].isoformat() if hasattr(run["created_at"], 'isoformat') else str(run["created_at"])
            
            if run.get("config"):
                cfg = run["config"]
                if isinstance(cfg, str):
                    cfg = json.loads(cfg)
                run_export["config"] = cfg
            
            if run.get("summary"):
                summary = run["summary"]
                if isinstance(summary, str):
                    summary = json.loads(summary)
                run_export["summary"] = {k: v for k, v in summary.items() if not k.startswith("_")}
            
            export_data.append(run_export)
        
        if pretty:
            json_output = json.dumps(export_data, indent=2, default=str)
        else:
            json_output = json.dumps(export_data, default=str)
        
        if output:
            Path(output).write_text(json_output)
            print_success(f"Exported {len(export_data)} runs to {output}")
        else:
            console.print(json_output)
        
        cache.close()
        
    except SystemExit:
        raise
    except Exception as e:
        print_error(f"Failed to export runs: {e}")
        raise SystemExit(1)
