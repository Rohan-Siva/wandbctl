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
│   15 Commands for Complete W&B Visibility                       │
│                                                                 │
│   CORE            sync, status, usage, zombies, preflight       │
│   ANALYTICS       trends, costs, failures, top                  │
│   MANAGEMENT      compare, export, projects, clean, summary     │
│   DIAGNOSTIC      health                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
pip install -e .
export WANDB_API_KEY=your_key_here

wandbctl sync --entity my-team
wandbctl usage --last 7d
wandbctl zombies
```

---

## Commands Reference

### Core Commands

| Command | Description |
|---------|-------------|
| `sync` | Pull runs from W&B into local cache |
| `status` | Show cache state and freshness |
| `usage` | Track runs, runtime, GPU-hours |
| `zombies` | Detect stalled runs eating compute |
| `preflight` | Validate configs before launch |

### Analytics Commands (v2)

| Command | Description |
|---------|-------------|
| `trends` | ASCII sparkline charts of activity over time |
| `costs` | Estimate GPU costs by project |
| `top` | Leaderboard of runs by runtime/GPU-hours |
| `compare` | Side-by-side run config/metrics comparison |
| `export` | Export cached runs to JSON |

### Management Commands (v3)

| Command | Description |
|---------|-------------|
| `projects` | List all projects with stats |
| `failures` | Analyze failure patterns and categories |
| `clean` | Purge old runs from cache |
| `summary` | Quick one-liner usage stats |
| `health` | Check W&B auth and cache health |

---

## Detailed Usage

### `sync` - Pull runs into local cache
```bash
wandbctl sync                              # Sync all
wandbctl sync --entity my-team             # Specific entity
wandbctl sync --since 2024-01-01           # Only recent runs
```

### `usage` - Track where compute goes
```bash
wandbctl usage                  # All time
wandbctl usage --last 24h       # Last 24 hours
wandbctl usage --refresh        # Force sync first
```

### `zombies` - Find stalled runs

**Confidence Levels:**
- 🔴 **HIGH** - No updates for 30+ min, or runtime 3x average
- 🟡 **MEDIUM** - No updates for 15+ min

```bash
wandbctl zombies                    # Default 15min threshold
wandbctl zombies --threshold 30     # Custom threshold
```

### `preflight` - Pre-launch validation
```bash
wandbctl preflight config.yaml              # Check config
wandbctl preflight config.yaml --warn-only  # Don't block
wandbctl preflight config.yaml --force      # Skip all checks
```

### `trends` - Activity over time
```bash
wandbctl trends --last 30d        # Last 30 days
wandbctl trends --group week      # Group by week
```

Output:
```
Runs:      ▁▂▃▄▅▆▇█▅▃  (247 total)
Runtime:   ▁▁▂▃▅█▇▅▃▂  (847h total)
```

### `costs` - GPU cost estimation
```bash
wandbctl costs                    # Default $2.50/GPU-hr
wandbctl costs --rate 3.10        # Custom rate
wandbctl costs --last 7d          # Recent only
```

### `top` - Run leaderboard
```bash
wandbctl top                      # Top 10 by runtime
wandbctl top --by gpu-hours -n 20 # Top 20 by GPU-hours
wandbctl top --state failed       # Top failed runs
```

### `compare` - Run comparison
```bash
wandbctl compare abc123 def456 ghi789
```

### `export` - JSON export
```bash
wandbctl export -o runs.json      # Export to file
wandbctl export --last 7d --pretty # Pretty print recent
```

### `projects` - Project overview
```bash
wandbctl projects                 # All projects
wandbctl projects --entity team   # Specific entity
```

### `failures` - Failure analysis
```bash
wandbctl failures                 # Analyze all failures
wandbctl failures --last 7d       # Recent failures only
```

### `clean` - Cache cleanup
```bash
wandbctl clean --older-than 90    # Delete runs >90 days old
wandbctl clean --dry-run          # Preview what would delete
```

### `summary` - One-liner stats
```bash
wandbctl summary
# 247 runs | 198 ok | 37 fail | 12 running | 847h runtime | 2541 GPU-hrs | 80% success
```

### `health` - System health check
```bash
wandbctl health
```

---

## Data Freshness

| Command | Source | Speed |
|---------|--------|-------|
| `usage`, `status`, `trends`, `costs`, `top`, `export`, `projects`, `failures`, `summary` | Cache | Instant |
| `zombies` | Live | Fast |
| `preflight` | Cache + config | Instant |

---

## Configuration

**Cache:** `~/.wandbctl/cache.duckdb`

**Authentication:**
- `WANDB_API_KEY` environment variable
- `~/.netrc` file

---

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

---

## License

MIT

---

```
    ╔═══════════════════════════════════════════════════════╗
    ║      Made for ML engineers who hate waste             ║
    ╚═══════════════════════════════════════════════════════╝
```
