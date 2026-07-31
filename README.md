<p align="center">
  <strong>0dai</strong><br>
  One config layer for seven AI coding agents.
</p>

<p align="center">
  <a href="https://0dai.dev">Website</a> ·
  <a href="https://0dai.dev/pricing">Pricing</a> ·
  <a href="https://0dai.dev/docs">Docs</a> ·
  <a href="https://github.com/0dai-dev/docs/issues">Issues</a>
</p>

---

## Public feedback

Report bugs, friction, and feature requests in **this repository's issues**:

**https://github.com/0dai-dev/docs/issues**

The 0dai product working monorepo is private. Do not expect to open issues on
`0dai-dev/0dai` / `iGeezmo/0dai` as an external user.

### Security

Security reports must **not** use public GitHub issues. Email **security@0dai.dev**
only (see the product `SECURITY.md` in the working monorepo). The disclosure
clock starts when mail reaches that address.

---

Your team uses Claude Code, Codex, Gemini, OpenCode, Aider, Qoder — each with its own config. 0dai generates all of them from a single `ai/` directory so your project knowledge stays in one place.

## Quick Start

```bash
npm install -g @0dai-dev/cli
cd your-project
0dai init
```

That's it. 0dai detects your stack, creates `ai/`, and generates `CLAUDE.md`, `AGENTS.md`, `opencode.json`, and the rest.

## What Happens

```
your-project/
├── ai/                    ← 0dai creates this
│   ├── manifest/          ← project metadata, commands, discovery
│   ├── personas/          ← agent role definitions
│   ├── playbooks/         ← reusable workflows
│   └── experience/        ← team knowledge (events → candidates → accepted)
├── CLAUDE.md              ← generated for Claude Code
├── AGENTS.md              ← generated for Codex
├── opencode.json          ← generated for OpenCode
├── .gemini/settings.json  ← generated for Gemini
└── .qoder/settings.json   ← generated for Qoder
```

Edit `ai/`, run `0dai sync`, all agent configs update. No manual copy-paste.

## Commands

| Command | What it does |
|---------|-------------|
| `0dai init` | Install ai/ layer into any project |
| `0dai sync` | Regenerate all agent configs from ai/ |
| `0dai doctor` | Check health, credentials, agent versions |
| `0dai status` | Project maturity, swarm quota, sessions |
| `0dai detect` | Show detected stack and available CLIs |
| `0dai run <goal>` | AI-decompose a goal into agent tasks |
| `0dai swarm status` | Task queue, active, done counts |
| `0dai graph status` | Project knowledge graph stats |
| `0dai experience list` | Recent agent task events |
| `0dai models` | Model ratings by speed/quality/cost |
| `0dai audit` | Scan for leaked secrets in configs |
| `0dai auth login` | Authenticate (device code flow) |

Run `0dai --help` for the full list.

## Supported Agents

| Agent | Config file | Status |
|-------|------------|--------|
| [Claude Code](https://claude.ai/code) | `CLAUDE.md`, `.claude/settings.json` | Full support |
| [Codex](https://openai.com/codex) | `AGENTS.md`, `.codex/config.toml` | Full support |
| [OpenCode](https://github.com/nichochar/opencode) | `opencode.json` | Full support |
| [Gemini CLI](https://github.com/google/gemini-cli) | `.gemini/settings.json` | Full support |
| [Aider](https://aider.chat) | `.aider.conf.yml` | Full support |
| [Qoder](https://qoder.ai) | `.qoder/settings.json` | Full support |

## Free vs Pro

| | Free | Pro ($19/mo) |
|---|------|-------------|
| init, sync, doctor, detect | ✅ | ✅ |
| 7 agent support | ✅ | ✅ |
| 20 MCP tools (read-only) | ✅ | ✅ |
| Stack detection (9 stacks) | ✅ | ✅ |
| Local mode (no account) | ✅ | ✅ |
| Swarm task delegation | — | ✅ 50/day |
| Graph sync (push/pull) | — | ✅ |
| Session roaming | — | ✅ |
| Report pipeline | — | ✅ |
| 58 MCP tools (full) | — | ✅ |
| Model routing | — | ✅ |

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  ai/ layer  │────▶│  0dai sync   │────▶│  CLAUDE.md   │
│  (source)   │     │  (generates) │     │  AGENTS.md   │
│             │     │              │     │  opencode.json│
│  manifest/  │     │  Detects:    │     │  .gemini/    │
│  personas/  │     │  - Stack     │     │  .qoder/     │
│  playbooks/ │     │  - CLIs      │     │  .aider.conf │
│  experience/│     │  - Team size │     └─────────────┘
└─────────────┘     └──────────────┘
```

0dai never reads your source code. It detects file names and structure, not content.

## Included Stacks

`nextjs` · `fastapi` · `python-service` · `go-service` · `flutter` · `react-native` · `fullstack-monorepo` · `backend-api` · `data-ml`

## Development

```bash
# Run tests
python3 -m pytest tests/ -q

# Web dev server
cd web && npm run dev

# CLI development
node cli/npm-package/bin/0dai.js --help

# Docker (full stack)
docker compose -f docker-compose.prod.yml up -d
```

## Links

- **Website:** [0dai.dev](https://0dai.dev)
- **Docs:** [0dai.dev/docs](https://0dai.dev/docs)
- **npm:** [@0dai-dev/cli](https://www.npmjs.com/package/@0dai-dev/cli)
- **Pricing:** [0dai.dev/pricing](https://0dai.dev/pricing)
- **License:** MIT
