"""Tests for zombie detection logic."""

from datetime import datetime, timezone, timedelta

import pytest

from wandbctl.commands.zombies import classify_zombie


def make_running_run(
    id: str = "test-run",
    runtime: int = 3600,
    minutes_since_update: int = 5,
) -> dict:
    """Create a running run dict for testing."""
    now = datetime.now(timezone.utc)
    updated_at = now - timedelta(minutes=minutes_since_update)
    
    return {
        "id": id,
        "entity": "test-entity",
        "project": "test-project",
        "name": f"Run {id}",
        "state": "running",
        "runtime_seconds": runtime,
        "updated_at": updated_at,
    }


def test_not_zombie_recent_update():
    """Test run with recent update is not zombie."""
    run = make_running_run(minutes_since_update=5)
    result = classify_zombie(run, threshold_minutes=15, avg_runtime=None)
    assert result is None


def test_zombie_medium_confidence():
    """Test run with threshold exceeded is medium zombie."""
    run = make_running_run(minutes_since_update=20)
    result = classify_zombie(run, threshold_minutes=15, avg_runtime=None)
    
    assert result is not None
    assert result["confidence"] == "medium"


def test_zombie_high_confidence_long_stall():
    """Test run with 2x threshold exceeded is high zombie."""
    run = make_running_run(minutes_since_update=35)
    result = classify_zombie(run, threshold_minutes=15, avg_runtime=None)
    
    assert result is not None
    assert result["confidence"] == "high"


def test_zombie_high_confidence_runtime():
    """Test run with 3x average runtime is high zombie."""
    run = make_running_run(runtime=10800, minutes_since_update=20)  # 3 hours
    avg_runtime = 3000  # ~50 min average
    result = classify_zombie(run, threshold_minutes=15, avg_runtime=avg_runtime)
    
    assert result is not None
    assert result["confidence"] == "high"


def test_zombie_preserves_run_info():
    """Test zombie result includes run info."""
    run = make_running_run(id="my-run-123", minutes_since_update=20)
    result = classify_zombie(run, threshold_minutes=15, avg_runtime=None)
    
    assert result["id"] == "my-run-123"
    assert result["project"] == "test-project"
    assert result["entity"] == "test-entity"


def test_no_zombie_without_updated_at():
    """Test run without updated_at is not classified."""
    run = {
        "id": "test",
        "entity": "e",
        "project": "p",
        "state": "running",
        "runtime_seconds": 3600,
        "updated_at": None,
    }
    result = classify_zombie(run, threshold_minutes=15, avg_runtime=None)
    assert result is None
