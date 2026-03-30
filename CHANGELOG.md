# Changelog

## v1.0.0 - 2026-03-30

**General Availability. Five agents. One config. Zero friction.**

## v1.0.0-rc.1 - 2026-03-30

Release Candidate 1. Feature-complete for v1.0 General Availability.

**Highlights since v0.1.0:**
- 5 agent CLIs: Claude Code, Codex, OpenCode, Gemini, Aider
- 9 built-in stacks with weighted detection
- 43 MCP tools (read + write + system)
- Session Roaming between agent CLIs
- Experience Flywheel (harvest → promote → sync)
- Supabase self-hosted backend (GoTrue + PostgREST)
- User accounts: profile, team management, billing
- 3 payment methods: Stripe, Crypto (BTC/ETH/USDC/SOL), bank transfer
- Compliance reporting: SOC 2 + ISO 27001
- Documentation site (MkDocs, 8 pages)
- API stability guarantees documented

## v0.9.5 - 2026-03-30

- Hardening: MCP path traversal protection, graceful errors, SDK version sync, API stability doc.
- Ready for v1.0 Release Candidate.

## v0.9.4 - 2026-03-30

- Add documentation site: MkDocs with Material theme.
- Pages: Getting Started, Session Roaming Guide, Migration Guide, CLI Reference, MCP Reference, SDK Reference, Architecture, FAQ.
- Dark theme (slate) with teal accent matching landing page.

## v0.9.3 - 2026-03-30

- Add billing: `0dai billing` with 3 payment methods.
- Stripe (card), Coinbase Commerce (crypto: BTC/ETH/USDC/SOL), bank transfer.
- API key management: create/list/revoke `0dai_sk_*` keys for MCP HTTP.

## v0.9.2 - 2026-03-30

- Add user account dashboard: Profile, Team, Project, Usage pages at /account.
- Add `0dai team` CLI: members, invite, remove, role.
- Team invite generates shareable auth codes.
- Dashboard nav bar extended with Account tab.

## v0.9.1 - 2026-03-30

- Real auth: API-first validation with offline fallback for development.
- Add `0dai auth signup --email` and `0dai auth refresh`.
- Complete auth flow: signup → code → login → token → team features.

## v0.9.0 - 2026-03-30

- CONSOLIDATION: tiered CLI help — `0dai --help` shows 10 core commands, `--help --all` shows full 50.
- Rewrote help to group commands by tier: Core (10), Account (2), Additional, Team, Enterprise, Internal.
- Updated roadmap with concrete v0.9.0→v1.0.0 plan including user accounts and billing.
- Begins v0.9.x — the path to v1.0 (real auth, real billing, real user accounts).

## v0.8.1 - 2026-03-30

- Add webhook hooks: trigger external systems on init/sync/audit/deploy events.
- `0dai webhook` CLI: add, list, remove, test. Completes v0.8.x Now.

## v0.8.0 - 2026-03-30

- Add plugin system: extend 0dai with custom commands, checks, generators via ai/plugins/.
- Plugin scaffold, execution, validation. `get_plugins` MCP tool (43 total).
- Begins v0.8.x — Platform & Extensibility.

## v0.7.8 - 2026-03-30

- Add change approval workflows: ops-tier commands (deploy, migrate, rollback) require human approval.
- `0dai approve` CLI: list, approve, deny, check, request.
- `check_approval` MCP tool — agents auto-request approval for ops commands (42 total).
- Approval state in ai/manifest/approvals.json with pending/history tracking.

## v0.7.7 - 2026-03-30

- Add multi-tenant MCP server: `--multi /proj1 /proj2` serves multiple projects from one server.
- `list_projects` MCP tool shows all registered projects with ai/ layer status.
- `get_project_health_multi` queries specific project by name.
- Isolation: each tool call resolves target via project name, no cross-contamination.
- Backwards compatible: single-tenant mode unchanged without `--multi` flag.

## v0.7.6 - 2026-03-29

