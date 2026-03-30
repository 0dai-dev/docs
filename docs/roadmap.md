# Roadmap

## Delivered

### v0.1.x — Foundation

All v0.1.x milestones delivered (v0.1.0 through v0.1.19):
- 9 first-class stacks with weighted detection
- Chain-based migration framework
- Org policy packs, codebase analysis, mono/poly-repo packs
- Release automation, CONTRIBUTING.md, roadmap guardian (64 checks)

### v0.2.x — Production Readiness & MCP

- Pytest unit tests, JSON hardening, dynamic TTL, verbose flag, pre-sync backups
- MCP server (22 tools via FastMCP), web dashboard, configure wizard
- Multi-agent personas, custom stacks, Python SDK
- Semantic search (TF-IDF), audit logging, cross-repo federation
- Community stack registry (8 stacks), IDE configs (.vscode/, .idea/)

### v0.3.x — Ecosystem & Polish

- Maturity scorecards (0-100 score + grade)
- Gemini CLI as 4th supported agent
- Agent Teams config generator (6 persona-derived agents)
- MCP catalog per stack, spec-driven development templates
- SDK PyPI preparation, Backstage Software Template export
- Remote MCP server via Streamable HTTP

### v0.4.x — Automation & Intelligence

- Changelog automation from git log
- Code graph analysis (Python/JS/Go import graphs)
- Pre-release auditor (13 checks, 7 categories)
- Documentation drift detector (41 checks)
- Stack compatibility tester (9/9 stacks, ~195 checks)

---

## Planned

### v0.5.x — Write Operations & Agent Orchestration

**Тема:** Перевод MCP из read-only в полноценный инструмент + поддержка мультиагентных паттернов.

#### Now

- ~~Add MCP write tools: `create_spec`, `update_manifest`, `record_experience` — agents can modify the ai/ layer, not just read it.~~ (done in v0.5.0: 3 write tools + audit logging)
- ~~Add agent orchestration configs: generate `claude-squad` / `claude-swarm` compatible workspace definitions from ai/ layer.~~ (done in v0.5.1)

#### Next

- ~~Add observability templates: agent tracing configs for Langfuse, OpenTelemetry, LangSmith per stack.~~ (done in v0.5.4: 3 providers, 10 stacks)
- ~~Add experience auto-scoring: rank experience candidates by impact/frequency without manual review.~~ (done in v0.5.2: 6-dimension scoring, auto-promote)
- ~~Add Aider as 5th supported agent CLI (50K+ stars, git-native, BYOK).~~ (done in v0.5.3)

#### Later

- ~~Add write-ahead log for MCP mutations: undo/redo for ai/ layer changes.~~ (done in v0.5.6)
- ~~Add prompt versioning: track and diff system prompt changes over time in `ai/prompts/`.~~ (done in v0.5.5)

### v0.6.x — Team Collaboration

**Тема:** От одиночного разработчика к командной инфраструктуре.

#### Now

- ~~Add team dashboard with authentication: extend `0dai serve` with basic auth and multi-user view.~~ (done in v0.6.0: session auth, multi-page, activity/WAL views)
- ~~Add shared knowledge base: team-level experience sync (beyond repo federation).~~ (done in v0.6.1: centralized KB hub with push/pull/search)

#### Next

- ~~Add team activity feed: who changed what in ai/ layer, when, with what agent.~~ (done in v0.6.2: audit+WAL+experience+git aggregation)
- ~~Add role-based command policy: different team members get different command tier access.~~ (done in v0.6.3: 4 roles, per-user assignments)
- ~~Add conflict resolution for concurrent ai/ edits across branches.~~ (done in v0.6.4: managed auto-resolve, custom flagging)

#### Later

- Add Slack/Teams integration: notifications on experience promotion, policy changes, maturity drops.
- Add PR-aware ai/ layer: auto-suggest ai/ changes when PRs modify key architecture.

### v0.7.x — Enterprise Readiness & GTM

**Тема:** Готовность к корпоративному adoption + go-to-market.

#### Now

- ~~Add product landing page with pricing and onboarding.~~ (done in v0.7.0: `0dai site`, 3-tier monetization)
- ~~Add offline license validation and feature tiering.~~ (done in v0.7.0: free/team/enterprise)
- ~~Rewrite README with problem-first positioning.~~ (done in v0.7.0)
- ~~Add enterprise policy engine: centralized org policies pushed to all repos via `0dai policy-push`.~~ (done in v0.7.1: init/add-repo/push/status)
- ~~Add compliance reporting: generate SOC 2 / ISO 27001 evidence from audit logs and policies.~~ (done in v0.7.2: 8 evidence sources × 6 controls)
- ~~Add session roaming: transfer task context between agent CLIs (start in Claude, continue in Codex).~~ (done in v0.7.3: save/status/complete/history + MCP + hook)
- ~~Add cloud authentication with `0dai auth login` for team feature gating.~~ (done in v0.7.4: browser auth flow, 7-day offline TTL)

#### Next

