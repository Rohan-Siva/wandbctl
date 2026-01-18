# wandbctl

A local command-line tool for monitoring, auditing, and analyzing Weights & Biases usage.

**Surface waste and prevent failures before they burn compute.**

## Features

- **Usage reporting**: Summarize runs, runtime, GPU-hours across projects
- **Zombie detection**: Find runs that are active but not making progress
- **Preflight checks**: Validate configs before launch, detect duplicates
- **Local caching**: Fast queries with DuckDB, works offline

## Installation

```bash
# From source
pip install -e .

# Or with pip (once published)
pip install wandbctl
```

## Quick Start

```bash
# Set your W&B API key
export WANDB_API_KEY=your_key_here

# Sync runs to local cache
wandbctl sync --entity my-team --project my-project

# Check cache status
wandbctl status

# View usage summary
wandbctl usage
wandbctl usage --last 24h

# Detect zombie runs
wandbctl zombies

# Preflight check before training
wandbctl preflight config.yaml
```

## Commands

### `wandbctl sync`

Pull runs from W&B into local cache.

```bash
wandbctl sync                              # Sync all projects
wandbctl sync --entity my-team             # Sync specific entity
wandbctl sync --project my-project         # Sync specific project
wandbctl sync --since 2024-01-01           # Sync runs after date
```

### `wandbctl status`

Show cache state and freshness.

```bash
wandbctl status
```

### `wandbctl usage`

Display usage statistics from cached data.

```bash
wandbctl usage                             # All cached runs
wandbctl usage --last 24h                  # Last 24 hours
wandbctl usage --last 7d                   # Last 7 days
wandbctl usage --entity my-team            # Filter by entity
wandbctl usage --refresh                   # Force sync first
```

### `wandbctl zombies`

Detect stalled runs (active but not logging).

```bash
wandbctl zombies                           # Use default 15min threshold
wandbctl zombies --threshold 30            # Custom threshold
wandbctl zombies --project my-project      # Filter by project
```

Zombie classification:
- **HIGH confidence**: No updates for 30+ minutes, or runtime 3× average
- **MEDIUM confidence**: No updates for 15+ minutes

### `wandbctl preflight`

Validate config before launching a training run.

```bash
wandbctl preflight config.yaml             # Check config
wandbctl preflight config.yaml --warn-only # Warn but don't fail
wandbctl preflight config.yaml --force     # Skip all checks
```

Checks performed:
1. **Config sanity**: Required fields, valid values
2. **Duplicate detection**: Warn if identical config ran recently
3. **Failure patterns**: Warn if similar configs crashed

CI integration:
```bash
wandbctl preflight config.yaml || exit 1
python train.py
```

## Data Freshness

Commands use a hybrid freshness model:

| Command | Data Source | Behavior |
|---------|-------------|----------|
| `usage` | Cache | Fast, shows cache age |
| `status` | Cache | Shows cache state |
| `zombies` | Live | Always fetches running runs |
| `preflight` | Cache + config | Uses cached history |

Use `--refresh` flag to force sync on cache-first commands.

## Configuration

Cache location: `~/.wandbctl/cache.duckdb`

Authentication uses standard W&B methods:
- `WANDB_API_KEY` environment variable
- `~/.netrc` file

## License

MIT
