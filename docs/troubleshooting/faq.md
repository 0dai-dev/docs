# Frequently Asked Questions

## What stays free forever?

The CLI core is permanently free: `init`, `sync`, `doctor`, `status`, `detect`, `validate`, support for up to 7 agents, 20 MCP tools, and full local mode.

## Can I use 0dai without an account?

Yes. `0dai init` works entirely locally with no account required.

## What happens when I downgrade from Pro?

Your data stays intact. Graph sync, session roaming, and other Pro features stop updating but nothing is deleted.

## How does 0dai handle my code?

0dai never reads your source code content. It only processes file names, directory structure, and metadata to build the project graph.

## Which AI agents are supported?

Claude Code, Codex, OpenCode (MiniMax/Kimi), Gemini, Aider, and Qoder.

## Can I self-host?

The CLI is open source and runs locally. Pro features require the 0dai server. For enterprise self-hosting, contact hello@0dai.dev.

## How do I add a new agent?

Run `0dai sync`. It automatically detects installed agent CLIs and configures them.

## What is the experience pipeline?

The experience pipeline records task outcomes (success, failure, duration, patterns) and uses them for learning and anti-pattern detection across sessions.

## How does graph context work?

0dai builds a project graph from your codebase structure and injects relevant context into agent prompts, so each agent gets the information it needs without reading your source code.
