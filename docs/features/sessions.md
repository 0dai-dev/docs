# Sessions -- Save and Resume Agent Context

Sessions let you pause work in one agent and resume it in another without losing context. The goal, plan, modified files, and key decisions travel with the session.

## Commands

### `0dai session save`

> Plan required: **Pro** or **Team**

Snapshot the current working context to the cloud.

```bash
0dai session save
# Session saved: sess_a1b2c3
# Contains: goal, plan (4 steps), 3 files touched, 2 decisions
```

### `0dai session resume`

> Plan required: **Pro** or **Team**

Restore a saved session. The receiving agent gets the full context injected into its prompt.

```bash
0dai session resume sess_a1b2c3
# Restored session from Claude Code (2 hours ago)
# Goal: Add rate limiting to the API gateway
# Progress: 2/4 steps complete
```

Resume the most recent session without specifying an ID:

```bash
0dai session resume --latest
```

### `0dai session list`

List all saved sessions. Available on all plans.

```bash
0dai session list
# ID            Agent         Age     Goal
# sess_a1b2c3   Claude Code   2h      Add rate limiting to API gateway
# sess_x9y8z7   Codex         1d      Fix flaky integration tests
# sess_m4n5o6   Aider         3d      Migrate DB schema to v2
```

## What transfers between agents

| Data | Description |
|------|-------------|
| **Goal** | The original task description |
| **Plan** | Step-by-step breakdown with completion status |
| **Files touched** | List of modified/created files with summaries |
| **Decisions** | Architectural choices made during the session |
| **Blockers** | What stopped progress, if anything |

## Typical workflow

```bash
# Start work with Claude Code
0dai run "Implement caching layer" --agent claude

# Claude gets stuck on a Redis config issue -- save and switch
0dai session save

# Resume in Codex which has better Redis knowledge
0dai session resume --latest --agent codex
```

## Storage

Sessions are stored remotely and expire after 30 days. Local session metadata is cached in `ai/sessions/`.
