"""DuckDB cache layer for local storage and fast queries."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import duckdb

from wandbctl.api import RunMetadata


DEFAULT_CACHE_PATH = Path.home() / ".wandbctl" / "cache.duckdb"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS runs (
    id VARCHAR PRIMARY KEY,
    entity VARCHAR NOT NULL,
    project VARCHAR NOT NULL,
    name VARCHAR,
    state VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    runtime_seconds INTEGER,
    config JSON,
    summary JSON,
    gpu_count INTEGER,
    synced_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runs_entity_project ON runs(entity, project);
CREATE INDEX IF NOT EXISTS idx_runs_state ON runs(state);
CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at);

CREATE SEQUENCE IF NOT EXISTS sync_log_seq;

CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY DEFAULT nextval('sync_log_seq'),
    entity VARCHAR NOT NULL,
    project VARCHAR,
    synced_at TIMESTAMP NOT NULL,
    run_count INTEGER
);
"""


class Cache:
    """DuckDB-based local cache for W&B data."""
    
    def __init__(self, path: Optional[Path] = None):
        self.path = path or DEFAULT_CACHE_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = duckdb.connect(str(self.path))
        self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema."""
        for statement in SCHEMA_SQL.strip().split(";"):
            statement = statement.strip()
            if statement:
                self._conn.execute(statement)
    
    def close(self):
        """Close database connection."""
        self._conn.close()
    
    def upsert_run(self, run: RunMetadata) -> None:
        """Insert or update a run in the cache."""
        now = datetime.now(timezone.utc)
        self._conn.execute(
            """
            INSERT OR REPLACE INTO runs 
            (id, entity, project, name, state, created_at, updated_at, 
             runtime_seconds, config, summary, gpu_count, synced_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                run.id,
                run.entity,
                run.project,
                run.name,
                run.state,
                run.created_at,
                run.updated_at,
                run.runtime_seconds,
                json.dumps(run.config) if run.config else None,
                json.dumps(run.summary) if run.summary else None,
                run.gpu_count,
                now,
            ]
        )
    
    def upsert_runs(self, runs: list[RunMetadata]) -> int:
        """Batch upsert runs. Returns count."""
        count = 0
        for run in runs:
            self.upsert_run(run)
            count += 1
        return count
    
    def log_sync(
        self,
        entity: str,
        project: Optional[str],
        run_count: int,
    ) -> None:
        """Record a sync operation."""
        now = datetime.now(timezone.utc)
        self._conn.execute(
            """
            INSERT INTO sync_log (entity, project, synced_at, run_count)
            VALUES (?, ?, ?, ?)
            """,
            [entity, project, now, run_count]
        )
    
    def get_last_sync(
        self,
        entity: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Optional[datetime]:
        """Get the last sync timestamp for entity/project."""
        if entity and project:
            result = self._conn.execute(
                """
                SELECT MAX(synced_at) FROM sync_log
                WHERE entity = ? AND project = ?
                """,
                [entity, project]
            ).fetchone()
        elif entity:
            result = self._conn.execute(
                """
                SELECT MAX(synced_at) FROM sync_log
                WHERE entity = ?
                """,
                [entity]
            ).fetchone()
        else:
            result = self._conn.execute(
                "SELECT MAX(synced_at) FROM sync_log"
            ).fetchone()
        
        return result[0] if result and result[0] else None
    
    def get_run_count(
        self,
        entity: Optional[str] = None,
        project: Optional[str] = None,
    ) -> int:
        """Get count of cached runs."""
        if entity and project:
            result = self._conn.execute(
                "SELECT COUNT(*) FROM runs WHERE entity = ? AND project = ?",
                [entity, project]
            ).fetchone()
        elif entity:
            result = self._conn.execute(
                "SELECT COUNT(*) FROM runs WHERE entity = ?",
                [entity]
            ).fetchone()
        else:
            result = self._conn.execute(
                "SELECT COUNT(*) FROM runs"
            ).fetchone()
        
        return result[0] if result else 0
    
    def get_cache_size_bytes(self) -> int:
        """Get cache file size in bytes."""
        if self.path.exists():
            return self.path.stat().st_size
        return 0
    
    def query_runs(
        self,
        entity: Optional[str] = None,
        project: Optional[str] = None,
        state: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> list[dict]:
        """Query runs with filters. Returns list of dicts."""
        conditions = []
        params = []
        
        if entity:
            conditions.append("entity = ?")
            params.append(entity)
        if project:
            conditions.append("project = ?")
            params.append(project)
        if state:
            conditions.append("state = ?")
            params.append(state)
        if since:
            conditions.append("created_at >= ?")
            params.append(since)
        
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        result = self._conn.execute(
            f"""
            SELECT id, entity, project, name, state, created_at, updated_at,
                   runtime_seconds, config, summary, gpu_count, synced_at
            FROM runs
            {where}
            ORDER BY created_at DESC
            """,
            params
        ).fetchall()
        
        columns = [
            "id", "entity", "project", "name", "state", "created_at", "updated_at",
            "runtime_seconds", "config", "summary", "gpu_count", "synced_at"
        ]
        return [dict(zip(columns, row)) for row in result]

    def get_usage_stats(
        self,
        entity: Optional[str] = None,
        project: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> dict:
        """Get aggregated usage statistics."""
        conditions = []
        params = []
        
        if entity:
            conditions.append("entity = ?")
            params.append(entity)
        if project:
            conditions.append("project = ?")
            params.append(project)
        if since:
            conditions.append("created_at >= ?")
            params.append(since)
        
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        result = self._conn.execute(
            f"""
            SELECT 
                COUNT(*) as total_runs,
                SUM(CASE WHEN state = 'finished' THEN 1 ELSE 0 END) as finished_runs,
                SUM(CASE WHEN state = 'failed' THEN 1 ELSE 0 END) as failed_runs,
                SUM(CASE WHEN state = 'running' THEN 1 ELSE 0 END) as running_runs,
                SUM(CASE WHEN state = 'crashed' THEN 1 ELSE 0 END) as crashed_runs,
                SUM(COALESCE(runtime_seconds, 0)) as total_runtime_seconds,
                SUM(COALESCE(runtime_seconds, 0) * COALESCE(gpu_count, 1)) as total_gpu_seconds,
                COUNT(DISTINCT project) as project_count
            FROM runs
            {where}
            """,
            params
        ).fetchone()
        
        return {
            "total_runs": result[0] or 0,
            "finished_runs": result[1] or 0,
            "failed_runs": result[2] or 0,
            "running_runs": result[3] or 0,
            "crashed_runs": result[4] or 0,
            "total_runtime_seconds": result[5] or 0,
            "total_gpu_seconds": result[6] or 0,
            "project_count": result[7] or 0,
        }
    
    def get_running_runs(
        self,
        entity: Optional[str] = None,
        project: Optional[str] = None,
    ) -> list[dict]:
        """Get all running runs from cache."""
        return self.query_runs(entity=entity, project=project, state="running")
    
    def get_config_hash_matches(
        self,
        config_hash: str,
        entity: Optional[str] = None,
        project: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """Find runs with matching config hash (for duplicate detection)."""
        conditions = ["config IS NOT NULL"]
        params = []
        
        if entity:
            conditions.append("entity = ?")
            params.append(entity)
        if project:
            conditions.append("project = ?")
            params.append(project)
        
        where = f"WHERE {' AND '.join(conditions)}"
        
        result = self._conn.execute(
            f"""
            SELECT id, entity, project, name, state, created_at, runtime_seconds, config
            FROM runs
            {where}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            params + [limit * 10]  # Fetch more to filter
        ).fetchall()
        
        columns = ["id", "entity", "project", "name", "state", "created_at", "runtime_seconds", "config"]
        matches = []
        for row in result:
            run_dict = dict(zip(columns, row))
            if run_dict.get("config"):
                import hashlib
                run_config = run_dict["config"]
                if isinstance(run_config, str):
                    run_config = json.loads(run_config)
                run_hash = hashlib.sha256(
                    json.dumps(run_config, sort_keys=True).encode()
                ).hexdigest()[:16]
                if run_hash == config_hash:
                    matches.append(run_dict)
                    if len(matches) >= limit:
                        break
        
        return matches
