# MCP Tools Reference

0dai exposes 54 MCP (Model Context Protocol) tools that agents use to interact with the AI layer. Tool availability depends on your plan.

## Plan access

| Plan | Tools available | Access level |
|------|----------------|--------------|
| **Free** | ~20 tools | Read-only |
| **Pro** | All 54 tools | Read + write |
| **Team** | All 54 tools | Read + write + admin |

## Tool categories

### Project health

| Tool | Plan | Description |
|------|------|-------------|
| `get_project_health` | Free | Overall status: version, stack, manifests, experience stats |
| `get_project_health_multi` | Free | Health across multiple projects |
| `get_maturity_score` | Free | AI layer completeness score (0-100) |
| `get_discovery` | Free | Auto-detected stack, frameworks, languages |
| `get_environment` | Free | Runtime environment details |

### Manifests and config

| Tool | Plan | Description |
|------|------|-------------|
| `get_project_manifest` | Free | Project metadata (name, stack, team, goals) |
| `get_codebase_map` | Free | File tree, entry points, dependency graph |
| `get_commands` | Free | Available build/test/lint/dev commands |
| `get_specs` | Free | Structured requirements for features |
| `create_spec` | Pro | Create a new spec document |
| `get_custom_stacks` | Free | Custom stack definitions |

### Experience and learning

| Tool | Plan | Description |
|------|------|-------------|
| `search_experience` | Free | Find prior learnings by keyword (TF-IDF ranked) |
| `record_experience` | Pro | Log outcomes for the experience flywheel |
| `score_candidates` | Free | Evaluate experience candidates for promotion |
| `get_prompt_history` | Free | View past prompts and their outcomes |

### Swarm and orchestration

| Tool | Plan | Description |
|------|------|-------------|
| `swarm_delegate` | Pro | Create a task for another agent |
| `swarm_run` | Pro | Execute queued swarm tasks |
| `get_swarm_status` | Free | Check task queue/active/done counts |
| `watch_tasks` | Pro | Stream task progress in real time |
| `run_task` | Pro | Execute a single task |
| `get_orchestration` | Free | Current orchestration config |
| `get_activity_feed` | Free | Unified timeline of all changes |

### Graph and knowledge

| Tool | Plan | Description |
|------|------|-------------|
| `get_project_graph` | Free | Read the local knowledge graph |
| `get_knowledge_base` | Free | Curated knowledge entries |
| `update_decision` | Pro | Record an architectural decision |
| `get_working_group_profiles` | Free | Agent capability profiles |
| `get_working_group_history` | Free | Past working group deliberations |
| `working_group_deliberate` | Pro | Start a multi-agent deliberation |
| `working_group_research` | Pro | Collaborative research task |

### Compliance and security

| Tool | Plan | Description |
|------|------|-------------|
| `get_compliance_report` | Free | SOC2/ISO27001 evidence mapping |
| `scan_secrets` | Free | Detect leaked credentials in ai/ layer |
| `get_audit_log` | Free | Chronological audit trail |
| `get_org_policy` | Free | Organization-level policies |
| `get_role_policy` | Free | What this agent role is allowed to do |
| `check_approval` | Free | Verify if a command/action is pre-approved |

### Sessions and state

| Tool | Plan | Description |
|------|------|-------------|
| `get_session` | Free | Retrieve a saved session |
| `save_session` | Pro | Save handoff notes for the next agent |
| `get_wal` | Free | Write-ahead log for crash recovery |
| `undo_mutation` | Pro | Revert a prior write operation |

### Agent management

| Tool | Plan | Description |
|------|------|-------------|
| `get_agent_teams` | Free | Configured agent team roster |
| `get_model_ratings` | Free | Performance ratings by model |
| `get_personas` | Free | Agent persona definitions |
| `get_plugins` | Free | Installed plugins |
| `get_registry` | Free | Plugin registry |

### Feedback and telemetry

| Tool | Plan | Description |
|------|------|-------------|
| `submit_feedback` | Pro | Report quality/usability scores |
| `get_telemetry_summary` | Free | Usage and performance metrics |
| `get_bulletins` | Free | Security advisories and cross-project learnings |

### Multi-project

| Tool | Plan | Description |
|------|------|-------------|
| `list_projects` | Free | All projects in the workspace |
| `get_portfolio` | Free | Portfolio-level health dashboard |
| `get_federation` | Free | Cross-project federation config |
| `get_applied_lock` | Free | Active lock status |
| `check_conflicts` | Free | Detect conflicting changes across agents |
| `get_ai_version` | Free | Current AI layer version |
| `get_mcp_catalog` | Free | Full catalog of available MCP tools |
| `get_observability` | Free | Observability configuration |

## Usage from agents

Agents call MCP tools automatically when they have the 0dai MCP server connected. You do not need to invoke tools manually -- the agent framework handles discovery and invocation.

To verify which tools your agent can access:

```bash
0dai mcp catalog
```
