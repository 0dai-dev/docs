# 0dai

One config layer for 5 AI agent CLIs — Claude Code, Codex, OpenCode, Gemini, Aider.

## Install

```bash
npm install -g @0dai-dev/cli
```

## Usage

```bash
cd your-project
0dai auth login
0dai activate free
0dai init       # detect stack, generate ai/ layer + native configs
0dai sync       # update after changes
0dai detect     # show detected stack
0dai doctor     # check health
0dai status     # maturity, swarm tasks, session
```

## What it does

`0dai init` and `0dai sync` are activation-first. They authenticate the user, require a free activation license, bind the project, then send only allowlisted project metadata (file names + package/build manifests) to the API and generate:

- `ai/` — manifests, personas, skills, playbooks, delegation policy
- `.claude/` — settings, agents, hooks, rules
- `.codex/` — config, agents
- `.gemini/` — settings, agents
- `.aider/` — config, agents
- `AGENTS.md`, `.mcp.json`

Your source code is never sent. Only file names and package/build manifests.

## Links

- Website: https://0dai.dev
- Docs: https://docs.0dai.dev
- API: https://api.0dai.dev
