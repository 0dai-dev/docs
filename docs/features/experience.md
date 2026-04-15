# Experience Pipeline -- Learning from Agent Work

The experience pipeline records what agents do, measures outcomes, and detects anti-patterns. Over time, 0dai learns which agents and models work best for different task types.

## Commands

### `0dai experience list`

Show recent experience events.

```bash
0dai experience list
# TIME        AGENT        TYPE       SCORE  COST
# 10m ago     Claude Code  task       82     $0.08
# 25m ago     Codex        task       91     $0.12
# 1h ago      Aider        fix        45     $0.03
# 2h ago      Claude Code  refactor   88     $0.15
```

Filter by agent or time range:

```bash
0dai experience list --agent codex --since 24h
```

### `0dai experience stats`

Aggregated success rates and costs by agent and model.

```bash
0dai experience stats
# AGENT        TASKS  AVG SCORE  AVG COST  SUCCESS RATE
# Claude Code  34     85         $0.11     94%
# Codex        21     79         $0.09     86%
# Aider        15     72         $0.04     80%
# Gemini       8      77         $0.06     88%
```

Break down by model:

```bash
0dai experience stats --by model
```

### `0dai experience warnings`

Show active anti-pattern alerts.

```bash
0dai experience warnings
# [WARN] Aider: 3 consecutive failures on test-writing tasks
# [WARN] Claude Code: cost escalation -- $0.45 avg last 5 tasks (was $0.11)
# [WARN] Codex: stuck on task #42 for 18 minutes
```

### `0dai experience dismiss`

Dismiss a warning by ID.

```bash
0dai experience dismiss warn_abc123
```

## Anti-pattern detection

The pipeline watches for these patterns automatically:

| Pattern | Trigger | Action |
|---------|---------|--------|
| **Repeated failures** | 3+ consecutive failures by same agent | Warning + suggest agent switch |
| **Cost escalation** | Cost > 3x rolling average | Warning + suggest model downgrade |
| **Stuck agent** | No progress for > 15 minutes | Warning + suggest task kill |
| **Low quality streak** | 3+ tasks scoring below 60 | Warning + suggest different agent |
| **Retry loops** | Same error appearing 3+ times | Warning + suggest manual intervention |

## How experience improves task routing

When you use `0dai run`, the swarm router checks experience data to pick agents:

1. Match task type (test, refactor, feature, fix) to agent success rates
2. Consider recent performance trends
3. Factor in cost efficiency
4. Avoid agents with active warnings for that task type

## Data storage

Experience data lives in `ai/experience/` as append-only JSON logs. Safe to commit.

```
ai/experience/
  events.json       # raw event log
  stats.json        # precomputed aggregates
  warnings.json     # active warnings
```
