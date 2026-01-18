"""Tests for config utilities."""

import json
import tempfile
from pathlib import Path

import pytest

from wandbctl.utils.config import load_config, hash_config, validate_config


def test_load_yaml_config():
    """Test loading YAML config."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("model: resnet50\nbatch_size: 32\nlr: 0.001\n")
        f.flush()
        
        config = load_config(f.name)
        
        assert config["model"] == "resnet50"
        assert config["batch_size"] == 32
        assert config["lr"] == 0.001


def test_load_json_config():
    """Test loading JSON config."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"model": "bert", "epochs": 10}, f)
        f.flush()
        
        config = load_config(f.name)
        
        assert config["model"] == "bert"
        assert config["epochs"] == 10


def test_load_missing_config():
    """Test loading non-existent config."""
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/config.yaml")


def test_hash_config_deterministic():
    """Test config hashing is deterministic."""
    config = {"a": 1, "b": {"c": 2}, "d": [1, 2, 3]}
    
    hash1 = hash_config(config)
    hash2 = hash_config(config)
    
    assert hash1 == hash2
    assert len(hash1) == 16


def test_hash_config_order_independent():
    """Test hash is independent of key order."""
    config1 = {"a": 1, "b": 2}
    config2 = {"b": 2, "a": 1}
    
    assert hash_config(config1) == hash_config(config2)


def test_validate_config_valid():
    """Test validating a good config."""
    config = {
        "model": "resnet50",
        "batch_size": 32,
        "lr": 0.001,
        "seed": 42,
        "epochs": 100,
    }
    
    results = validate_config(config)
    
    assert all(r["passed"] for r in results)


def test_validate_config_missing_seed():
    """Test validation catches missing seed."""
    config = {
        "model": "resnet50",
        "batch_size": 32,
    }
    
    results = validate_config(config)
    
    failed = [r for r in results if not r["passed"]]
    assert len(failed) == 1
    assert "seed" in failed[0]["message"].lower()


def test_validate_config_invalid_batch_size():
    """Test validation catches invalid batch_size."""
    config = {
        "batch_size": 0,
        "seed": 42,
    }
    
    results = validate_config(config)
    
    failed = [r for r in results if not r["passed"]]
    assert any("batch_size" in r["message"] for r in failed)


def test_validate_config_invalid_lr():
    """Test validation catches invalid learning rate."""
    config = {
        "lr": -0.001,
        "seed": 42,
    }
    
    results = validate_config(config)
    
    failed = [r for r in results if not r["passed"]]
    assert any("learning_rate" in r["message"] for r in failed)