- Add SSO for dashboard: `0dai serve --sso` authenticates via cloud auth token.
- SSO login page accepts auth codes directly or uses existing `~/.0dai/auth.json` from `0dai auth login`.
- Dashboard auto-detects cloud token — if already authenticated, no login needed.
- Backwards compatible: `--auth --password` mode still works alongside `--sso`.

## v0.7.5 - 2026-03-29

- Add sensitive data scanner: detect secrets, API keys, tokens, PII in ai/ layer configs.
- 14 detection patterns: AWS/GCP/Stripe/OpenAI/Anthropic keys, GitHub PATs, JWT, private keys, passwords, connection strings.
- Add `0dai scan` CLI with `--json` and `--fix` (auto-redact found secrets).
- Add `scan_secrets` MCP tool (39 total).

## v0.7.4 - 2026-03-29

- Add cloud authentication: `0dai auth login` with browser-based auth code flow.
- Token stored at ~/.0dai/auth.json with 7-day offline TTL and auto-refresh.
- Replace offline license.json with cloud auth for all team features.
- Team-gated commands (kb, activity, role-policy, conflicts, federation) now require `0dai auth login`.
- Add `0dai auth` CLI: login, status, logout, --json.
- Core CLI (init, sync, doctor, detect, serve, harvest, promote, search) remains fully free without auth.

## v0.7.3 - 2026-03-29

- Add session roaming: transfer active task context between AI agent CLIs seamlessly.
- Start in Claude Code, continue in Codex, finish in Gemini — session state preserved in ai/sessions/active.json.
- Session includes: goal, plan, files touched, key decisions, handoff notes, agent history.
- Add `0dai session` CLI: save, status, complete, history, --json.
- Add `get_session` and `save_session` MCP tools (38 total).
- SessionStart hook auto-detects active session and shows handoff notes to the next agent.

## v0.7.2 - 2026-03-29

- Add compliance reporting: generate SOC 2 Type II and ISO 27001:2022 evidence from ai/ layer data.
- Maps 8 evidence sources to 6 framework controls with pass/gap status.
- Evidence from: audit logs, WAL, role policies, org policies, experience pipeline, version control, prompt versioning, licensing.
- Add `0dai compliance` CLI with `--framework soc2|iso27001`, `--json`.
- Add `get_compliance_report` MCP tool (36 total).
- Completes v0.7.x Now section.

## v0.7.1 - 2026-03-29

- Add enterprise policy engine: `0dai policy-push` pushes centralized org policies to all registered repos.
- Default policy pack with protected paths, denied commands, and deployment constraints.
- Org rules pushed to `.claude/rules/` as `org-*` prefixed files.
- Add license gating for team features: kb, activity, role-policy, conflicts, federation show soft upgrade message without team license.
- Add `policy-push` CLI: init, add-repo, push, status, --json.

## v0.7.0 - 2026-03-29

- Add product landing page: `0dai site` serves a single-page site with problem statement, pricing, and quick start.
- Add offline license validation: `scripts/license.py` with JWT-like tier checking (free/team/enterprise).
- Rewrite README with problem-first positioning: "Stop duplicating AI agent configs 5 different ways."
- Define monetization tiers: Free (solo), Team $29/mo (shared KB, roles, federation), Enterprise (SSO, compliance).
- Feature tiering: Core (5 commands), Advanced (8), Power (22) — landing page shows only Core.
- Begins v0.7.x — Enterprise Readiness & GTM phase.

## v0.6.4 - 2026-03-29

- Add concurrent edit resolution: detect and resolve ai/ layer conflicts across branches.
- Managed files auto-resolved (upstream wins), custom files flagged for manual review.
- Add `0dai conflicts` CLI with `--branch`, `--resolve`, `--json`.
- Add `check_conflicts` MCP tool (35 total).
- Completes v0.6.x Next section.

## v0.6.3 - 2026-03-29

- Add role-based command policy: per-user access control for command tiers.
- Four roles: viewer (safe), developer (safe+workspace), lead (+promote), admin (all+deploy).
- Add `0dai role-policy` CLI: init, set, check, list, --json.
- Add `get_role_policy` MCP tool — agents check access before ops commands (34 total).
- Policy stored in ai/manifest/role-policy.json.

