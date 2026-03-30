# zerodayai

Python SDK for the [0dai](https://github.com/0dai-dev/0dai) AI operating layer.

Read manifests, detect stacks, query experience, manage specs, and inspect agent teams — all from Python. Zero dependencies (pure stdlib).

## Install

```bash
pip install zerodayai
```

## Quick Start

```python
import zerodayai

# Check AI layer health
h = zerodayai.health("/path/to/project")
print(h["version"], h["stack"])

# Detect project stack
d = zerodayai.detect("/path/to/project")
print(d["stack"])  # "fastapi", "nextjs", etc.

# Read all manifests
m = zerodayai.manifests("/path/to/project")

# Search experience knowledge base
results = zerodayai.experience("/path/to/project", query="bugfix")

# List development specs
s = zerodayai.specs("/path/to/project", status="ready")

# Inspect agent teams
teams = zerodayai.agent_teams("/path/to/project")
```

## API

| Function | Description |
|----------|-------------|
| `version(target)` | Get AI layer version |
| `detect(target)` | Get detected stack from discovery.json |
| `health(target)` | Comprehensive health check |
| `manifests(target)` | All manifest data in one call |
| `codebase_map(target)` | Structural map (entry points, deps, roles) |
| `experience(target, query)` | Search or summarize knowledge base |
| `specs(target, status)` | List development specifications |
| `agent_teams(target)` | Installed agents and personas |

All functions accept an optional `target` path (defaults to `"."`).

## Requirements

- Python 3.10+
- No external dependencies

## License

Apache-2.0
