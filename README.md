```
                         _  _          _   _ 
 __      ____ _ _ __   __| || |__   ___| |_| |
 \ \ /\ / / _` | '_ \ / _` || '_ \ / __| __| |
  \ V  V / (_| | | | | (_| || |_) | (__| |_| |
   \_/\_/ \__,_|_| |_|\__,_||_.__/ \___|\__|_|
                                              
        Surface waste. Prevent failures. Save compute.
```

# wandbctl

> A blazing fast CLI for monitoring, auditing, and analyzing your Weights & Biases usage.  
> **Stop burning GPU hours. Start knowing where they go.**

---

## Features

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   USAGE            Track runs, runtime, GPU-hours at a glance  │
│   ─────────────────────────────────────────────────────────────│
│   ZOMBIES          Detect stalled runs before they eat your    │
│                    compute budget                               │
│   ─────────────────────────────────────────────────────────────│
│   PREFLIGHT        Validate configs & catch duplicates         │
│                    before launch                                │
│   ─────────────────────────────────────────────────────────────│
│   LOCAL CACHE      DuckDB-powered queries. Works offline.      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# Install
pip install -e .

# Set your API key
export WANDB_API_KEY=your_key_here

# Sync your runs to local cache
wandbctl sync --entity my-team --project my-project

# See where your compute is going
wandbctl usage --last 7d

# Hunt for zombie runs
wandbctl zombies

# Preflight check before training
wandbctl preflight config.yaml
```

---

## Commands

### `sync` - Pull runs into local cache
```bash
wandbctl sync                              # Sync all
wandbctl sync --entity my-team             # Specific entity
wandbctl sync --since 2024-01-01           # Only recent runs
```

### `status` - Show cache state
```bash
wandbctl status
```
```
       Cache Status        
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
│ Property     │ Value      │
├──────────────┼────────────┤
│ Cache size   │ 2.1 MB     │
│ Cached runs  │ 1,247      │
│ Last sync    │ 5m ago     │
└──────────────┴────────────┘
```

### `usage` - Track where compute goes
```bash
wandbctl usage                  # All time
wandbctl usage --last 24h       # Last 24 hours
wandbctl usage --last 7d        # Last week
wandbctl usage --refresh        # Force sync first
```
```
       Usage Summary       
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
│ Metric        │ Value    │
├───────────────┼──────────┤
│ Total runs    │ 247      │
│   Finished    │ 198      │
│   Running     │ 12       │
│   Failed      │ 37       │
├───────────────┼──────────┤
│ Total runtime │ 847h 23m │
│ Est. GPU-hrs  │ 2,541.2h │
└───────────────┴──────────┘
```

### `zombies` - Find stalled runs

```
  ZOMBIE DETECTION
  
  Active runs that stopped logging
  but never finished. They're eating
  your GPU hours right now.
```

```bash
wandbctl zombies                    # Default 15min threshold
wandbctl zombies --threshold 30     # Custom threshold
wandbctl zombies --project my-proj  # Filter by project
```

**Confidence Levels:**
- 🔴 **HIGH** - No updates for 30+ min, or runtime 3x average
- 🟡 **MEDIUM** - No updates for 15+ min

### `preflight` - Pre-launch validation

```
  PREFLIGHT CHECKS
  
  Gate your CI/training scripts.
  Catch problems before burning compute.
```

```bash
wandbctl preflight config.yaml              # Check config
wandbctl preflight config.yaml --warn-only  # Don't block
wandbctl preflight config.yaml --force      # Skip all checks
```

**Checks performed:**
1. Config sanity (required fields, valid values)
2. Duplicate detection (identical config ran recently?)
3. Failure patterns (similar configs crashed?)

**CI Integration:**
```bash
#!/bin/bash
wandbctl preflight config.yaml || exit 1
python train.py
```

---

## Data Freshness

| Command | Source | Speed |
|---------|--------|-------|
| `usage` | Cache | Instant |
| `status` | Cache | Instant |
| `zombies` | Live | Fast |
| `preflight` | Cache + config | Instant |

> Use `--refresh` to force sync on cache-first commands.

---

## Configuration

**Cache:** `~/.wandbctl/cache.duckdb`

**Authentication:** Uses standard W&B methods:
- `WANDB_API_KEY` environment variable
- `~/.netrc` file

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_zombies.py -v
```

---

## License

MIT

---

```
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║      Made for ML engineers who hate waste             ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
```
