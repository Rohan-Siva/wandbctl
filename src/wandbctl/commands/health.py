import click

from wandbctl.cache import Cache
from wandbctl.utils.display import (
    console,
    print_error,
    print_success,
    print_warning,
    format_bytes,
    format_time_ago,
)


@click.command()
def health():
    try:
        checks = []
        
        console.print("\n[bold]Health Check[/bold]\n")
        
        try:
            import wandb
            api = wandb.Api()
            entity = api.default_entity
            if entity:
                checks.append(("W&B Auth", True, f"Connected as {entity}"))
            else:
                checks.append(("W&B Auth", False, "No default entity found"))
        except Exception as e:
            checks.append(("W&B Auth", False, str(e)))
        
        try:
            cache = Cache()
            run_count = cache.get_run_count()
            cache_size = cache.get_cache_size_bytes()
            last_sync = cache.get_last_sync()
            
            checks.append(("Cache", True, f"{run_count} runs, {format_bytes(cache_size)}"))
            
            if last_sync:
                checks.append(("Last Sync", True, format_time_ago(last_sync)))
            else:
                checks.append(("Last Sync", False, "Never synced"))
            
            cache.close()
        except Exception as e:
            checks.append(("Cache", False, str(e)))
        
        try:
            import duckdb
            checks.append(("DuckDB", True, f"v{duckdb.__version__}"))
        except Exception as e:
            checks.append(("DuckDB", False, str(e)))
        
        all_passed = True
        for name, passed, msg in checks:
            if passed:
                print_success(f"{name}: {msg}")
            else:
                print_warning(f"{name}: {msg}")
                all_passed = False
        
        console.print()
        
        if all_passed:
            print_success("All checks passed")
        else:
            print_warning("Some checks failed")
        
    except Exception as e:
        print_error(f"Health check failed: {e}")
        raise SystemExit(1)
