<div align="center">

# 0dai — Zero Day AI

**AI agents that know your project.**

One brain for Claude Code, Codex, Gemini CLI, Aider, and OpenCode.
Context syncs. Intelligence grows. Agents get smarter.

[Website](https://0dai.dev) · [Get Started](#quickstart) · [Pricing](https://0dai.dev/pricing) · [Docs](https://0dai.dev/docs)

![npm version](https://img.shields.io/npm/v/@0dai-dev/cli)
![license](https://img.shields.io/badge/license-MIT-blue)

</div>

---

## What is 0dai?

0dai is a CLI that orchestrates AI coding agents. Instead of configuring each agent separately, 0dai generates and syncs native configs for all of them from one source.

**One command. Seven agents. Zero config drift.**

## Quickstart

```bash
npm install -g @0dai-dev/cli
cd your-project
0dai init
```

That's it. 0dai detects your stack and generates:
- `CLAUDE.md` — rules for Claude Code
- `AGENTS.md` — context for Codex
- `GEMINI.md` — Gemini CLI configuration
- `opencode.json` — OpenCode settings
- `.cursorrules` — Cursor editor rules

## How it works

```bash
# Initialize — detect stack, generate configs
0dai init

# Check health
0dai doctor

# See what's configured
0dai status

# Sync configs after project changes
0dai sync

# Full onboarding in one command
0dai quickstart
```

## Supported Agents

| Agent | Config Generated | Status |
|-------|-----------------|--------|
| Claude Code | CLAUDE.md | Supported |
| Codex (OpenAI) | AGENTS.md | Supported |
| Gemini CLI | GEMINI.md | Supported |
| Aider | .aider.conf.yml | Supported |
| OpenCode | opencode.json | Supported |
| Cursor | .cursorrules | Supported |
| Windsurf | .windsurfrules | Supported |

## Pro Features

Free tier covers config generation for all agents. [Pro ($19/mo)](https://0dai.dev/pricing) adds:

- **Project Graph** — AI memory that grows with your project
- **Swarm** — delegate tasks to multiple agents in parallel
- **Session Roaming** — save in Claude, resume in Codex
- **Experience Intelligence** — learn which model works best for what
- **Anti-Pattern Detection** — warnings before you repeat mistakes
- **55 MCP tools** (vs 20 free)

[Compare plans](https://0dai.dev/pricing)

## MCP Server

0dai includes an MCP server that gives AI agents project context:

```bash
# Start MCP server
0dai mcp start
```

20 tools available free, 55 with Pro.

## Local Mode

Works fully offline without an account:

```bash
0dai init  # generates configs from bundled templates
```

Sign in for server-generated configs and Pro features:

```bash
0dai auth login
0dai sync
```

## Links

- **Website:** [https://0dai.dev](https://0dai.dev)
- **npm:** [https://www.npmjs.com/package/@0dai-dev/cli](https://www.npmjs.com/package/@0dai-dev/cli)
- **Pricing:** [https://0dai.dev/pricing](https://0dai.dev/pricing)
- **Docs:** [https://0dai.dev/docs](https://0dai.dev/docs)
- **Issues:** [https://github.com/0dai-dev/0dai/issues](https://github.com/0dai-dev/0dai/issues)

## License

MIT — see [LICENSE](LICENSE)