## v0.6.2 - 2026-03-29

- Add team activity feed: unified timeline from audit log, WAL, experience events, and git commits.
- Shows who changed what in ai/ layer, when, with which agent (cli/mcp/git).
- Add `0dai activity` CLI with `--limit`, `--filter <source>`, `--json`.
- Add `get_activity_feed` MCP tool with source filtering (33 total).

## v0.6.1 - 2026-03-29

- Add shared knowledge base: centralized team-level experience hub for cross-project knowledge.
- `0dai kb init` connects a project to a shared KB directory.
- `0dai kb push` — push accepted knowledge (rules, skills, playbooks, anti-patterns) to KB.
- `0dai kb pull` — pull team knowledge into `ai/experience/team-knowledge/` (skips own contributions).
- `0dai kb search` — full-text search across team knowledge.
- Contributor tracking in `meta/kb.json` — who pushed what, when.
- Add `get_knowledge_base` MCP tool with optional search (32 total).
- Completes v0.6.x Now section.

## v0.6.0 - 2026-03-29

- Add authenticated team dashboard: `0dai serve --auth --password <pass>` enables login-protected multi-page UI.
- Dashboard now has 3 pages: Overview (health/manifests), Activity (audit log), WAL (mutation history).
- Session-based auth with HTTP-only cookies, SHA-256 password hashing, 8-hour TTL.
- Support `--users <file.json>` for multi-user access and `ODAI_DASHBOARD_PASSWORD` env var.
- Navigation bar with active page indicator and auth status badge.
- Begins v0.6.x — Team Collaboration phase.

## v0.5.6 - 2026-03-29

- Add write-ahead log (WAL) for MCP mutations: undo/redo for ai/ layer changes.
- All MCP write tools (create_spec, record_experience, update_decision) now record file state before mutation.
- Add `0dai wal` CLI with `--list`, `--undo [<id>]`, `--json`.
- Add `get_wal` and `undo_mutation` MCP tools (31 total).
- WAL stored in ai/manifest/wal.jsonl with base64 before-state for reliable rollback.
- Completes entire v0.5.x roadmap (Now + Next + Later all delivered).

## v0.5.5 - 2026-03-29

- Add prompt versioning: track and diff system prompt changes over time.
- Snapshots prompt hashes from ai/prompts/, .claude/agents/, .gemini/agents/, .aider/agents/.
- History stored in ai/prompts/.history.json with add/modify/remove tracking.
- Add `0dai prompt-history` CLI with `--status`, `--history`, `--json`.
- Add `get_prompt_history` MCP tool (29 total).

## v0.5.4 - 2026-03-29

- Add observability templates: stack-aware tracing configs for Langfuse, OpenTelemetry, and LangSmith.
- Catalog maps 10 stacks to recommended providers with packages and env vars.
- Add `0dai observability` CLI with `--list`, `--json`, `--provider <name>`.
- Generates `ai/observability/.env.observability.template` and `recommendations.json`.
- Add `get_observability` MCP tool (28 total).
- Completes v0.5.x Next roadmap section.

## v0.5.3 - 2026-03-29

- Add Aider as 5th supported agent CLI (50K+ stars, git-native, BYOK model support).
- Generate `.aider.conf.yml` and `.aider/agents/` during init and sync.
- 6 agent templates: coder, reviewer, architect, qa, devops, security.
- Aider detected in `detect_available_clis()`, added to standard and enterprise presets.
- All detectors, templates, and native output map updated for Aider.

## v0.5.2 - 2026-03-29

- Add experience auto-scoring: rank candidates by impact, frequency, and quality signals across 6 dimensions.
- Scoring: recurrence (0-10), CI signal (0-5), stability (0-3), scope clarity (0-2), review quality (0-3), type weight (0-2). Max 25.
- Recommendations: promote (>=18), review (>=10), defer (<10).
- Add `0dai score-experience` CLI with `--json` and `--auto-promote` for threshold-based auto-promotion.
- Add `score_candidates` MCP tool (27 total).

