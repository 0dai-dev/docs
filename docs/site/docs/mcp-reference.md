# MCP Tools Reference

0dai exposes its data and capabilities via a [Model Context Protocol](https://modelcontextprotocol.io) server. Start the server with `0dai serve`, then configure your AI agent to connect to it.

Tools are grouped by whether they read data, write data, or perform system operations.

---

## Read Tools

These tools return data without modifying state. Agents should call them at session start to load context.

| Tool | Description |
|---|---|
| `get_project_manifest` | Returns the full contents of `ai/manifest.json`, including project identity, stack, and team settings. |
| `get_codebase_map` | Returns a structural map of the codebase: directories, key files, and their relationships. |
| `get_commands` | Returns all commands defined in the manifest (build, test, lint, deploy, etc.) so agents know how to run the project. |
| `get_discovery` | Returns the auto-detected stack and tooling summary for the current project. |
| `get_project_health` | Returns a health score and list of issues for the current project based on manifest completeness and sync state. |
| `get_ai_version` | Returns the current 0dai CLI version and server protocol version. |
| `get_personas` | Returns all configured agent personas, including role definitions and behavioral overrides. |
| `get_bulletins` | Returns all active team bulletins — time-sensitive announcements that agents should surface to users. |
| `get_custom_stacks` | Returns any custom stack definitions registered in the project or org. |
| `get_applied_lock` | Returns the current applied lock state, indicating whether the manifest is locked against mutations. |
| `get_environment` | Returns environment context: detected CI system, OS, shell, and relevant environment variables. |
| `get_telemetry_summary` | Returns an aggregated summary of agent usage telemetry for the current project. |
| `get_registry` | Returns the current manifest registry state, including remote manifest versions and sync status. |
| `get_maturity_score` | Returns the project's AI-readiness maturity score across multiple dimensions (documentation, testing, security, etc.). |
| `search_experience` | Searches the harvested knowledge base for entries relevant to a given query string. |
| `get_federation` | Returns the federation configuration, showing how this project's manifest relates to other projects in the org. |
| `get_audit_log` | Returns recent entries from the immutable audit log for the current project. |
| `get_agent_teams` | Returns all agent team definitions installed in the project, including member roles and responsibilities. |
| `get_orchestration` | Returns the current orchestration plan if a multi-agent task is in progress. |
| `get_observability` | Returns observability data for recent agent sessions: latency, token usage, and error rates. |
| `get_prompt_history` | Returns recent prompt history for the current project, grouped by agent and session. |
| `get_wal` | Returns recent entries from the write-ahead log, showing pending and applied manifest mutations. |
| `get_activity_feed` | Returns the team activity feed: recent syncs, promotions, approvals, and session completions. |
| `get_role_policy` | Returns the role policy definitions that govern what each agent role is permitted to do. |
| `check_conflicts` | Checks for manifest conflicts between the local state and the remote registry. |
| `get_knowledge_base` | Returns the full contents of the team knowledge base, including decisions and shared context. |
| `get_compliance_report` | Returns the most recent compliance report for the current project. |
| `get_plugins` | Returns all installed 0dai plugins and their registered capabilities. |
| `scan_secrets` | Scans tracked files for sensitive data patterns (API keys, tokens, credentials) and returns any findings. |
| `check_approval` | Checks whether a pending manifest change has been approved by required reviewers. |
| `list_projects` | Returns a list of all projects registered under the current team or org. |
| `get_project_health_multi` | Returns health scores for multiple projects in a single call — useful for dashboard views. |
| `get_session` | Returns the current active session from `ai/sessions/active.json`, including goal, plan, files touched, and handoff notes. |

---

## Write Tools

These tools modify state. Agents should use them to record progress and decisions during a session.

| Tool | Description |
|---|---|
| `create_spec` | Creates or updates a project spec entry in the manifest based on provided requirements or descriptions. |
| `record_experience` | Stores a new experience entry (a pattern, solution, or lesson learned) in the project knowledge base. |
| `update_decision` | Records or updates an architectural decision, including rationale and alternatives considered. |
| `save_session` | Writes the current session state to `ai/sessions/active.json`, enabling handoff to another agent. |

---

## System Tools

These tools perform operations that affect agent behavior or candidate evaluation.

| Tool | Description |
|---|---|
| `score_candidates` | Evaluates a set of candidate approaches against the project's manifest constraints and returns a ranked score. |
| `undo_mutation` | Rolls back the most recent manifest mutation using the write-ahead log, restoring the previous state. |

---

## Connecting an Agent to the MCP Server

Start the server:

```bash
0dai serve
```

The server listens on `http://localhost:3000` by default. Configure your agent to use it:

**Claude Code (`CLAUDE.md`):**

```markdown
MCP server: http://localhost:3000
```

**Codex (`AGENTS.md`):**

```markdown
tools:
  mcp_server: http://localhost:3000
```

Once connected, agents can call any tool listed above during a session. The `get_project_manifest`, `get_commands`, and `get_session` tools are typically called automatically at session start via the SessionStart hook.

---

## Error Codes

| Code | Meaning |
|---|---|
| `NOT_FOUND` | The requested resource does not exist (e.g., no active session). |
| `LOCKED` | The manifest is locked and the requested write operation is not permitted. |
| `AUTH_REQUIRED` | The tool requires an authenticated session. Run `0dai auth login`. |
| `SCHEMA_ERROR` | The input to a write tool failed schema validation. |
| `CONFLICT` | The write operation conflicts with a concurrent change. Use `undo_mutation` or `check_conflicts` to resolve. |
