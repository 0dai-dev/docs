# Show HN Launch Plan

## Hacker News

### Title
```
Show HN: 0dai – One config layer for 5 AI agent CLIs
```

### URL
```
https://github.com/0dai-dev/0dai
```

### Author's First Comment

```
Hi HN, I built 0dai because I use 3+ AI agents daily and got tired
of maintaining the same project knowledge in 5 different config formats.

The problem: Claude Code reads .claude/settings.json + CLAUDE.md,
Codex reads .codex/config.toml + AGENTS.md, OpenCode reads opencode.json,
Gemini reads .gemini/settings.json, Aider reads .aider.conf.yml.

Same architecture docs. Same command policies. Same team patterns. Five copies.

0dai generates all of them from one `ai/` directory:

  0dai init-existing --target .   # detects stack, creates ai/ layer
  0dai doctor --target .          # shows what agents know
  0dai sync --target .            # regenerates all native configs

Two features I haven't seen elsewhere:

1. Session Roaming — save your task context, switch to a different
   agent CLI, it auto-detects the session and picks up where you left off.
   Goal, plan, files touched, decisions — all transferred.

2. Experience Flywheel — capture what worked during development,
   promote patterns into team knowledge. Agents learn from your history.

It also ships an MCP server (43 tools) so agents can self-serve project
context without copy-pasting from docs.

Free tier: all core commands, all stacks, MCP server. No limits.
Team plan ($29/mo): shared dashboard, knowledge base, role-based access.

CLI runs locally, team features hosted at app.0dai.dev.
Your code never leaves your machine.

Genuinely curious: do you maintain configs for multiple AI agents?
Is this a real problem or am I over-engineering a niche pain?

Docs: https://docs.0dai.dev
Dashboard: https://app.0dai.dev
```

---

## Reddit

### r/ClaudeAI

**Title:** `I built a tool that generates CLAUDE.md and configs for 4 other AI agents from a single source of truth`

**Body:**
```
I use Claude Code + Codex + Gemini CLI. Each has its own config format.
I was maintaining the same project knowledge in 3 places.

So I built 0dai — one `ai/` directory that generates native configs for
all 5 agent CLIs. Run `init-existing`, it detects your stack (FastAPI,
Next.js, etc.), creates the canonical layer, and emits .claude/,
.codex/, .gemini/, .opencode/, .aider/ configs.

The killer feature: Session Roaming. Save context in Claude Code,
switch to Codex, it picks up where you left off. No re-explaining.

Free tier, no limits: https://github.com/0dai-dev/0dai
Docs: https://docs.0dai.dev

Does anyone else juggle multiple AI agent CLIs?
```

### r/LocalLLaMA

**Title:** `0dai: switch between Claude Code, Codex, Gemini, Aider without losing context (Session Roaming)`

**Body:**
```
Built a tool for multi-agent workflows. Your project knowledge lives
in one `ai/` directory. Native configs for each agent CLI are generated.

Session Roaming: start debugging in Claude Code, save session context,
switch to Aider — it auto-detects what you were doing and continues.

Experience Flywheel: capture what worked, promote it to team knowledge.
Agents learn from your history.

43 MCP tools, 9 stack templates.

https://github.com/0dai-dev/0dai
```

---

## Twitter/X Thread

```
I built 0dai — one config for 5 AI agent CLIs.

Problem: Claude Code, Codex, Gemini, OpenCode, Aider
each read different config files. Same project. Five formats.

Solution: one `ai/` directory → all configs generated.
Three commands. Free tier.

https://github.com/0dai-dev/0dai

---

The killer feature no one else has: Session Roaming.

Start a bug fix in Claude Code.
Save context: `0dai session save --summary "auth done, need tests"`
Switch to Codex.
It auto-detects the session. Picks up where you left off.

---

Experience Flywheel:
- Capture what worked → `harvest`
- Promote patterns → `promote`
- Next agent run → reads your team's learnings

Agents get smarter with every sprint.

---

v1.0 is out.

https://github.com/0dai-dev/0dai
https://docs.0dai.dev

Free for individuals. Team plan for $29/mo.
```

---

## Launch Checklist

- [x] Verify https://github.com/0dai-dev/0dai loads (landing page)
- [x] Verify https://docs.0dai.dev loads (documentation)
- [x] Verify https://app.0dai.dev loads (dashboard)
- [ ] Landing page has no GitHub/open-source references
- [ ] Submit Show HN post (URL: https://github.com/0dai-dev/0dai)
- [ ] Post first comment within 5 minutes
- [ ] Post to r/ClaudeAI (2 hours after HN)
- [ ] Post to r/LocalLLaMA (4 hours after HN)
- [ ] Post Twitter thread (same day)
- [ ] Monitor HN comments for 24 hours
