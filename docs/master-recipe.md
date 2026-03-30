# Master Recipe

## What This Repository Is

`ZeroDayAI` is an upstream generator and sync source for project-local AI operating layers.

It gives each product repository:

- one shared `ai/` canonical memory and generation layer,
- one predictable integration pattern for Codex, Claude Code, and OpenCode,
- one safe sync path for future upgrades.

## Golden Rules

- Keep product knowledge in `ai/`, not duplicated across tool-specific configs.
- Keep native config files thin: they should be emitted from `ai/`, not become the new source of truth.
- Only overwrite files that are explicitly marked managed.
- Treat `ai/docs/decisions.md` as the short ADR stream for humans and agents.
- Use `ai/manifest/project.yaml` as the canonical project contract.
- Prefer rendering native outputs from `ai/templates/` and keep upstream root templates reduced to the smallest possible compatibility shim set.
- Separate instructions, skills, and experience so durable knowledge does not collapse into one giant instruction file.
- Treat Docker as the outer runtime sandbox and native CLI permissions as the inner sandbox.
- For untrusted repositories, prefer explicit container startup with automatic bootstrap disabled.

## Recommended Delivery Modes

1. `generator`: simplest adoption; copy generated files into target repos.
2. `subtree`: good balance of visibility and centralized upgrades.
3. `submodule`: strongest upstream linkage, highest operational discipline.

## Production Rollout

1. Stabilize this repository and tag `v0.1.0`.
2. Test `init-existing` on one real Node/Python repo and one Flutter repo.
3. Test `init-new` for greenfield creation.
4. Add org-specific policies, MCP servers, and CI validation.
5. Freeze the initial contract and start onboarding teams.

## Definition Of Done

- `bin/ai-repo detect`, `init-existing`, `init-new`, and `sync` work on target repos.
- Managed files update safely on repeat sync.
- Root configs exist for Codex, Claude, and OpenCode.
- `ai/` contains prompts, playbooks, stack detectors, decisions log, and hooks.
- CI verifies the AI layer exists and remains structurally valid.

## Upstream Validation

- Run `bash tests/smoke_test.sh` before tagging a new version.
- Run `python3 scripts/validate_templates.py` for fast structural validation.
- Keep GitHub Actions green on `.github/workflows/smoke.yml`.
- Extend smoke coverage whenever a new stack or config contract is added.
- Add explicit migration scripts when `ai/VERSION` changes require structure-aware sync.
- Add doctor diagnostics when manifests become rich enough to explain policy decisions, not just store them.

## Knowledge Flywheel

- Collect normalized experience events instead of raw transcripts.
- Review and promote repeated patterns into rules, skills, playbooks, or anti-patterns.
- Keep local or personal memory outside the shared repository contract unless it becomes validated team knowledge.
