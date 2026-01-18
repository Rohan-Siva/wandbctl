"""W&B API client wrapper for read-only access."""

from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, Optional
import wandb


@dataclass
class RunMetadata:
    """Metadata for a W&B run."""
    id: str
    entity: str
    project: str
    name: str
    state: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    runtime_seconds: Optional[int]
    config: dict
    summary: dict
    gpu_count: Optional[int]
    
    @classmethod
    def from_api_run(cls, run: wandb.apis.public.Run) -> "RunMetadata":
        """Create RunMetadata from a W&B API run object."""
        config = dict(run.config) if run.config else {}
        summary = dict(run.summary) if run.summary else {}
        
        gpu_count = None
        if "_wandb" in summary and "gpu_count" in summary["_wandb"]:
            gpu_count = summary["_wandb"]["gpu_count"]
        elif "gpu_count" in config:
            gpu_count = config.get("gpu_count")
        
        runtime = None
        if hasattr(run, "runtime") and run.runtime is not None:
            runtime = int(run.runtime)
        elif "_runtime" in summary:
            runtime = int(summary["_runtime"])
        
        created = None
        if hasattr(run, "created_at") and run.created_at:
            if isinstance(run.created_at, str):
                try:
                    created = datetime.fromisoformat(run.created_at.replace("Z", "+00:00"))
                except ValueError:
                    pass
            elif isinstance(run.created_at, datetime):
                created = run.created_at
        
        updated = None
        if hasattr(run, "updated_at") and run.updated_at:
            if isinstance(run.updated_at, str):
                try:
                    updated = datetime.fromisoformat(run.updated_at.replace("Z", "+00:00"))
                except ValueError:
                    pass
            elif isinstance(run.updated_at, datetime):
                updated = run.updated_at
        
        return cls(
            id=run.id,
            entity=run.entity,
            project=run.project,
            name=run.name or run.id,
            state=run.state,
            created_at=created,
            updated_at=updated,
            runtime_seconds=runtime,
            config=config,
            summary=summary,
            gpu_count=gpu_count,
        )


class WandbClient:
    """Client for interacting with W&B Public API."""
    
    def __init__(self):
        self._api = wandb.Api()
    
    @property
    def default_entity(self) -> Optional[str]:
        """Get the default entity for the authenticated user."""
        try:
            return self._api.default_entity
        except Exception:
            return None
    
    def list_projects(self, entity: Optional[str] = None) -> list[str]:
        """List all projects for an entity."""
        entity = entity or self.default_entity
        if not entity:
            raise ValueError("No entity specified and no default entity found")
        
        projects = self._api.projects(entity=entity)
        return [p.name for p in projects]
    
    def list_runs(
        self,
        entity: Optional[str] = None,
        project: Optional[str] = None,
        filters: Optional[dict] = None,
        order: str = "-created_at",
        per_page: int = 100,
    ) -> Iterator[RunMetadata]:
        """List runs with optional filters."""
        entity = entity or self.default_entity
        if not entity:
            raise ValueError("No entity specified and no default entity found")
        
        path = f"{entity}/{project}" if project else entity
        
        try:
            runs = self._api.runs(
                path=path,
                filters=filters or {},
                order=order,
                per_page=per_page,
            )
            for run in runs:
                try:
                    yield RunMetadata.from_api_run(run)
                except Exception:
                    continue
        except wandb.CommError as e:
            raise ConnectionError(f"Failed to fetch runs: {e}")
    
    def get_run(self, entity: str, project: str, run_id: str) -> RunMetadata:
        """Get a specific run by ID."""
        path = f"{entity}/{project}/{run_id}"
        run = self._api.run(path)
        return RunMetadata.from_api_run(run)
    
    def list_running_runs(
        self,
        entity: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Iterator[RunMetadata]:
        """List only currently running runs (fresh fetch)."""
        filters = {"state": "running"}
        return self.list_runs(entity=entity, project=project, filters=filters)