## v0.5.1 - 2026-03-29

- Add agent orchestration config generator: `0dai orchestrate` produces squad and swarm workspace definitions.
- Generates `ai/orchestration/squad.yaml` (lead + specialists + gate) and `ai/orchestration/swarm.yaml` (orchestrator + parallel specialists + reviewer).
- Agents, roles, and workflows derived from ai/personas/ and ai/playbooks/.
- Supports `--list` for roster preview and `--json` for programmatic access.
- Add `get_orchestration` MCP tool (26 total).

## v0.5.0 - 2026-03-29

- Add MCP write tools: agents can now modify the ai/ layer, not just read it.
- `create_spec` — create structured development specs with auto-incremented IDs.
- `record_experience` — record experience events for the knowledge flywheel.
- `update_decision` — append Architecture Decision Records to decisions.md.
- All write operations logged to audit.jsonl with `mcp-write:` prefix.
- Opens v0.5.x roadmap: Write Operations & Agent Orchestration (25 MCP tools total).

## v0.4.4 - 2026-03-29

- Add stack compatibility tester: `0dai stack-test` scaffolds every layout in temp dirs and validates structure.
- Tests 9 stacks: verifies scaffold output, AI layer, native configs, and structure.md paths.
- Supports `--stack <name>` for single-stack testing and `--json` for CI.
- Structure.md parser correctly handles nested path indentation.
- Completes v0.4.x roadmap — all Automation & Intelligence features delivered.

## v0.4.3 - 2026-03-29

- Add documentation drift detector: `0dai doc-drift` compares code state against docs.
- 41 checks across 6 categories: CLI commands in README, script references, stack docs, persona fields, architecture docs, agent-persona consistency.
- Supports `--json` for CI integration.
- Detects missing scripts, undocumented commands, incomplete personas, and template mismatches.

## v0.4.2 - 2026-03-29

- Add pre-release auditor: `0dai audit` combines roadmap guardian, template validation, version consistency, git state, and migration checks into a single pass/fail gate.
- 13 automated checks across 7 categories: version, git, templates, guardian, migrations, smoke, changelog.
- Supports `--json` for CI integration and `--fix` for remediation suggestions.
- Blocks release on any FAIL, warns on non-critical issues.

## v0.4.1 - 2026-03-29

- Add code graph analysis: `codebase-map.json` now includes `import_graph` with module dependency data.
- Parses Python (`import`/`from`), JavaScript/TypeScript (`import`/`require`), and Go (`import`) statements.
- Graph includes: files with imports, total edges, external dependency ranking (top 20), per-file import list.
- MCP `get_codebase_map` tool now returns import graph data alongside structural analysis.

## v0.4.0 - 2026-03-29

- Add changelog automation: `0dai changelog` generates entries from git log between tags.
- Supports `--from`, `--to`, `--version`, `--apply` (prepend to CHANGELOG.md), and `--json`.
- Auto-detects latest tag as starting point, groups by conventional commit categories.
- Opens v0.4.x roadmap: Automation & Intelligence.

## v0.3.8 - 2026-03-29

- Add remote MCP server mode via Streamable HTTP transport.
- Add `--http` flag to `0dai mcp` for HTTP mode (default: stdio unchanged).
- Configurable `--host` (default 127.0.0.1) and `--port` (default 8421).
- MCP endpoint available at `http://<host>:<port>/mcp` when in HTTP mode.
- Add `.mcp-remote.json` template for connecting to remote 0dai MCP server.
- Completes v0.3.x roadmap — all planned features delivered.

## v0.3.7 - 2026-03-29

- Add Backstage Software Template export: generate `template.yaml` for Spotify Backstage developer portal.
- Export all 9 project layouts as Backstage-compatible scaffolder templates.
- Add `0dai backstage-export` CLI: `--list`, `--export <stack|all>`, `--output <dir>`, `--json`.
- Templates include AI layer configuration step with agent selection and preset choice.
- Pre-generated templates available in `backstage/` directory.

