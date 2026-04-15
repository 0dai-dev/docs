# Config File Reference

0dai reads and generates config files for each supported agent. This page documents the format and key fields for each.

## CLAUDE.md (Claude Code)

Placed at project root. Markdown format with structured instructions.

```markdown
# Project: my-app

## Stack
- Runtime: Node.js 20
- Framework: Next.js 14
- Database: PostgreSQL 15

## Rules
- Always use TypeScript strict mode
- Run `npm test` before committing
- Never modify files in `vendor/`

## Commands
- Build: `npm run build`
- Test: `npm test`
- Lint: `npm run lint`
```

Claude Code reads this file at session start. Keep it under 500 lines.

## AGENTS.md (Cross-Agent Standard)

Placed at project root. This is the **canonical agent guidance file** following the [Linux Foundation AGENTS.md spec](https://agents.md/). Read by Codex, Cursor, Windsurf, Gemini CLI, Aider, Zed, Factory, Amp, and other tools.

0dai generates this file with the following sections:

- **Quick Context** — first 3 actions, MCP tool recommendations
- **File Structure** — expected `ai/` directory layout
- **Commands** — build/test/lint command table
- **Behavioral Contract** — convention rules, decision recording, experience logging
- **Planning Protocol** — structured reasoning, library doc lookup, project context rules
- **Available Subagents** — planner, architect, reviewer, qa, devops, security
- **Session Roaming** — handoff via `get_session` / `save_session`
- **Safety Rules** — protected files, destructive operation warnings
- **MCP Tools** — 58-tool reference, `.mcp.json` config, tier summary

The file is installed via `merge_managed_markdown_block` — user edits outside the managed block are preserved on sync.

## opencode.json

Placed at project root. JSON configuration for OpenCode agent.

```json
{
  "model": "anthropic:claude-sonnet-4-20250514",
  "provider": "anthropic",
  "project": {
    "name": "my-app",
    "runtime": "node20"
  },
  "instructions": "Follow the coding standards in CLAUDE.md"
}
```

## .gemini/settings.json

Placed in `.gemini/` directory.

```json
{
  "model": "gemini-2.5-pro",
  "codeExecution": true,
  "safetySettings": [],
  "systemInstruction": "You are working on the my-app project. Follow CLAUDE.md."
}
```

## ai/manifest/project.yaml

Central project manifest. Source of truth for 0dai tooling.

```yaml
name: my-app
version: 1.2.0
stack:
  runtime: node20
  framework: nextjs14
  database: postgresql15
  language: typescript

team:
  owner: alice
  agents:
    - claude-code
    - codex
    - aider

goals:
  - "Ship v2 API by Q2"
  - "Achieve 90% test coverage"

maturity:
  target: 80
  current: 65
```

Key fields:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Project identifier |
| `version` | Yes | Current project version |
| `stack` | Yes | Runtime, framework, database, language |
| `team.owner` | No | Human operator |
| `team.agents` | No | Configured agent list |
| `goals` | No | Current objectives |
| `maturity.target` | No | Target AI maturity score (0-100) |

## ai/manifest/commands.yaml

Defines available commands grouped by safety tier.

```yaml
safe:
  # Read-only, no side effects. Always approved.
  - name: test
    command: npm test
  - name: lint
    command: npm run lint
  - name: typecheck
    command: npx tsc --noEmit

workspace:
  # Modifies local files. Approved for most agents.
  - name: build
    command: npm run build
  - name: format
    command: npm run format
  - name: migrate
    command: npx prisma migrate dev

ops:
  # Affects external systems. Requires explicit approval.
  - name: deploy
    command: npm run deploy
  - name: publish
    command: npm publish
  - name: db-push
    command: npx prisma db push --accept-data-loss
```

Tier descriptions:

| Tier | Risk | Auto-approved |
|------|------|---------------|
| `safe` | None -- read-only | Yes |
| `workspace` | Local file changes | Yes (default) |
| `ops` | External side effects | No -- requires `check_approval` |
