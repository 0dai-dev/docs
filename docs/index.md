# 0dai Documentation

**0dai** is a CLI tool that creates a unified AI configuration layer for your codebase. One `ai/` directory powers six AI agent CLIs: Claude Code, Codex, OpenCode, Gemini, Aider, and Qoder.

- Version: 3.10.1
- Website: [0dai.dev](https://0dai.dev)
- npm: `@0dai-dev/cli`

## Table of Contents

### Getting Started

- [Installation](guide/installation.md) -- install, update, and uninstall the CLI
- [Initialization](guide/initialization.md) -- set up the `ai/` directory in your project
- [Configuration](guide/configuration.md) -- understand the `ai/` directory structure and config files

### Reference

- [CLI Commands](guide/commands.md) -- full reference for every command, flag, and subcommand

## Plans

| Feature | Free | Pro ($15/mo) |
|---|---|---|
| `init`, `sync`, `doctor`, `detect`, `validate` | Yes | Yes |
| Swarm task orchestration | -- | Yes |
| Graph sync (push/pull edges) | Nodes only | Full |
| Session roaming | -- | Yes |
| Reports (push) | -- | Yes |
| `run` (AI goal decomposition) | -- | Yes |
| Task limit | -- | 50/day |

## Supported Agents

| Agent | Config file generated |
|---|---|
| Claude Code | `CLAUDE.md` |
| Codex | `AGENTS.md` |
| OpenCode | `opencode.json` |
| Gemini | `GEMINI.md` |
| Aider | `.aider.conf.yml` |
| Qoder | `qoder.yaml` |
