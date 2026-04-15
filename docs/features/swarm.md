# Swarm -- Multi-Agent Task Delegation

> Plan required: **Pro** ($15/mo) or **Team**

Swarm decomposes a goal into parallel tasks and delegates them across your configured agents (Claude Code, Codex, OpenCode, Gemini, Aider, Qoder).

## Quick start

```bash
# Describe what you want -- 0dai breaks it into tasks and assigns agents
0dai run "Add OAuth2 login with Google and GitHub providers"

# Watch tasks execute in real time
0dai watch
```

## Commands

### `0dai run <goal>`

AI-powered goal decomposition. Analyzes your codebase, splits the goal into subtasks, picks the best agent for each, and queues them.

```bash
0dai run "Refactor the payment module and add Stripe webhooks"
# => Creates 4 tasks: schema migration, webhook handler, event processing, tests
```

### `0dai swarm status`

Shows queue, active, and completed task counts with per-task quality scores.

```
Queue: 2 | Active: 1 | Done: 5 | Failed: 0
Total cost: $0.42 | Avg quality: 87/100
```

### `0dai watch`

Live terminal UI. Streams agent output, task transitions, and quality scores as work happens.

```bash
0dai watch              # all tasks
0dai watch --task 12    # single task
```

### `0dai swarm webhook add|list|test`

Get notified when tasks complete or fail.

```bash
# Add a Slack webhook
0dai swarm webhook add https://hooks.slack.com/services/T00/B00/xxx

# List configured webhooks
0dai swarm webhook list

# Send a test payload
0dai swarm webhook test
```

## Quality scoring

Every completed task receives a quality score (0--100) based on:

- Test pass rate
- Lint/type-check results
- Code diff complexity
- Agent self-reported confidence

Scores below 60 trigger automatic review suggestions.

## Cost tracking

Each task logs token usage and estimated cost. View totals with:

```bash
0dai swarm status --costs
```

## Rate limits

| Plan | Tasks per day |
|------|--------------|
| Free | -- (swarm not available) |
| Pro  | 50 |
| Team | 200 |

## Example workflow

```bash
# 1. Run a goal
0dai run "Add full-text search to the blog"

# 2. Monitor progress
0dai watch

# 3. Check results
0dai swarm status

# 4. Review quality
0dai experience stats --last 1h
```
