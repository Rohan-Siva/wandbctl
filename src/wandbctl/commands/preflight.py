"""Preflight check command for config validation."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import click

from wandbctl.api import WandbClient
from wandbctl.cache import Cache
from wandbctl.utils.config import load_config, hash_config, validate_config
from wandbctl.utils.display import (
    console,
    print_error,
    print_info,
    print_warning,
    print_success,
    print_preflight_result,
)


@click.command()
@click.argument("config_path", type=click.Path(exists=True))
@click.option("--entity", "-e", help="W&B entity for duplicate check")
@click.option("--project", "-p", help="W&B project for duplicate check")
@click.option("--warn-only", is_flag=True, help="Warn but don't fail on issues")
@click.option("--force", is_flag=True, help="Skip all checks and exit 0")
def preflight(
    config_path: str,
    entity: str | None,
    project: str | None,
    warn_only: bool,
    force: bool,
):
    """Validate a config file before launching a training run.
    
    Performs pre-launch checks to prevent waste:
    
    \b
    1. Config sanity - Required fields, valid values
    2. Duplicate detection - Warn if identical config ran recently
    3. Failure correlation - Warn if similar configs crashed
    
    Exit codes:
    
    \b
    - 0: Safe to launch
    - 1: Issues detected (blocked)
    
    Examples:
    
        wandbctl preflight config.yaml
        
        wandbctl preflight config.yaml --entity my-team --project my-project
        
        wandbctl preflight config.yaml --warn-only
        
        wandbctl preflight config.yaml --force
    """
    if force:
        print_info("Force mode: skipping all checks")
        print_success("Preflight passed (forced)")
        sys.exit(0)
    
    try:
        config = load_config(config_path)
    except FileNotFoundError as e:
        print_error(str(e))
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to parse config: {e}")
        sys.exit(1)
    
    print_info(f"Checking config: {config_path}")
    console.print()
    
    all_checks = []
    has_errors = False
    
    sanity_results = validate_config(config)
    for result in sanity_results:
        all_checks.append(result)
        if not result["passed"]:
            severity = result.get("severity", "error")
            if severity == "error":
                has_errors = True
                print_error(result["message"])
            else:
                print_warning(result["message"])
        else:
            print_success(result["message"])
    
    config_hash = hash_config(config)
    print_info(f"Config hash: {config_hash}")
    
    try:
        cache = Cache()
        run_count = cache.get_run_count(entity=entity, project=project)
        
        if run_count > 0:
            console.print()
            print_info("Checking for duplicate runs...")
            
            matches = cache.get_config_hash_matches(
                config_hash=config_hash,
                entity=entity,
                project=project,
                limit=5,
            )
            
            if matches:
                recent_24h = []
                now = datetime.now(timezone.utc)
                for m in matches:
                    created = m.get("created_at")
                    if created:
                        if created.tzinfo is None:
                            created = created.replace(tzinfo=timezone.utc)
                        if (now - created) < timedelta(hours=24):
                            recent_24h.append(m)
                
                if recent_24h:
                    failed_count = sum(1 for m in recent_24h if m.get("state") in ("failed", "crashed"))
                    msg = f"Identical config ran {len(recent_24h)} time(s) in last 24h"
                    if failed_count > 0:
                        msg += f" ({failed_count} failed)"
                        has_errors = True
                        all_checks.append({"passed": False, "message": msg, "severity": "error"})
                        print_error(msg)
                    else:
                        all_checks.append({"passed": False, "message": msg, "severity": "warning"})
                        print_warning(msg)
                else:
                    all_checks.append({"passed": True, "message": "No recent duplicate configs found"})
                    print_success("No recent duplicate configs found")
            else:
                all_checks.append({"passed": True, "message": "No matching configs in history"})
                print_success("No matching configs in history")
            
            console.print()
            print_info("Checking for failure patterns...")
            
            runs = cache.query_runs(entity=entity, project=project)
            recent_failures = [
                r for r in runs
                if r.get("state") in ("failed", "crashed")
                and r.get("runtime_seconds") is not None
                and r.get("runtime_seconds") < 300  # Failed in < 5 min
            ]
            
            if len(recent_failures) > 5:
                msg = f"{len(recent_failures)} runs failed within 5 minutes (early crash pattern)"
                all_checks.append({"passed": False, "message": msg, "severity": "warning"})
                print_warning(msg)
            else:
                all_checks.append({"passed": True, "message": "No concerning failure patterns"})
                print_success("No concerning failure patterns")
        
        cache.close()
        
    except Exception as e:
        print_warning(f"Could not check cache: {e}")
    
    console.print()
    
    if has_errors and not warn_only:
        print_preflight_result(False, all_checks)
        sys.exit(1)
    else:
        print_preflight_result(True, all_checks)
        sys.exit(0)