## v0.3.6 - 2026-03-29

- Prepare Python SDK for PyPI publication: `pip install zerodayai`.
- Add SDK README with API reference and quick start examples.
- Add `py.typed` marker for PEP 561 type checking support.
- Update `pyproject.toml` with classifiers, keywords, author, and URLs.
- Add GitHub Actions workflow for automated PyPI publish on tag push.
- SDK version synced to project version (0.3.6), 8 public functions, zero dependencies.

## v0.3.5 - 2026-03-29

- Add spec-driven development: structured specifications in `ai/specs/` with YAML frontmatter + markdown body.
- Specs define context, goal, requirements, acceptance criteria, and technical notes for agents.
- Add `0dai spec` CLI: `--new`, `--list`, `--info`, `--validate`, `--json`.
- Auto-generates spec IDs (SPEC-001, SPEC-002, ...) and validates structure.
- Add `get_specs` MCP tool with status filtering (22 MCP tools total).
- Add `specs()` function to Python SDK.
- Ships with TEMPLATE.md and 2 example specs for reference.
- Spec directory installed during `init-existing` and `sync`.

## v0.3.4 - 2026-03-29

- Add Agent Teams config generator: 6 specialized agents for `.claude/agents/` (planner, reviewer, architect, qa, devops, security).
- Agent definitions derived from `ai/personas/` with rich system prompts, focus paths, review checklists.
- Add `0dai agent-teams` CLI with `--list`, `--info <name>`, `--json` subcommands.
- Add `get_agent_teams` MCP tool (21 total).
- Add `agent_teams()` function to Python SDK.
- Add matching Gemini agent templates (architect, qa, devops, security).

## v0.3.3 - 2026-03-28

- Add MCP catalog per stack: auto-recommend and install MCP servers in `.mcp.json` based on detected project stack.
- Catalog applied during `init-existing` and `sync` — zero-config MCP setup.
- Add `get_mcp_catalog` MCP tool (20 total).

## v0.3.2 - 2026-03-28

- Add Gemini CLI as 4th supported agent with `.gemini/settings.json` and `.gemini/agents/` generation.
- Gemini detected in `detect_available_clis()`, configs generated during init and sync.
- Added to standard and enterprise configure presets.
- All detectors, templates, and native output map updated for Gemini.

## v0.3.1 - 2026-03-28

- Add `0dai maturity` command: 0-100 scorecard with grade (A-F), badge URL, and detailed check breakdown.
- Evaluates: manifests, native configs, experience lifecycle, personas, org policy, IDE configs, bulletins, federation, audit log.
- Add `get_maturity_score` MCP tool (19 total).
- Add memory-bank infrastructure for persistent project state between sessions.
- Publish v0.3.x roadmap with maturity scorecards, Gemini CLI, Agent Teams, MCP catalog, spec-driven templates.

## v0.3.0 - 2026-03-28

- Add community stack registry with 8 stacks (django, rails, spring-boot, rust, svelte-kit, nuxt, terraform, kubernetes).
- Add `0dai registry` command with `--list`, `--search`, `--install` for browsing and installing community stacks.
- Add IDE config generation: `.vscode/settings.json`, `.vscode/extensions.json`, `.idea/0dai.xml` auto-generated per stack.
- Add `get_registry` MCP tool (18 MCP tools total).
- IDE configs run automatically during `init-existing` and `sync`.
- **Closes the entire v0.2.x roadmap** — all Now, Next, and Later items complete. Graduate to v0.3.0.

## v0.2.9 - 2026-03-28

- Add cross-repo knowledge federation: link related repos and sync accepted experience (rules, skills, anti-patterns).
- Add `0dai federation` command with `--add`, `--sync`, `--remove`, and status display.
- Synced knowledge stored in `ai/experience/federated/<peer>/` — isolated from local knowledge.
- Add `get_federation` MCP tool showing peer status, reachability, and synced item counts (17 MCP tools total).

