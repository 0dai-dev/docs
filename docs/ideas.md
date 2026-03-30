# Implementation Ideas

Generated from full project audit at v0.1.13. Prioritized by impact and feasibility.

## High Priority — Next Release Candidates

### 1. Release Automation Workflow
- Add `.github/workflows/release.yml` triggered by VERSION file change or git tag
- Auto-generate release from CHANGELOG.md section
- Publish GitHub Release with release-notes/ as body
- Run roadmap guardian as release gate
- **Why**: Eliminates manual release steps and prevents version drift

### 2. React Native Stack Layout
- Last remaining "Next" roadmap stack
- Follow existing pattern: `project_layouts/react-native/scaffold.sh` + `structure.md`
- Detector: match on `app.json`, `metro.config.js`, `android/`, `ios/`
- Scaffold: `src/screens/`, `src/navigation/`, `src/components/`, `src/services/`
- **Why**: Completes the "Next" roadmap item for stacks

### 3. Pattern-Driven Stack Scoring Enhancement
- Current `detect_stack()` uses simple file-exists counting
- Add weighted scoring: primary markers (high weight) vs secondary (low weight)
- Add `priority` field to detector YAML to break ties
- Handle overlapping detectors (e.g., FastAPI vs plain Python)
- **Why**: Prevents misdetection as project count grows; roadmap "Now" item

### 4. Contributor Workflow Guidance
- Add `CONTRIBUTING.md` with branch naming, commit message, and PR conventions
- Document the plan-act paradigm used in development
- Add pre-commit hook example for local validation
- **Why**: Roadmap "Next" item; enables team onboarding

## Medium Priority — Quality of Life

### 5. Unit Tests for Python Scripts
- Current testing: smoke test only (integration-level)
- Add pytest-based unit tests for `aggregate_experience.py`, `score_knowledge_intake.py`, `roadmap_guardian.py`
- Test edge cases: malformed JSON, empty directories, missing files
- **Why**: Audit revealed unprotected JSON parsing across 5 scripts

### 6. JSON Error Handling Hardening
- Wrap all `json.loads()` calls in try-except across scripts and bootstrap embedded Python
- Provide human-readable error messages with file paths
- Graceful degradation instead of stack traces
- **Why**: Audit found 12+ unprotected JSON parse sites

### 7. Dynamic Experience Expiration
- `harvest_experience.sh` line 70 has hardcoded `expires_at: 2026-09-25`
- Calculate dynamically: current date + configurable offset (default 6 months)
- Use `ODAI_EXPERIENCE_TTL_DAYS` env var for override
- **Why**: Current value becomes stale; time-sensitive bug

### 8. Changelog Automation
- Script that generates CHANGELOG entry from git log between tags
- Group by conventional commit prefix (feat:, fix:, chore:)
- Auto-update release-notes/ from CHANGELOG section
- **Why**: Roadmap "Next" item; reduces manual release overhead

## Lower Priority — Future Foundation

### 9. Org Policy Packs
- Allow per-org overrides: MCP defaults, hook policies, permission boundaries
- Load from `ai/packs/org-{name}.yaml` during init/sync
- Merge with defaults, don't replace
- **Why**: Roadmap "Later" item; needed for multi-team adoption

### 10. MCP Server Integration Profiles
- Pre-configured MCP server setups per stack (DB tools for backend, Figma for frontend, etc.)
- Template `.mcp.json` that adapts to detected stack
- **Why**: Makes MCP setup zero-config for common stacks

### 11. Graph/Code Analysis Integration
- Add optional static analysis profiles per stack
- Generate `ai/manifest/codebase-map.json` with module dependency graph
- Feed into agent context for better navigation
- **Why**: Roadmap "Later" item; improves agent effectiveness

### 12. Template Pack Registry
- Support mono-repo and poly-repo operating modes
- Allow external pack sources (git URL, local path)
- Version and lock external packs like dependency managers
- **Why**: Roadmap "Later" item; extensibility for ecosystem growth

## Ideas for Agent Roles

### 13. Pre-Release Auditor Agent
- Combines roadmap guardian + template validation + smoke tests
- Generates release readiness report
- Blocks release on any FAIL finding

### 14. Stack Compatibility Tester Agent
- Runs `init-new` for every stack in a clean environment
- Verifies resulting project structure against structure.md
- Detects regressions in scaffold scripts

### 15. Documentation Drift Detector Agent
- Compares code comments, function signatures, and CLI help text against docs
- Flags stale documentation automatically
- Could run as scheduled CI job

## Inspired by Omnara (YC S25) — Added 2026-03-27

