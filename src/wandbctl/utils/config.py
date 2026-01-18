"""Configuration parsing utilities."""

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML or JSON config file."""
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    content = path.read_text()
    
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(content) or {}
    elif path.suffix == ".json":
        return json.loads(content)
    else:
        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError:
            return json.loads(content)


def hash_config(config: dict) -> str:
    """Create a stable hash of a config dict."""
    normalized = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def validate_config(config: dict) -> list[dict]:
    """
    Validate a config for common issues.
    Returns list of {"passed": bool, "message": str, "severity": str}
    """
    issues = []
    
    if "batch_size" in config:
        bs = config["batch_size"]
        if isinstance(bs, (int, float)) and bs <= 0:
            issues.append({
                "passed": False,
                "message": f"batch_size must be positive (got {bs})",
                "severity": "error"
            })
    
    if "lr" in config or "learning_rate" in config:
        lr = config.get("lr") or config.get("learning_rate")
        if isinstance(lr, (int, float)) and lr <= 0:
            issues.append({
                "passed": False,
                "message": f"learning_rate must be positive (got {lr})",
                "severity": "error"
            })
    
    if "seed" not in config and "random_seed" not in config:
        issues.append({
            "passed": False,
            "message": "No random seed specified (reproducibility risk)",
            "severity": "warning"
        })
    
    if "epochs" in config:
        epochs = config["epochs"]
        if isinstance(epochs, (int, float)) and epochs <= 0:
            issues.append({
                "passed": False,
                "message": f"epochs must be positive (got {epochs})",
                "severity": "error"
            })
    
    if not issues:
        issues.append({
            "passed": True,
            "message": "Config sanity checks passed",
            "severity": "info"
        })
    
    return issues
