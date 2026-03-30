# API Stability

## Stable (no breaking changes)

### CLI Commands (10 core)
`init-existing`, `sync`, `detect`, `doctor`, `validate`, `serve`, `harvest`, `promote`, `session`, `mcp`

Flags and output format frozen. New flags may be added but existing ones won't change.

### MCP Tools (43)
Tool names and parameter signatures frozen. New tools may be added. Return schemas may gain new fields but won't remove existing ones.

### SDK Functions (7)
`version()`, `detect()`, `health()`, `manifests()`, `codebase_map()`, `experience()`, `agent_teams()`

Function signatures frozen. Return dicts may gain new keys but won't remove existing ones.

### File Formats
- `ai/manifest/project.yaml` — stable
- `ai/manifest/discovery.json` — stable
- `ai/manifest/commands.yaml` — stable
- `ai/sessions/active.json` — stable
- `~/.0dai/auth.json` — stable

## Experimental (may change)

- Team commands (`kb`, `activity`, `role-policy`, `conflicts`, `federation`)
- Enterprise commands (`policy-push`, `compliance`)
- Internal commands (`audit`, `doc-drift`, `stack-test`, etc.)
- Billing API
- Plugin system
- Webhook system

## Versioning Policy

Starting from v1.0.0:
- **Patch** (1.0.x): bug fixes, security patches
- **Minor** (1.x.0): new features, new tools, backwards compatible
- **Major** (x.0.0): breaking changes (aim: never before v2.0)