## v0.2.8 - 2026-03-28

- Add enterprise audit logging: every init/sync writes to `ai/manifest/audit.jsonl` with timestamp, action, user, version.
- Add TF-IDF semantic search over `ai/experience/` replacing simple substring matching — results ranked by relevance score.
- Add `0dai search --target <path> --query <text>` CLI command.
- Upgrade MCP `search_experience` tool to TF-IDF ranking (16 MCP tools total with new `get_audit_log`).

## v0.2.7 - 2026-03-28

- Add `0dai serve` lightweight web dashboard — single-page dark-themed HTML view of project AI layer health.
- Dashboard shows: version, stack, repo mode, manifests health, codebase map, personas, bulletins, command tiers, org policy.
- JSON API endpoint at `/api/health` for programmatic access.
- Zero dependencies — pure Python stdlib (http.server).
- Completes the v0.2.x "Next" roadmap section.

## v0.2.6 - 2026-03-28

- Add Python SDK (`sdk/zerodayai/`) with programmatic access to ai/ layer: `detect()`, `health()`, `manifests()`, `codebase_map()`, `experience()`, `version()`.
- SDK requires zero dependencies — pure Python stdlib, works with Python 3.10+.
- Add SDK unit test (14 total tests now).
- Publishable via `pip install .` from `sdk/` directory.

## v0.2.5 - 2026-03-28

- Add custom stack extensibility: projects define stacks in `ai/stacks/*.yaml` with priority over upstream detectors.
- Custom stacks use the same weighted scoring (match_primary/match_any/priority) as built-in stacks.
- Add `get_custom_stacks` MCP tool (15 total).
- Add custom stacks README with schema docs and priority guidelines.

## v0.2.4 - 2026-03-28

- Add 4 agent persona profiles: architect, qa, devops, security with role-specific prompts, focus paths, and review checklists.
- Personas installed automatically during `init-existing` and `sync` to `ai/personas/`.
- Add `get_personas` MCP tool (14 total) so agents can discover and adopt personas.

## v0.2.3 - 2026-03-28

- Add pre-sync backup mechanism: tar snapshot of ai/ before sync, keeps last 5 backups.
- Add `0dai configure` wizard with 3 presets (minimal, standard, enterprise) for one-command project setup.
- Configure generates `ai/config/project-config.json` and updates `.mcp.json` with recommended servers.

## v0.2.2 - 2026-03-28

- Add bidirectional experience loop: telemetry reporting (project → upstream) and bulletins (upstream → project).
- Add `0dai report` command generating anonymized telemetry with aggregated metrics, tool usage, and knowledge counts.
- Add `0dai pull-bulletins` command and automatic bulletin sync during `0dai sync`.
- Ship 2 initial bulletins: MCP security advisory and experience TTL guidance.
- Add `get_bulletins` and `get_telemetry_summary` MCP tools (13 total MCP tools now).
- Add experience loop architecture documentation.

## v0.2.1 - 2026-03-28

- Add 0dai MCP server with 11 read-only tools exposing project AI layer to any MCP-compatible agent.
- Tools: get_project_health, get_project_manifest, get_codebase_map, get_org_policy, get_commands, get_environment, get_discovery, get_applied_lock, get_ai_version, search_experience.
- Built on FastMCP 3.1.1 — agents query knowledge via protocol, no CLI wrapping.
- Add `0dai mcp` command and self-register in `.mcp.json`.
- Add MCP server unit test (13 total tests now).

## v0.2.0 - 2026-03-27

- Graduate from v0.1.x to v0.2.0 with production-readiness focus.
- Add 12 unit tests covering codebase analyzer, experience aggregator, scorer, guardian, and validator.
- Harden JSON parsing in aggregate, score, and prepare scripts with try-except and readable error messages.
- Replace hardcoded experience expiration date with dynamic TTL via `ODAI_EXPERIENCE_TTL_DAYS` env var (default 180 days).
- Add `--verbose` / `-v` flag and `debug()` function across all bootstrap commands.
- Fix guardian warning: add apply_org_pack.sh to README tree (64/64 checks now pass).
- Publish v0.2.0 roadmap with 12 planned features across Now/Next/Later.

