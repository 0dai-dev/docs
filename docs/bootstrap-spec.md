# Bootstrap Spec

## Core Model

ZeroDayAI uses two layers in every target repository:

1. `ai/` as the canonical generation and synchronization layer.
2. Native tool files in the locations that Codex, Claude Code, and OpenCode actually read.

The canonical layer owns templates, manifests, prompts, playbooks, and generation logic.
The native layer is emitted from that source of truth.

## Canonical Layer

```text
ai/
  bootstrap/
    lib.sh
    detect.sh
    init_existing.sh
    init_new.sh
    sync.sh
    validate.sh
    doctor.sh
    harvest.sh
    promote.sh
  manifest/
    project.yaml
    applied-lock.json
    discovery.json
    init-report.md
    commands.yaml
  packs/
  channels/
  migrations/
  templates/
    shared/
    codex/
    claude/
    opencode/
  prompts/
  playbooks/
  docs/
  skills-src/
  agents-src/
  experience/
```

`ai/templates/` is the canonical template source for emitted native files. ZeroDayAI bootstrap should now prefer rendering from `ai/templates/`, while upstream `templates/root/` is intentionally reduced to a minimal compatibility bridge.

`bootstrap/native_output_map.json` is the internal mapping layer from canonical sources to native output paths and compatibility shims.

## Native Outputs

```text
repo/
  AGENTS.md
  .codex/
    config.toml
    agents/
  .agents/
    skills/
  .claude/
    settings.json
    CLAUDE.md
    rules/
    skills/
    agents/
    hooks/
  .mcp.json
  opencode.json
  .opencode/
    agents/
  ai/
```

## Source Of Truth

- `ai/manifest/project.yaml` is the canonical project contract.
- `ai/manifest/applied-lock.json` pins the applied pack versions and generated state.
- `ai/manifest/discovery.json` is generated from repository inspection.
- `ai/manifest/init-report.md` records what bootstrap changed.
- `ai/manifest/commands.yaml` classifies project commands by execution tier.
- `ai/VERSION` tracks the installed ZeroDayAI layer version for sync and migrations.
- `ai/VERSION_SCHEMA` tracks the schema version of the AI layer structure itself.

## `init-existing`

Purpose: adapt ZeroDayAI to an existing repository without restructuring user code.

### Contract

```bash
./bin/0dai-repo init-existing --target <path> [--agents <list|auto>] [--dry-run] [--report json]
```

### Required behavior

- detect stack from pattern files in `ai/patterns/detectors/`
- detect installed tools and existing native configs
- write `ai/manifest/discovery.json`
- materialize `ai/manifest/project.yaml`
- emit native configs only for enabled tools
- merge managed blocks into existing `AGENTS.md` and `.claude/CLAUDE.md` instead of overwriting user content
- preserve non-managed files and stage `*.generated` candidates on conflict
- never edit user-level config in home directories
- never commit automatically

### Native files emitted

- Codex: `AGENTS.md`, `.codex/config.toml`, optional `.codex/agents/*`
- Claude Code: `.claude/settings.json`, `.claude/CLAUDE.md`, `.claude/rules/*`, `.claude/hooks/*`, optional `.claude/agents/*`
- OpenCode: `opencode.json`, `.opencode/agents/*`
- Shared skills: `.agents/skills/*`, `.claude/skills/*`

## `init-new`

Purpose: create a new AI-ready repository with a strong default layout and native multi-tool outputs.

### Contract

```bash
./bin/0dai-repo init-new --target <path> --stack <name> [--agents <list|auto>] [--no-git] [--dry-run]
```

### Required behavior

- scaffold project layout from `project_layouts/<stack>/`
- initialize the canonical `ai/` layer
- write `ai/manifest/project.yaml`
- emit native files for Codex, Claude Code, and OpenCode
- create `.gitignore`
- run `git init` unless disabled
- validate generated outputs and write `ai/manifest/init-report.md`

## Safety Model

- managed files may be updated by sync
- non-managed files are preserved
- existing markdown entrypoints should prefer managed blocks or imports over full replacement
- seed-only files are created once and not silently replaced
- deterministic policies belong in hooks, not only in instruction docs

## Sync And Migrations

- `sync` must compare `ai/VERSION` with the upstream ZeroDayAI version.
- known version jumps may run explicit migration scripts from `bootstrap/migrations/`
- unknown version jumps should fall back to managed sync without destructive rewrites
- every sync should refresh `ai/manifest/init-report.md`
- pack/channel upgrades should update `ai/manifest/applied-lock.json`
- bootstrap and sync should refresh generated file hashes in `ai/manifest/applied-lock.json`
- bootstrap and sync should refresh `ai/manifest/commands.yaml` from current repo and environment heuristics

## Command Tiers

- `safe`: low-risk commands like linting or formatting
- `workspace`: commands that mutate or validate the project workspace
- `ops`: commands with infrastructure, service, or operational impact

## Knowledge Layers

- `instructions`: rules, policy, architecture, and workflow guidance
- `skills`: reusable recipes and repeatable workflows
- `experience`: events, candidate lessons, accepted knowledge, rejected items, and archives

`experience` should collect normalized operational signals, not full chat transcripts or large raw logs.

## Native Tool Notes

- Codex project config lives in `.codex/config.toml`
- Codex and OpenCode share root `AGENTS.md`
- Claude Code project config lives in `.claude/settings.json`
- Claude-specific instructions live in `.claude/CLAUDE.md` and `.claude/rules/`
- OpenCode project config lives in `opencode.json`

## Validation

- structural validation: `python3 scripts/validate_templates.py`
- smoke validation: `bash tests/smoke_test.sh`
- future goal: tool-aware validation for Codex, Claude Code, and OpenCode runtime status

## Doctor

- `./bin/0dai doctor --target <path>` reports environment, execution mode, available CLIs, and command tier decisions

## Experience Commands

- `0dai task run` records normalized task completion events into `ai/experience/outbox/`
- `harvest` converts normalized events in `ai/experience/outbox/` into candidate lessons in `ai/experience/candidates/`
- `promote` moves reviewed candidates into `ai/experience/accepted/` by knowledge type
- `python3 scripts/aggregate_experience.py` generates a summarized experience report for CI artifacts
- `python3 scripts/prepare_knowledge_issue.py` generates a GitHub-native intake summary for issue or discussion creation
- `python3 scripts/create_knowledge_issue.py --repo <owner/repo>` opens an intake issue when thresholds are met

## Container Runtime

- `docker/ai-runner/Dockerfile` provides the baseline interactive runtime.
- `docker-compose.ai.yml` mounts the repository as `/workspace` and keeps user state in volumes.
- `.devcontainer/devcontainer.json` reuses the same runtime model for editor-based development.
- `docker/ai-runner/entrypoint.sh` supports explicit `trusted|untrusted` and `auto|init|sync|none` bootstrap modes.
- `docker/ai-runner/check-tools.sh` and `docker/ai-runner/examples/` provide runtime diagnostics and example user/system configs.
