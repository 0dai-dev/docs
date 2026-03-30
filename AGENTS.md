# ZeroDayAI Guidance

## Mission

This repository defines a reusable AI-first operating layer for software projects.

## Working Rules

- Prefer extending templates over inventing one-off project logic.
- Keep the generated project layer under `ai/` simple, explicit, and readable.
- Preserve user changes in target repositories; do not overwrite unmanaged files silently.
- Update docs and templates together when changing bootstrap behavior.
- Keep bootstrap scripts POSIX-friendly when possible.

## Read Order

1. `README.md`
2. `docs/architecture.md`
3. `bootstrap/*.sh`
4. `templates/`
5. `project_layouts/`

## Output Philosophy

- New project mode should create a strong default.
- Existing project mode should adapt and avoid breakage.
- Sync should be safe, predictable, and reviewable.
