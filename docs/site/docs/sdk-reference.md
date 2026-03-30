# Python SDK Reference

The 0dai Python SDK provides programmatic access to all 0dai data from Python scripts, notebooks, and automation pipelines.

## Installation

The SDK is distributed with the 0dai repository. Install it from the `sdk/` directory:

```bash
cd sdk/
pip install .
```

To install in development mode (editable install):

```bash
pip install -e .
```

**Requirements:** Python 3.9 or later.

---

## Import

```python
import zerodayai
```

All functions are available directly on the `zerodayai` module. No client instantiation is required.

---

## Functions

### `zerodayai.version(target)`

Returns version information for the 0dai installation at `target`.

**Parameters:**

- `target` (`str`) — path to the project root

**Returns:** `dict` with keys `cli_version`, `manifest_version`, `protocol_version`

```python
import zerodayai

info = zerodayai.version("/path/to/project")
print(info["cli_version"])
# "0.7.5"
```

---

### `zerodayai.detect(target)`

Returns the detected technology stack for the project at `target`.

**Parameters:**

- `target` (`str`) — path to the project root

**Returns:** `dict` with keys `languages`, `frameworks`, `tooling`, `confidence`

```python
stack = zerodayai.detect("/path/to/project")
print(stack["languages"])
# ["TypeScript", "Python"]
print(stack["frameworks"])
# ["Next.js", "FastAPI"]
```

---

### `zerodayai.health(target)`

Returns a comprehensive health check for the project at `target`.

**Parameters:**

- `target` (`str`) — path to the project root

**Returns:** `dict` with keys `score` (0–100), `issues` (list), `warnings` (list), `passing` (list)

```python
health = zerodayai.health("/path/to/project")
print(health["score"])
# 87

for issue in health["issues"]:
    print(f"[issue] {issue}")
```

---

### `zerodayai.manifests(target)`

Returns the full manifest data for the project at `target`.

**Parameters:**

- `target` (`str`) — path to the project root

**Returns:** `dict` — the parsed contents of `ai/manifest.json`

```python
manifest = zerodayai.manifests("/path/to/project")
print(manifest["project"]["name"])
# "my-project"
print(manifest["stack"]["primary_language"])
# "TypeScript"
```

---

### `zerodayai.codebase_map(target)`

Returns a structural map of the codebase at `target`.

**Parameters:**

- `target` (`str`) — path to the project root

**Returns:** `dict` with keys `directories`, `entry_points`, `key_files`, `relationships`

```python
cmap = zerodayai.codebase_map("/path/to/project")

for entry in cmap["entry_points"]:
    print(entry)
# "src/index.ts"
# "api/main.py"
```

---

### `zerodayai.experience(target, query)`

Searches the harvested knowledge base at `target` for entries relevant to `query`. Returns a summarized view of matching experience entries.

**Parameters:**

- `target` (`str`) — path to the project root
- `query` (`str`) — natural language search query

**Returns:** `dict` with keys `results` (list of matching entries), `summary` (string), `total` (int)

```python
result = zerodayai.experience(
    "/path/to/project",
    "how do we handle database migrations"
)

print(result["summary"])
# "The team uses Alembic for migrations, triggered via `make migrate`..."

for entry in result["results"]:
    print(entry["title"], entry["date"])
```

---

### `zerodayai.agent_teams(target)`

Returns all agent team definitions installed in the project at `target`.

**Parameters:**

- `target` (`str`) — path to the project root

**Returns:** `list` of `dict`, each with keys `name`, `members`, `responsibilities`, `entry_point`

```python
teams = zerodayai.agent_teams("/path/to/project")

for team in teams:
    print(team["name"])
    for member in team["members"]:
        print(f"  - {member['role']}: {member['agent']}")
```

---

## Error Handling

All functions raise `zerodayai.ZeroDayAIError` on failure. The exception includes a `code` attribute corresponding to the MCP error codes documented in the [MCP Reference](mcp-reference.md).

```python
import zerodayai

try:
    health = zerodayai.health("/path/to/project")
except zerodayai.ZeroDayAIError as e:
    print(f"Error {e.code}: {e}")
```

Common error codes:

| Code | Cause |
|---|---|
| `NOT_FOUND` | The target path does not contain a valid 0dai project. |
| `AUTH_REQUIRED` | The operation requires authentication. Run `0dai auth login`. |
| `SCHEMA_ERROR` | The manifest at `target` is malformed. Run `0dai validate` to diagnose. |

---

## Using the SDK in CI

A common pattern is to run health checks and fail the build if the score drops below a threshold:

```python
import sys
import zerodayai

health = zerodayai.health(".")
score = health["score"]

print(f"0dai health score: {score}/100")

if health["issues"]:
    for issue in health["issues"]:
        print(f"  [issue] {issue}")

if score < 70:
    print("Health score below threshold. Failing build.")
    sys.exit(1)
```
