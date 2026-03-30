# FAQ

## Does 0dai replace Claude Code / Codex / Gemini?

No. 0dai generates the config files these agents read. It's the infrastructure layer *underneath* your agents — not a replacement.

## What happens to my existing CLAUDE.md?

Your content is preserved. 0dai uses managed blocks (marked `managed: true`) and `.generated` fallback files. Custom content is never overwritten. See [Migration Guide](migration.md).

## Do I need all 5 agent CLIs installed?

No. 0dai auto-detects which CLIs are present (`claude`, `codex`, `opencode`, `gemini`, `aider`) and generates configs only for those.

## Is this a SaaS product?

The core CLI runs entirely locally. All data stays in your repo. No cloud, no telemetry, no account required for core features.

Team features (shared knowledge base, activity feed, role-based access) require authentication via `0dai auth login`.

## What stacks are supported?

9 built-in stacks: FastAPI, Next.js, Flutter, Go, Python, React Native, Data/ML, backend-api, fullstack monorepo. Plus 8 community stacks in the registry. Custom stacks supported via `ai/stacks/`.

## How is this different from just writing CLAUDE.md?

CLAUDE.md is one file for one agent. 0dai generates configs for 5 agents simultaneously, adds experience tracking, MCP integration (43 tools), agent personas, org policies, team knowledge, compliance reporting, and session roaming. It's infrastructure, not a text file.

## What is Session Roaming?

Start a task in Claude Code, continue in Codex, finish in Gemini — without losing context. 0dai saves session state (goal, plan, files touched, decisions) in `ai/sessions/active.json`. Each agent auto-detects the active session on startup. See [Session Roaming Guide](session-roaming.md).

## What is the Experience Flywheel?

A knowledge lifecycle: capture task outcomes (`harvest`), review them as candidates, promote validated patterns to accepted knowledge (`promote`). Promoted knowledge syncs back into agent configs. Agents learn from your team's history.

## How much does it cost?

- **Free**: All core commands, all stacks, all CLIs, experience flywheel, MCP server. No limits.
- **Team** ($29/mo): Shared knowledge base, activity feed, role-based access, federation, conflict resolution.
- **Enterprise** (custom): SSO, compliance reporting, policy engine, dedicated support.
