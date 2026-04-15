# Installation

## Requirements

- **Node.js** >= 16
- At least one supported AI agent CLI installed (Claude Code, Codex, OpenCode, Gemini, Aider, or Qoder)

## Install

```bash
npm install -g @0dai-dev/cli
```

## Verify

```bash
0dai --version
```

You should see output like `0dai v3.10.1`.

## Update

Use the built-in update command, which also updates any installed agent CLIs:

```bash
0dai update
```

Preview what would be updated without making changes:

```bash
0dai update --dry-run
```

Or update directly via npm:

```bash
npm update -g @0dai-dev/cli
```

## Uninstall

```bash
npm uninstall -g @0dai-dev/cli
```

This removes the CLI only. Your project's `ai/` directory and agent config files are left untouched.

## Next Steps

Run `0dai init` in your project to create the AI configuration layer. See [Initialization](initialization.md).
