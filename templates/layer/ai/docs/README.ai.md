# managed: true

# AI Layer

This directory is the AI operating layer for the project.

## Purpose

- Give coding agents one predictable place for architecture and workflow context.
- Separate project knowledge from agent-specific root config files.
- Support safe sync from the upstream universal AI repository.
- Provide portable prompts, playbooks, hooks, and stack detectors across CLI tools.

## Read Order

1. `ai/meta/project.manifest.yaml`
2. `ai/docs/decisions.md`
3. `AGENTS.md`
4. `CLAUDE.md`
5. `ai/playbooks/`
6. `ai/prompts/`

## Ownership

- Upstream toolkit owns files marked `managed: true`.
- Project team owns local decisions and custom docs.
- Project-level configs in `.codex/`, `.claude/`, `.opencode/`, and `opencode.json` should stay thin and point back to `ai/`.