### 16. 0dai MCP Server
- Expose ai/ layer as MCP tools: `get_project_manifest`, `get_codebase_map`, `get_org_policy`, `search_experience`, `get_commands`
- Any MCP-compatible agent (Claude Code, Cursor, Windsurf) can query project knowledge natively
- Use `fastmcp` Python framework for implementation
- No CLI wrapping — agents read knowledge through protocol, not subprocess
- **Why**: Omnara's CLI wrapper was fragile; MCP integration was durable. This is the highest-impact feature.

### 17. Web Dashboard (`0dai serve`)
- Lightweight FastAPI/uvicorn web UI for viewing manifests, codebase-map, org policy, experience stats
- Read-only view, no mutations — safe to expose
- Mobile-friendly responsive design
- Omnara proved mobile access to agent state is high-value
- **Why**: Developers want to check project AI state without terminal

### 18. Multi-Agent Personas
- Define roles (architect, qa, devops, security) in `ai/agents/personas/`
- Each persona has: system prompt additions, allowed commands (tier filter), focus paths, review checklist
- Agents select persona based on task type or user instruction
- Inspired by CrewAI role-based patterns and Omnara multi-agent management
- **Why**: One repo, multiple concerns, personalized agent behavior

### 19. Python SDK (`pip install zerodayai`)
- Programmatic access to ai/ layer: read manifests, query experience, apply policies
- Enables CI/CD integration, custom tooling, and third-party extensions
- API mirrors CLI commands: `zerodayai.detect(path)`, `zerodayai.sync(path)`, `zerodayai.analyze(path)`
- **Why**: Omnara had Python SDK; programmatic access enables ecosystem growth

### 20. Cross-Repo Knowledge Federation
- Link related repos (e.g., micro-services) via `ai/federation.yaml`
- Share experience, patterns, and anti-patterns across service boundaries
- `0dai federation sync` pulls knowledge from federated repos
- **Why**: Enterprise teams have 10-100 repos that should share AI learnings

## Trends & Market Context — 2026-2027

### Key Trends
- **MCP as universal integration standard** — 4133+ servers, 873% growth, Linux Foundation governance; being an MCP server = instant distribution
- **Agent SDK over CLI wrappers** — Claude Agent SDK, OpenAI Agents SDK; native SDKs are more stable than subprocess wrappers
- **Spec-driven development** — AWS Kiro uses specs to define what agents build; structured intent before execution
- **Multi-agent orchestration** — claude-squad, Agent Teams, JetBrains Central all enable parallel agents; config layer becomes critical
- **Agentic IDE convergence** — Cursor, Windsurf, Claude Code, Codex, Gemini CLI all converging on similar patterns
- **Knowledge persistence** — agents need persistent project context across sessions; 0dai's ai/ layer solves this
- **Market risk** — 40%+ agentic projects cancelled by 2027 (Gartner) due to unclear value; structured approach reduces risk

### Market Size
- AI agent market: $7.84B (2025) → $52.62B (2030), CAGR 46.3%
- 90% developers use AI at work (JetBrains 2026)
- MCP: 34.7K dependent projects

### Strategic Position
0dai occupies a unique position: **project knowledge infrastructure**. While others build agents (Claude Code, Codex), IDEs (Cursor, Windsurf), or orchestrators (CrewAI, LangGraph), 0dai provides the **canonical knowledge layer** that all agents read. Nearest enterprise analog: **Backstage Golden Paths** (30K+ stars, CNCF) — but for AI agents, not infrastructure.

### Additional Ideas from Research

#### 21. Gemini CLI Support
- Add as 4th supported agent CLI (96K+ stars, free 1000 req/day)
- Generate `.gemini/` config directory
- **Why**: Fastest growing CLI agent, free tier enables wide adoption

#### 22. Spec-Driven Development Templates
- Generate spec files (like AWS Kiro) defining what to build before how
- `ai/specs/` directory with structured intent documents
- Agents read specs to understand project goals, not just structure
- **Why**: AWS Kiro validates this pattern; structure intent → better agent output

#### 23. Agent Teams Config Generator
- Generate `.claude/agents/` configs for Claude Code Agent Teams
- Define lead + teammates with specific scopes and skills
- Template agent definitions for common team patterns (frontend + backend + qa)
- **Why**: Official Anthropic feature, 0dai is natural generator

#### 24. MCP Catalog Per Stack
- Recommend specific MCP servers per detected stack
- Flutter → firebase MCP, Go → kubernetes MCP, Python → database MCP
- Generate `.mcp.json` with stack-appropriate servers pre-configured
- **Why**: Reduces MCP setup from manual to zero-config

#### 25. Maturity Scorecards
- Extend `0dai doctor` to rate AI layer maturity (0-100 score)
- Check: manifests present, experience captured, policies applied, tests exist
- Output badge-ready score for README
- **Why**: Cortex IDP does this for infrastructure; 0dai can do it for AI layer
