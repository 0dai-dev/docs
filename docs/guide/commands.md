# CLI Commands

Full reference for every `0dai` command. Commands marked with a lock icon require a Pro plan.

## Core Commands

### init

Initialize the `ai/` configuration layer in your project.

```bash
0dai init [--dry-run] [--minimal]
```

| Flag | Description |
|---|---|
| `--dry-run` | Preview files that would be created |
| `--minimal` | Skip optional files, generate core config only |

### sync

Update the `ai/` layer to reflect current project state.

```bash
0dai sync [--dry-run] [--quiet]
```

| Flag | Description |
|---|---|
| `--dry-run` | Preview changes without writing |
| `--quiet` | Suppress output |

### detect

Show the auto-detected stack (languages, frameworks, package managers).

```bash
0dai detect
```

### doctor

Check project health, agent CLI availability, and credentials.

```bash
0dai doctor [--drift]
```

| Flag | Description |
|---|---|
| `--drift` | Include configuration drift report |

### validate

Validate `ai/` layer completeness and correctness.

```bash
0dai validate
```

### status

Show project maturity score, swarm state, and session info.

```bash
0dai status
```

### run

Decompose a goal into swarm tasks, auto-routed to the best agent.

```bash
0dai run <goal> [--dry-run]
```

| Flag | Description |
|---|---|
| `--dry-run` | Show planned tasks without executing |

This command requires a Pro plan.

## Knowledge Commands

### graph

Manage the project knowledge graph.

```bash
0dai graph push     # Upload local graph to server
0dai graph pull     # Download server graph and merge locally
0dai graph status   # Show local graph stats and sync state
```

`graph push` uploads edges on Pro (nodes only on Free). `graph pull` requires Pro.

### experience

View structured experience events recorded by agents.

```bash
0dai experience list    # Show recent experience events
0dai experience stats   # Success and cost stats by agent/model/type
```

### reflect

Session reflection showing what was delivered, delegation rate, and blockers.

```bash
0dai reflect
```

### report

Generate and submit project reports.

```bash
0dai report preview    # Preview privacy-safe project report
0dai report push       # Send report to 0dai (with offline queue)
0dai report status     # Show last report, queue, and auto-report status
```

`report push` requires a Pro plan.

## Swarm Commands

### swarm

Multi-agent task orchestration and delegation.

```bash
0dai swarm status           # Show task queue and delegation state
0dai swarm webhook add      # Register a webhook (fires on task done/failed)
0dai swarm webhook list     # Show registered webhooks
0dai swarm webhook test     # Send test ping to a webhook URL
```

Swarm commands require a Pro plan.

### watch

Live task monitor showing queue, active, and recently completed tasks.

```bash
0dai watch [--interval N]
```

| Flag | Description |
|---|---|
| `--interval N` | Refresh interval in seconds |

### metrics

Effectiveness score covering adoption funnel, sessions, and delegation.

```bash
0dai metrics
```

### audit

Scan `ai/` directory and agent configs for leaked secrets.

```bash
0dai audit
```

## Account Commands

### auth

Manage authentication.

```bash
0dai auth login     # Authenticate via device code flow
0dai auth logout    # Remove stored credentials
0dai auth status    # Show account info and usage
```

### activate

Manage plan activation.

```bash
0dai activate free      # Claim free activation license
0dai activate status    # Show activation and bound-project status
```

### portfolio

List all tracked projects with score, sessions, agents, and last activity.

```bash
0dai portfolio
```

### models

Show model ratings across providers.

```bash
0dai models [--fast | --balanced | --deep | --available]
```

| Flag | Description |
|---|---|
| `--fast` | Show models optimized for speed |
| `--balanced` | Show models balancing speed and quality |
| `--deep` | Show models optimized for quality |
| `--available` | Show only locally available models |

## Other Commands

### feedback

Submit feedback to the 0dai team.

```bash
0dai feedback push    # Send feedback to 0dai
```

### session

Save and resume session context for roaming across machines.

```bash
0dai session save     # Save current session for roaming
```

Session roaming requires a Pro plan.

### update

Update all installed agent CLIs to their latest versions.

```bash
0dai update [--dry-run]
```

| Flag | Description |
|---|---|
| `--dry-run` | Preview updates without installing |

### terminal

Launch an interactive agent session in a managed terminal.

```bash
0dai terminal [launch] [--tool <agent>]    # Start a session
0dai terminal list                          # List active sessions
0dai terminal attach <id>                   # Re-attach to a session
0dai terminal kill <id>                     # Kill a session
```

| Flag | Description |
|---|---|
| `--tool <agent>` | Agent to launch: `codex`, `claude`, `gemini`, `opencode`, `aider` (default: `codex`) |

Pass a prompt after `--`:

```bash
0dai terminal --tool claude -- "fix the auth bug"
```

### redeem

Redeem a plan upgrade code.

```bash
0dai redeem <CODE>
```

## Pro Feature Summary

The following commands or subcommands require a Pro plan ($15/mo):

| Command | Pro requirement |
|---|---|
| `run` | Full command |
| `swarm` | Full command |
| `graph push` (edges) | Free pushes nodes only |
| `graph pull` | Full subcommand |
| `session save` | Full subcommand |
| `report push` | Full subcommand |