## v0.1.19 - 2026-03-27

- Add mono-repo and poly-repo template packs with detection indicators, agent guidance, CI strategy, and structural expectations.
- Add automatic repo mode detection in codebase analysis (checks workspaces, monorepo markers, directory structure).
- `ai/manifest/codebase-map.json` now includes `repo_mode` field ("monorepo" or "polyrepo").

## v0.1.18 - 2026-03-27

- Add codebase analysis that generates `ai/manifest/codebase-map.json` with entry points, dependency managers, directory roles, and file type distribution.
- Wire analysis into `init-existing` and `sync` so agents automatically get a structural map of the project.
- Classify directories by role (source, tests, infrastructure, etc.) and detect dependency managers across all supported stacks.

## v0.1.17 - 2026-03-27

- Add org policy packs system for enterprise-level permission, MCP, hook, and constraint overrides.
- Add `0dai apply-policy` command to install org packs into target projects.
- Ship `enterprise-default` example pack with security-hardened permissions and deployment gates.
- Org packs generate `ai/manifest/org-policy.json` for agent-readable policy state.
- Wire org pack application into `sync` pipeline automatically.

## v0.1.16 - 2026-03-27

- Replace hardcoded migration case with chain-based migration runner that discovers scripts automatically.
- Support multi-step migration chains (e.g., 0.1.0 → 0.1.1 → 0.1.16) via BFS graph traversal of `bootstrap/migrations/`.
- Add `0.1.1_to_0.1.15.sh` migration for projects upgrading from early versions.
- Update `CURRENT_AI_VERSION` to track actual release version.
- Add smoke test for migration chain verification.

## v0.1.15 - 2026-03-27

- Move stack detection to weighted pattern scoring with `match_primary` (3x weight), `match_any` (1x weight), and `priority` tie-breaking.
- Add detection smoke tests verifying FastAPI beats generic Python and Go is correctly identified.
- Update all 11 detector YAMLs with primary markers and priority values.

## v0.1.14 - 2026-03-27

- Add React Native stack layout, detector, and stack pattern to complete all planned first-class stacks.
- Add release automation workflow triggered by version tags with validation gate and GitHub Release creation.
- Add `CONTRIBUTING.md` with branch naming, commit conventions, stack addition checklist, and release process.
- Add roadmap guardian agent and consistency checker with 58+ automated cross-file alignment checks.
- Polish foundation: fix devcontainer JSON syntax, update README tree, sync bootstrap-spec, CI job dependencies.

## v0.1.13 - 2026-03-27

- Add first-class stack layouts for Go service, FastAPI, and data/ML workspace.
- Add stack detection patterns (`go_service.yaml`, `fastapi.yaml`, `data_ml.yaml`) so new stacks are recognized during `init-existing`.
- Update `layout_for_stack()` routing and extend smoke test coverage for all three new stacks.

## v0.1.12 - 2026-03-26

- Add `ai/manifest/commands.yaml` so command execution policy becomes part of the canonical AI layer.
- Add `0dai doctor` to interpret project, environment, command-tier, and native output state for operators and agents.
- Extend validation and smoke coverage so execution policy manifests and doctor diagnostics are part of the supported foundation path.

## v0.1.11 - 2026-03-26

- Add `ai/manifest/environment.yaml` so 0dai can model execution context, available CLIs, capabilities, and constraints alongside project structure.
- Extend stack and command heuristics for an ops-dashboard style repository discovered during dogfooding.
- Update validation so environment manifest drift is part of the foundation path, not an afterthought.

## v0.1.10 - 2026-03-25

- Add a GitHub auto-intake step that can turn prepared intake summaries into triage-ready issues.
- Wire the intake creator into CI and telemetry paths with safe repository-variable guards.
- Extend the knowledge loop from artifacts and summaries into governance-ready GitHub objects.

