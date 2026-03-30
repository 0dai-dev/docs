# Session Roaming

Session Roaming is the killer feature that no other AI agent CLI offers: seamless transfer of working context between different AI agents — without losing your place.

## The Problem: Context Loss When Switching Agents

Every developer has hit this wall. You start a bug fix in Claude Code, build up context — the goal, the files you've touched, the decisions you've made — and then you need to switch to a different agent (Codex for a quick refactor, Gemini for a code review). The moment you switch, that context is gone. You paste summaries, re-explain the problem, and waste time rebuilding what you already had.

Session Roaming solves this by persisting your working session to a shared file that any agent can read.

## How It Works

Sessions are stored in `ai/sessions/active.json` within your project. This file acts as a handoff baton — written by one agent, read by the next.

When a new agent session starts, the **SessionStart hook** checks for `ai/sessions/active.json`. If an active session is found, the agent is automatically briefed: goal, plan, files touched, key decisions, and handoff notes are all loaded into context before the first prompt is processed.

No manual copy-pasting. No re-explaining. The new agent picks up exactly where the last one left off.

## Commands

### Save a Session

```bash
0dai session save --summary "Fixing auth token expiry bug in middleware"
```

Persists the current session state to `ai/sessions/active.json`. Use `--summary` to add a human-readable description of where you are and what you're doing.

### Check Session Status

```bash
0dai session status
```

Displays the current active session: goal, agent history, files touched, and the last handoff note.

### Complete a Session

```bash
0dai session complete
```

Marks the session as done and archives it to `ai/sessions/history/`. Use this when a task is fully finished so the next session starts clean.

### View Session History

```bash
0dai session history
```

Lists archived sessions with timestamps and summaries. Useful for auditing what was done and by which agent.

## Example Workflow

**Scenario:** You're fixing a bug in an authentication middleware and want to use Claude Code for investigation and Codex for the actual code edit.

**Step 1 — Start in Claude Code**

You open Claude Code and begin investigating the bug. After identifying the root cause (token expiry not being checked in the refresh path), you save the session:

```bash
0dai session save --summary "Auth bug: refresh path skips expiry check — fix needed in middleware/auth.js line 84"
```

**Step 2 — Switch to Codex**

You open Codex in the same project directory. The SessionStart hook fires and detects `ai/sessions/active.json`. Codex is automatically briefed with your goal, the files you already looked at, and your handoff note.

You don't type a single word of re-explanation. Codex already knows.

**Step 3 — Continue the Work**

Codex makes the targeted edit. You verify it. You save again if you want another agent to review:

```bash
0dai session save --summary "Fix applied — needs review of edge case where token is null"
```

**Step 4 — Complete**

Once the fix is confirmed and merged:

```bash
0dai session complete
```

The session is archived. The next session in this project starts fresh.

## What Gets Transferred

Every session carries the following fields:

| Field | Description |
|---|---|
| `goal` | The high-level objective of the session |
| `plan` | Ordered list of steps planned or taken |
| `files_touched` | All files read or modified during the session |
| `key_decisions` | Important choices made and the reasoning behind them |
| `handoff_notes` | Free-form notes written for the next agent |
| `agent_history` | Which agents handled which parts of the session |

## MCP Tools

Session Roaming is also available to agents via the Model Context Protocol server.

### `get_session`

Returns the current active session from `ai/sessions/active.json`. Agents call this at startup to load prior context.

```json
{
  "tool": "get_session",
  "result": {
    "goal": "Fix auth token expiry bug",
    "files_touched": ["middleware/auth.js", "tests/auth.test.js"],
    "handoff_notes": "Refresh path identified — fix at line 84"
  }
}
```

### `save_session`

Writes an updated session state to `ai/sessions/active.json`. Agents call this when they've made meaningful progress and want to hand off cleanly.

```json
{
  "tool": "save_session",
  "args": {
    "summary": "Applied fix, added test coverage",
    "files_touched": ["middleware/auth.js", "tests/auth.test.js"]
  }
}
```
