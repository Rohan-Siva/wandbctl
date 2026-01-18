import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile

import pytest

from wandbctl.cache import Cache
from wandbctl.api import RunMetadata


@pytest.fixture
def temp_cache():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "test_cache.duckdb"
        cache = Cache(path=cache_path)
        yield cache
        cache.close()


def make_run(
    id: str = "test-run-1",
    entity: str = "test-entity",
    project: str = "test-project",
    state: str = "finished",
    runtime: int = 3600,
    gpu_count: int = 1,
) -> RunMetadata:
    return RunMetadata(
        id=id,
        entity=entity,
        project=project,
        name=f"Run {id}",
        state=state,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        runtime_seconds=runtime,
        config={"seed": 42, "lr": 0.001},
        summary={"loss": 0.1},
        gpu_count=gpu_count,
    )


def test_cache_creation(temp_cache):
    assert temp_cache.path.exists()


def test_upsert_run(temp_cache):
    run = make_run()
    temp_cache.upsert_run(run)
    
    count = temp_cache.get_run_count()
    assert count == 1
    
    temp_cache.upsert_run(run)
    count = temp_cache.get_run_count()
    assert count == 1


def test_upsert_runs_batch(temp_cache):
    runs = [
        make_run(id="run-1"),
        make_run(id="run-2"),
        make_run(id="run-3"),
    ]
    
    count = temp_cache.upsert_runs(runs)
    assert count == 3
    assert temp_cache.get_run_count() == 3


def test_query_runs_by_entity(temp_cache):
    temp_cache.upsert_run(make_run(id="r1", entity="team-a"))
    temp_cache.upsert_run(make_run(id="r2", entity="team-b"))
    temp_cache.upsert_run(make_run(id="r3", entity="team-a"))
    
    results = temp_cache.query_runs(entity="team-a")
    assert len(results) == 2


def test_query_runs_by_state(temp_cache):
    temp_cache.upsert_run(make_run(id="r1", state="finished"))
    temp_cache.upsert_run(make_run(id="r2", state="running"))
    temp_cache.upsert_run(make_run(id="r3", state="failed"))
    
    results = temp_cache.query_runs(state="running")
    assert len(results) == 1
    assert results[0]["id"] == "r2"


def test_get_usage_stats(temp_cache):
    temp_cache.upsert_run(make_run(id="r1", state="finished", runtime=3600, gpu_count=2))
    temp_cache.upsert_run(make_run(id="r2", state="finished", runtime=7200, gpu_count=4))
    temp_cache.upsert_run(make_run(id="r3", state="failed", runtime=600, gpu_count=1))
    temp_cache.upsert_run(make_run(id="r4", state="running", runtime=1800, gpu_count=1))
    
    stats = temp_cache.get_usage_stats()
    
    assert stats["total_runs"] == 4
    assert stats["finished_runs"] == 2
    assert stats["failed_runs"] == 1
    assert stats["running_runs"] == 1
    assert stats["total_runtime_seconds"] == 3600 + 7200 + 600 + 1800
    assert stats["total_gpu_seconds"] == 3600*2 + 7200*4 + 600*1 + 1800*1


def test_sync_log(temp_cache):
    temp_cache.log_sync("my-entity", "my-project", 50)
    
    last_sync = temp_cache.get_last_sync(entity="my-entity", project="my-project")
    assert last_sync is not None
    
    temp_cache.log_sync("my-entity", "my-project", 25)
    new_sync = temp_cache.get_last_sync(entity="my-entity", project="my-project")
    assert new_sync >= last_sync


def test_get_running_runs(temp_cache):
    temp_cache.upsert_run(make_run(id="r1", state="finished"))
    temp_cache.upsert_run(make_run(id="r2", state="running"))
    temp_cache.upsert_run(make_run(id="r3", state="running"))
    
    running = temp_cache.get_running_runs()
    assert len(running) == 2
