# Architecture

## Operating Model

This repository is the upstream source of truth for a portable AI operating layer.

It supports two execution modes:

1. `init-new`: scaffold a new product repository and install the AI layer.
2. `init-existing`: install the AI layer into an existing repository without destructive changes.

## Design Layers

ZeroDayAI now treats `ai/` as the canonical generation layer and emits native tool files beside it.

### 1. Bootstrap Layer

Located in `bootstrap/`.

- Detects stack and installed tools.
- Installs or syncs `ai/`.
- Generates root config files for selected agent CLIs.
- Generates hook scripts, MCP defaults, and CI validation.
- Preserves unmanaged local customization by writing `*.generated` files instead of overwriting.

### 2. Template Layer

Located in `templates/`.

- `templates/layer/ai/` mirrors the canonical project-local `ai/` directory.
- `templates/root/` is reduced to temporary compatibility artifacts that have not yet moved into canonical sources.
- `bootstrap/native_output_map.json` defines how canonical template sources map to native emitted files.

Inside the canonical layer, `ai/templates/` is now the preferred source of truth for native file generation, while upstream `templates/root/` is intentionally reduced to a minimal compatibility bridge.

### 3. Stack Layout Layer

Located in `project_layouts/`.

- Holds opinionated project structures for greenfield repositories.
- Each stack exposes `scaffold.sh` and `structure.md`.

### 4. Runtime Layer

Located in `docker/` and `.devcontainer/`.

- Provides a reproducible workspace container around the canonical AI layer.
- Keeps project-scoped files in the repository and user-level state in volumes.
- Supports optional sidecars for telemetry and future MCP or knowledge services.
- Supports an isolated no-network runner profile and optional OpenCode web mode.

## Installation Contract In Target Projects

Generated projects follow this baseline:

```text
repo/
  ai/
    VERSION
    VERSION_SCHEMA
    bootstrap/
    docs/
    experience/
    manifest/
    channels/
    packs/
    migrations/
    templates/
    patterns/
    playbooks/
    prompts/
  AGENTS.md
  .codex/config.toml
  .agents/skills/
  .claude/settings.json
  .claude/CLAUDE.md
  .claude/rules/
  .claude/skills/
  .claude/agents/
  .claude/hooks/
  .mcp.json
  opencode.json
  .opencode/agents/
  .github/workflows/ai-layer-check.yml
```

## Sync Contract

- Files carrying `managed: true` may be overwritten during sync.
- Files without the marker are treated as user-owned and preserved.
- If a user-owned file collides with a template update, the new candidate is written as `*.generated`.

## Why This Works Across Agents

- Shared repository knowledge lives once inside `ai/`.
- Native tool files are emitted from that canonical layer into the paths each CLI scans.
- Codex and OpenCode share `AGENTS.md`; Claude gets its own compact `.claude/CLAUDE.md` and rule files.
- Hooks, agents, and skills remain tool-specific outputs generated from one project manifest.
- Existing instruction entrypoints should be merged via managed blocks rather than blindly overwritten.
- Instructions, skills, and operational experience should evolve as separate but connected knowledge systems.
