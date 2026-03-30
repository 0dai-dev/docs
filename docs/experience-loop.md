# Bidirectional Experience Loop

## Architecture

```
                    ┌─────────────────────┐
                    │   0dai upstream      │
                    │   (this repo)        │
                    │                      │
                    │  ai/inbox/           │ ◄── aggregated reports from projects
                    │  ai/bulletins/       │ ──► knowledge pushed to projects
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
        ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
        │ Project A  │   │ Project B  │   │ Project C  │
        │            │   │            │   │            │
        │ ai/        │   │ ai/        │   │ ai/        │
        │  experience│   │  experience│   │  experience│
        │  bulletins │   │  bulletins │   │  bulletins │
        │  telemetry │   │  telemetry │   │  telemetry │
        └────────────┘   └────────────┘   └────────────┘
```

## Flow: Project → Upstream (Reporting)

1. Agent works in project, `0dai task run` records events
2. `0dai harvest` converts events to candidates
3. `0dai promote` accepts good candidates
4. **NEW**: `0dai report` generates anonymized telemetry summary:
   - Stack, tool usage, task type distribution
   - Accepted patterns count by category
   - CI pass rate, human takeover rate
   - No code, no paths, no secrets — only aggregated metrics
5. Report written to `ai/telemetry/reports/` as JSON
6. Optionally pushed to upstream via `0dai report --push`

## Flow: Upstream → Project (Bulletins)

1. 0dai maintainers (or automation) create bulletins in `templates/layer/ai/bulletins/`
2. Bulletins contain: new rules, pattern warnings, security advisories, best practices
3. During `0dai sync`, new bulletins are installed to project `ai/bulletins/`
4. **NEW**: `0dai pull-bulletins` fetches latest bulletins without full sync
5. MCP tool `get_bulletins` exposes active bulletins to agents
6. Agents read bulletins to stay current with cross-project learnings

## Telemetry Report Schema

```json
{
  "schema": 2,
  "generated_at": "2026-03-28T...",
  "project_id": "sha256-of-repo-name",
  "stack": "fastapi",
  "repo_mode": "polyrepo",
  "ai_version": "0.2.1",
  "period_days": 30,
  "metrics": {
    "events_total": 47,
    "ci_pass_rate": 0.89,
    "human_takeover_rate": 0.12,
    "revert_rate": 0.02
  },
  "tool_usage": { "claude": 30, "codex": 17 },
  "task_types": { "bugfix": 20, "feature": 15, "refactor": 12 },
  "knowledge": {
    "rules_accepted": 3,
    "skills_accepted": 2,
    "anti_patterns_accepted": 1
  },
  "bulletins_applied": ["2026-03-security-advisory", "2026-03-mcp-best-practices"]
}
```

## Bulletin Schema

```yaml
managed: true
id: 2026-03-mcp-best-practices
severity: info
published: 2026-03-28
expires: 2026-09-28
applies_to:
  stacks: all
  versions: ">=0.2.0"
title: MCP Server Security Best Practices
body: |
  Start with read-only tools. Validate all inputs from LLM.
  66% of MCP servers have vulnerabilities. Never expose secrets
  through MCP tool responses.
action: review
```

## Privacy

- Project names are SHA256-hashed in telemetry
- No source code, file paths, or credentials leave the project
- Only aggregated metrics and counts
- `--dry-run` flag shows exactly what would be reported
- Reports stay local unless `--push` is explicitly used