- ~~Add SSO/SAML integration for `0dai serve` dashboard.~~ (done in v0.7.6: --sso flag, cloud token auth)
- ~~Add multi-tenant MCP server: one server serving multiple projects with isolation.~~ (done in v0.7.7: --multi flag, list_projects, per-project routing)
- ~~Add sensitive data scanner: detect secrets, PII, API keys in ai/ layer configs.~~ (done in v0.7.5: 14 patterns, auto-redact)

#### Later

- Add license compliance: scan dependencies against allowed/denied license lists.
- ~~Add change approval workflows: require human approval for ops-tier commands.~~ (done in v0.7.8)

### v0.8.x — Platform & Extensibility

**Тема:** 0dai как платформа с экосистемой.

#### Now

- ~~Add plugin system: extend 0dai with custom commands, checks, and generators via `ai/plugins/`.~~ (done in v0.8.0)
- ~~Add webhook hooks: trigger external systems on init/sync/audit events.~~ (done in v0.8.1)

#### Next

- Add marketplace for stacks, personas, playbooks: versioned, searchable, installable packages.
- Add custom agent framework: define project-specific agents with custom tools and permissions.
- Add template inheritance: stacks can extend other stacks (e.g., `fastapi-grpc` extends `fastapi`).

#### Later

- Add cloud-hosted MCP: managed 0dai server with team dashboard, no self-hosting.
- Add API gateway mode: 0dai as proxy between agents and protected resources.

### v0.9.x — Consolidation, User Accounts & Stabilization

**Тема:** Инфраструктурная честность — реальный auth, реальная оплата, реальный ЛК.

#### v0.9.0 — Consolidation
- ~~Tiered CLI help: 10 core commands by default, `--all` for full list.~~ (done in v0.9.0)
- API surface freeze: CLI, MCP, SDK signatures locked.
- Test suite expansion (50+ tests).
- MCP security review.

#### v0.9.1 — Real Auth
- Replace demo-mode auth with real backend (JWT, PKCE).
- User registration (email/password + GitHub OAuth).
- Real JWT signature validation.

#### v0.9.2 — User Account (Phase 1)
- ~~Account dashboard: profile, team management, repos, usage stats.~~ (done in v0.9.2)
- ~~`0dai team` CLI: invite, members, remove, role.~~ (done in v0.9.2)

#### v0.9.3 — User Account (Phase 2) + Billing
- Payment integration ($29/mo Team plan).
- Billing pages, invoices, API keys.
- Landing page wired to real Stripe Checkout.

#### v0.9.4 — Documentation & Migration
- ~~Documentation site (MkDocs at docs.0dai.dev).~~ (done in v0.9.4: 8 pages)
- ~~Migration guide from manual CLAUDE.md.~~ (done in v0.9.4)
- ~~Session Roaming guide.~~ (done in v0.9.4)

#### v0.9.5 — Hardening
- ~~Security: MCP path traversal protection, _safe_read().~~ (done in v0.9.5)
- ~~Error handling: graceful errors, --debug for stack traces.~~ (done in v0.9.5)
- ~~API stability doc, SDK version auto-sync.~~ (done in v0.9.5)

### v1.0 — General Availability

- ~~Stable API with semver guarantees.~~ (done: docs/api-stability.md)
- ~~Real user accounts with profile, team, billing.~~ (done: v0.9.1–v0.9.3)
- ~~Documentation site.~~ (done: v0.9.4, MkDocs 8 pages)
- SDK published to PyPI. (pending owner authorization)
- Three-pillar positioning: Five agents one config + Session Roaming + Experience Flywheel.

---

## Beyond v1.0

### v1.x — Intelligence & Learning

- ML-driven stack recommendations from codebase analysis.
- Predictive issue detection from experience patterns.
- Auto-generated playbooks from successful task sequences.
- Agent performance benchmarking across projects.

### v2.x — Agent Operating System

- Agent scheduling and orchestration (cron-like agent tasks).
- Multi-model routing: select best model per task type from experience data.
- Cross-project pattern mining: learn from all 0dai-managed repos.
- Agent marketplace: share and install trained agent configurations.

---

## Strategic Principles

1. **Knowledge > Control** — provide context, not control execution.
2. **Generate > Wrap** — generate native configs, never wrap CLI processes.
3. **Read-first, Write-careful** — MCP reads are safe, writes require audit trail.
4. **Project-scoped** — all state in ai/, nothing outside the repo boundary.
5. **Zero dependencies** — core tools use only Python stdlib.
6. **Non-destructive** — never overwrite user files, use .generated for conflicts.
7. **Privacy by default** — no data leaves the repo without explicit consent.

## Market Context

See `docs/competitive-analysis.md` for full landscape analysis.

**Strategic position:** 0dai is **project knowledge infrastructure** for AI agents — the canonical layer that Codex, Claude Code, OpenCode, and Gemini CLI all read. Nearest analog: Backstage Golden Paths (30K+ stars, CNCF), but for AI agent configuration rather than infrastructure.

**Market:** AI agent market $7.84B (2025) → $52.62B (2030). 90% developers use AI at work. MCP: 4133+ servers, 873% growth.
