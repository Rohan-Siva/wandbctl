import json

import click

from wandbctl.cache import Cache
from wandbctl.utils.display import (
    console,
    print_error,
    print_info,
)
from rich.table import Table


@click.command()
@click.argument("run_ids", nargs=-1, required=True)
@click.option("--entity", "-e", help="W&B entity (if not in cache)")
@click.option("--project", "-p", help="W&B project (if not in cache)")
def compare(run_ids: tuple[str, ...], entity: str | None, project: str | None):
    if len(run_ids) < 2:
        print_error("Need at least 2 run IDs to compare")
        raise SystemExit(1)
    
    if len(run_ids) > 5:
        print_error("Maximum 5 runs for comparison")
        raise SystemExit(1)
    
    try:
        cache = Cache()
        
        runs = cache.query_runs(entity=entity, project=project)
        
        matched_runs = []
        for run_id in run_ids:
            found = None
            for run in runs:
                if run["id"] == run_id or run["id"].startswith(run_id):
                    found = run
                    break
            
            if not found:
                print_error(f"Run not found in cache: {run_id}")
                cache.close()
                raise SystemExit(1)
            
            matched_runs.append(found)
        
        console.print()
        
        info_table = Table(title="Run Info", show_header=True, header_style="bold cyan")
        info_table.add_column("Field", style="dim")
        for run in matched_runs:
            info_table.add_column(run["id"][:8], no_wrap=True)
        
        info_fields = ["name", "state", "project"]
        for field in info_fields:
            values = [str(run.get(field, "—")) for run in matched_runs]
            info_table.add_row(field, *values)
        
        console.print(info_table)
        console.print()
        
        all_config_keys = set()
        configs = []
        for run in matched_runs:
            cfg = run.get("config")
            if isinstance(cfg, str):
                cfg = json.loads(cfg) if cfg else {}
            elif cfg is None:
                cfg = {}
            configs.append(cfg)
            all_config_keys.update(cfg.keys())
        
        if all_config_keys:
            config_table = Table(title="Config Comparison", show_header=True, header_style="bold yellow")
            config_table.add_column("Key", style="dim")
            for run in matched_runs:
                config_table.add_column(run["id"][:8], no_wrap=True)
            
            for key in sorted(all_config_keys):
                values = []
                base_val = None
                for i, cfg in enumerate(configs):
                    val = cfg.get(key)
                    val_str = str(val) if val is not None else "—"
                    
                    if i == 0:
                        base_val = val
                        values.append(val_str)
                    else:
                        if val != base_val:
                            values.append(f"[red]{val_str}[/red]")
                        else:
                            values.append(val_str)
                
                config_table.add_row(key, *values)
            
            console.print(config_table)
            console.print()
        
        all_summary_keys = set()
        summaries = []
        for run in matched_runs:
            summary = run.get("summary")
            if isinstance(summary, str):
                summary = json.loads(summary) if summary else {}
            elif summary is None:
                summary = {}
            filtered = {k: v for k, v in summary.items() if not k.startswith("_")}
            summaries.append(filtered)
            all_summary_keys.update(filtered.keys())
        
        if all_summary_keys:
            summary_table = Table(title="Metrics Comparison", show_header=True, header_style="bold green")
            summary_table.add_column("Metric", style="dim")
            for run in matched_runs:
                summary_table.add_column(run["id"][:8], no_wrap=True)
            
            for key in sorted(all_summary_keys):
                values = []
                for summary in summaries:
                    val = summary.get(key)
                    if isinstance(val, float):
                        values.append(f"{val:.4f}")
                    elif val is not None:
                        values.append(str(val))
                    else:
                        values.append("—")
                
                summary_table.add_row(key, *values)
            
            console.print(summary_table)
        
        cache.close()
        
    except SystemExit:
        raise
    except Exception as e:
        print_error(f"Failed to compare runs: {e}")
        raise SystemExit(1)
