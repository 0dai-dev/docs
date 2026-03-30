# Rollout Recipe

## 1. Create The Upstream Repo

- Initialize this repository as `ZeroDayAI`.
- Keep `bootstrap/`, `templates/`, and `project_layouts/` versioned.
- Publish internal usage rules in `AGENTS.md`.

## 2. Pick Your Delivery Model

- `generator`: run scripts from this repo and copy generated files into product repos.
- `subtree`: vendor this repo into product repos and run `bin/ai-repo` locally.
- `submodule`: share updates centrally, but require version management discipline.

## 3. First Production Usage

- Run `./bin/0dai-repo init-existing --target <repo>` on a real repository.
- Review created `ai/` and root config files.
- Confirm `.codex/config.toml`, `.claude/settings.json`, and `opencode.json` match your policy.
- Add project-specific decisions to `ai/docs/decisions.md`.
- Commit once the generated layer matches your policy.

## 4. Governance

- Update `ai/VERSION` on meaningful template changes.
- Add new stack detectors before adding new stack scaffolds.
- Validate generated configs in CI if your org standardizes on these tools.
- Keep hooks conservative by default; allow stronger automation per project.
- Expand stack coverage with dedicated layout folders rather than overloading one generic scaffold.