## v0.1.9 - 2026-03-25

- Add a knowledge-uploader MVP that prepares GitHub-native intake summaries from aggregated experience reports.
- Wire the uploader into Docker telemetry mode so `0dai` has a first path from local experience artifacts toward issue/discussion intake preparation.
- Keep the knowledge loop moving from event capture and promotion toward governance-ready intake artifacts.

## v0.1.8 - 2026-03-25

- Make `0dai` the default user-facing CLI while keeping explicit aliases and backward-compatible shims.
- Align logs, runtime entrypoints, workflow artifact names, CI template names, and documentation around the `0dai-` prefix model.
- Keep validation and smoke coverage consistent with the new default command identity.

## v0.1.7 - 2026-03-25

- Make `0dai` the primary user-facing CLI while keeping `0dai-repo`, `0dai-task`, and legacy shims for compatibility.
- Align logs, docs, runtime entrypoints, workflow artifact names, and CI template names with the `0dai` prefix.
- Keep validation and smoke coverage consistent with the new default command identity.

## v0.1.6 - 2026-03-25

- Add `ai-task` as the standard local wrapper for writing normalized experience events into `ai/experience/outbox` while running commands.
- Add CI-facing experience aggregation with `scripts/aggregate_experience.py` and GitHub Actions artifact upload.
- Remove deprecated UTC timestamp usage in `ai-task` and keep validation/smoke coverage aligned with the expanded knowledge loop.

## v0.1.5 - 2026-03-25

- Integrate the stronger Docker workspace starter pattern into the repository with isolated runner mode, OpenCode web profile support, tool diagnostics, sample configs, and environment scaffolding.
- Keep the trusted/untrusted runtime contract while making the container layer much closer to a practical daily and CI-ready developer experience.

## v0.1.4 - 2026-03-25

- Integrate a stronger Docker runtime starter pattern with isolated runner mode, tool checks, example configs, and environment scaffolding.
- Add the `promote` command to complete the first executable two-step knowledge flywheel: `harvest -> promote`.
- Keep validation and smoke coverage aligned with the expanded runtime and experience workflow.

## v0.1.3 - 2026-03-25

- Add the first executable knowledge flywheel workflow with `harvest` and `promote` commands.
- Add Docker runtime hardening with trusted/untrusted bootstrap modes, `.dockerignore`, and runtime secret scaffolding.
- Strengthen the operational model around applied locks, experience handling, and containerized project execution.

## v0.1.2 - 2026-03-25

- Move native output rendering to canonical sources in `ai/templates/*` instead of using upstream root templates as the primary source.
- Add `bootstrap/native_output_map.json` as an explicit canonical-to-native routing layer for bootstrap generation.
- Reduce `templates/root/*` to a minimal compatibility bridge with only remaining shim artifacts.
- Keep validation and smoke coverage aligned with the cleaned internal architecture.

## v0.1.1 - 2026-03-25

- Reframe ZeroDayAI around a canonical `ai/` generation layer that emits native Codex, Claude Code, and OpenCode project files.
- Add manifest-driven bootstrap outputs with `ai/manifest/project.yaml`, `ai/manifest/discovery.json`, and `ai/manifest/init-report.md`.
- Add native Claude rules, hooks, agents, Codex agents, and shared skills outputs for more realistic multi-tool repository initialization.
- Preserve existing `AGENTS.md` and `.claude/CLAUDE.md` via managed block merging instead of replacing user-owned instructions.
- Add version-aware sync with `ai/VERSION` and explicit migration support for `0.1.0 -> 0.1.1`.

## v0.1.0 - 2026-03-25

- Bootstrap the `ZeroDayAI` baseline for Codex CLI, Claude Code, and OpenCode.
- Add safe project-local AI layer installation for existing and greenfield repositories.
- Ship shared prompts, playbooks, hooks, stack patterns, and root agent config templates.
- Add stack layouts for `flutter`, `backend-api`, `nextjs`, `python-service`, and `fullstack-monorepo`.
- Add upstream smoke testing and template validation for release safety.
