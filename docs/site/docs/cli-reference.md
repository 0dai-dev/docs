# CLI Reference

All commands are invoked as `0dai <command> [options]`.

Run `0dai --help` for a top-level summary, or `0dai <command> --help` for command-specific options.

---

## Core Commands

These ten commands cover the daily workflow for any project using 0dai.

### `init-existing`

Migrate an existing project to 0dai without overwriting your current config files.

```bash
0dai init-existing --target .
```

Reads your existing `CLAUDE.md`, `AGENTS.md`, and similar files, then sets up the `ai/` directory structure alongside them. Uses managed blocks to inject 0dai content while preserving your custom text.

---

### `sync`

Regenerate agent config files from the current manifest state.

```bash
0dai sync
```

Run this after editing `ai/manifest.json`, adding bulletins, or changing personas. Updates `CLAUDE.md`, `AGENTS.md`, and any other registered agent files.

---

### `detect`

Auto-detect the project's tech stack and update the manifest.

```bash
0dai detect
```

Scans the project for package files, config files, and directory structure to identify languages, frameworks, and tooling. Writes results to `ai/manifest.json`.

---

### `doctor`

Check the health of the 0dai setup in the current project.

```bash
0dai doctor
```

Validates the manifest, checks agent file sync status, verifies stack detection, and reports any drift between the manifest and generated files. Use this after migrations or when something seems off.

---

### `validate`

Validate the manifest and all AI config files against their schemas.

```bash
0dai validate
```

Useful in CI to catch malformed manifests before they reach developers.

---

### `serve`

Start the local MCP (Model Context Protocol) server.

```bash
0dai serve
# or specify a port
0dai serve --port 8080
```

Exposes all 0dai data as MCP tools that AI agents can call during a session. Required for agents to use `get_session`, `save_session`, and other dynamic tools.

---

### `harvest`

Extract and store knowledge from the current codebase.

```bash
0dai harvest
```

Analyzes code, commit messages, and comments to build a searchable knowledge base in `ai/knowledge/`. Powers the `experience` MCP tool and `search` command.

---

### `promote`

Promote a local manifest change to the team registry.

```bash
0dai promote --message "Add payment service stack"
```

Requires auth. Pushes the current manifest state to the shared registry so other team members can pull it.

---

### `session`

Manage Session Roaming state.

```bash
0dai session save --summary "Description of where you are"
0dai session status
0dai session complete
0dai session history
```

See [Session Roaming](session-roaming.md) for full documentation.

---

### `mcp`

Inspect and test MCP tool availability.

```bash
0dai mcp list
0dai mcp call get_session
0dai mcp call get_project_health
```

`list` shows all available tools. `call` invokes a tool directly from the CLI for debugging.

---

## Account Commands

These commands require an active 0dai account. Run `0dai auth login` first.

### `auth`

Log in, log out, and manage credentials.

```bash
0dai auth login
0dai auth logout
0dai auth status
0dai auth token
```

### `team`

Manage team membership and invitations.

```bash
0dai team list
0dai team invite user@example.com
0dai team remove user@example.com
```

### `billing`

View subscription status and usage.

```bash
0dai billing status
0dai billing usage
```

---

## Additional Commands

| Command | Description |
|---|---|
| `search` | Search the harvested knowledge base |
| `configure` | Set local or global CLI configuration |
| `scan` | Scan for secrets and sensitive data in tracked files |
| `spec` | Generate or update a project spec from the manifest |
| `plugin` | Install, list, and remove 0dai plugins |
| `webhook` | Configure webhooks for manifest change events |
| `maturity` | Score the project's AI-readiness maturity level |

---

## Team Commands

These commands require auth and appropriate team permissions.

| Command | Description |
|---|---|
| `kb` | Manage the shared team knowledge base |
| `activity` | View team activity feed |
| `role-policy` | Define and enforce agent role policies |
| `conflicts` | Detect and resolve manifest conflicts across team members |
| `federation` | Configure cross-project or cross-org manifest federation |
| `approve` | Approve pending manifest changes in the review queue |

---

## Enterprise Commands

| Command | Description |
|---|---|
| `policy-push` | Push compliance policies to all projects in the org |
| `compliance` | Generate and export compliance reports |

---

## Internal / Advanced Commands

These commands are primarily used in automation, CI pipelines, or advanced debugging scenarios.

| Command | Description |
|---|---|
| `audit` | Query the immutable audit log |
| `doc-drift` | Detect documentation drift between manifest and actual code |
| `stack-test` | Test a custom stack definition against a target project |
| `changelog` | Generate a changelog from session history and decisions |
| `backstage-export` | Export manifest data to Backstage catalog format |
| `registry` | Interact with the manifest registry directly |
| `agent-teams` | Manage agent team definitions |
| `orchestrate` | Run a multi-agent orchestration plan |
| `score-experience` | Score the quality of harvested experience entries |
| `observability` | Query agent observability data |
| `prompt-history` | View prompt history for the current project |
| `wal` | Inspect the write-ahead log for manifest mutations |
| `report` | Generate a project health report |
| `pull-bulletins` | Pull the latest team bulletins from the registry |
| `apply-policy` | Apply a policy file to the current project |
| `task run` | Execute a named task defined in the manifest |
