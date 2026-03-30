# Getting Started

**Five agents. One config. Zero friction.**

0dai generates native configs for Claude Code, Codex, OpenCode, Gemini, and Aider from a single `ai/` directory.

## Quick Start (5 minutes)

### 1. Install into your project

```bash
git clone https://github.com/0dai-dev/0dai
cd 0dai
./bin/0dai init-existing --target /path/to/your/project
```

This auto-detects your stack (FastAPI, Next.js, Flutter, Go, Python, etc.) and generates:

- `ai/` — your source of truth (manifests, personas, playbooks, experience)
- `.claude/settings.json` + `.claude/agents/` — Claude Code config
- `.codex/config.toml` + `.codex/agents/` — Codex config
- `.gemini/settings.json` + `.gemini/agents/` — Gemini config
- `opencode.json` + `.opencode/agents/` — OpenCode config
- `.aider.conf.yml` + `.aider/agents/` — Aider config
- `AGENTS.md` — shared agent instructions

### 2. Verify

```bash
./bin/0dai doctor --target /path/to/your/project
```

Shows detected stack, available CLIs, command tiers, and maturity score.

### 3. Keep in sync

After editing files in `ai/`, regenerate all agent configs:

```bash
./bin/0dai sync --target /path/to/your/project
```

## What's Next

- [Session Roaming](session-roaming.md) — transfer context between agents
- [Migration Guide](migration.md) — move from manual CLAUDE.md to 0dai
- [CLI Reference](cli-reference.md) — all available commands
- [MCP Tools](mcp-reference.md) — 43 tools for agent self-service

## Three Things That Make 0dai Different

### 1. Five agents, one config
Write project knowledge once in `ai/`. Every agent CLI reads it natively. No more duplicating CLAUDE.md, AGENTS.md, and opencode.json separately.

### 2. Session Roaming
Start a task in Claude Code, continue in Codex, finish in Gemini. Session context transfers seamlessly via `ai/sessions/active.json`.

### 3. Experience Flywheel
Capture what worked and what didn't. Harvest patterns, promote them into team knowledge. Your agents get smarter with every sprint.
