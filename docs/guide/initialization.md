# Initialization

The `0dai init` command scaffolds the `ai/` directory and generates native config files for each detected AI agent CLI.

## Basic Usage

```bash
cd your-project
0dai init
```

This detects your stack (languages, frameworks, package managers) and creates a full AI configuration layer.

## Options

### Minimal mode

Skip optional files and generate only the core manifest and agent configs:

```bash
0dai init --minimal
```

### Dry run

Preview what would be created without writing any files:

```bash
0dai init --dry-run
```

## What Gets Created

After running `0dai init`, your project will contain:

```
ai/
  manifest/
    project.yaml       # Project metadata (name, stack, goals)
    commands.yaml       # Command tier classification
    discovery.json      # Auto-detected stack information
  personas/            # Agent persona definitions
  playbooks/           # Task playbooks and workflows
CLAUDE.md              # Claude Code configuration
AGENTS.md              # Codex configuration
opencode.json          # OpenCode configuration
```

Additional agent-specific files may be generated depending on which CLIs are detected on your system.

## Local Mode vs Authenticated Mode

### Local mode (no account)

Run `0dai init` without logging in. The CLI detects your stack locally and generates config files. All Free-tier commands work without an account.

### Authenticated mode

Log in first to unlock Pro features:

```bash
0dai auth login
0dai init
```

Authenticated init syncs your project manifest with the 0dai server, enabling graph sync, session roaming, swarm orchestration, and reports.

## Re-initialization

Running `0dai init` in a project that already has an `ai/` directory will update existing files. To refresh your config after changing your stack or dependencies:

```bash
0dai sync
```

See [Configuration](configuration.md) for details on each generated file.
