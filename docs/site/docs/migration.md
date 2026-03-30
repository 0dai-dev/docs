# Migrating from Manual CLAUDE.md / AGENTS.md

If you're already maintaining `CLAUDE.md`, `AGENTS.md`, or similar config files by hand, this guide shows you how to adopt 0dai without losing any of your existing content.

## Before: The Manual Maintenance Problem

Without 0dai, teams maintain a separate configuration file for each AI agent CLI they use:

- `CLAUDE.md` — instructions for Claude Code
- `AGENTS.md` — instructions for Codex
- `GEMINI.md` — instructions for Gemini CLI
- (and more as new agents arrive)

These files drift out of sync. A decision captured in `CLAUDE.md` never makes it to `AGENTS.md`. Onboarding instructions get updated in one file but not the others. Over time, each agent gets a subtly different picture of your project.

0dai solves this by managing a single source of truth and rendering agent-specific files from it — while preserving everything you've already written.

---

## Step 1: Backup Your Existing Config Files

Before running any 0dai commands, make copies of your existing files:

```bash
cp CLAUDE.md CLAUDE.md.bak
cp AGENTS.md AGENTS.md.bak
```

This is a precaution. 0dai will not delete your content, but it's good practice before any migration.

---

## Step 2: Run `0dai init-existing`

Point 0dai at your project root:

```bash
0dai init-existing --target .
```

This command inspects your project, reads your existing config files, and sets up the 0dai directory structure alongside what you already have.

If your project has a non-standard layout, pass the explicit path:

```bash
0dai init-existing --target /path/to/your/project
```

---

## Step 3: What 0dai Generates

After `init-existing` runs, you'll find the following new files and directories:

```
ai/
  manifest.json          # Project identity, stack, team settings
  sessions/
    active.json          # Session Roaming state (see session-roaming.md)
    history/             # Archived completed sessions
  knowledge/             # Harvested experience and decisions
  bulletins/             # Team-shared updates and announcements
  personas/              # Agent persona overrides
  stacks/                # Custom stack definitions
.0dai/
  config.json            # Local CLI configuration
```

Your existing `CLAUDE.md` and `AGENTS.md` files are left in place.

---

## Step 4: How Your Existing CLAUDE.md Is Preserved

0dai uses **managed blocks** to inject its generated content into your existing files. A managed block looks like this:

```markdown
<!-- 0dai:managed:start -->
...generated content...
<!-- 0dai:managed:end -->
```

Everything outside a managed block is yours and will never be touched. 0dai only updates content within its own blocks on each `sync`.

If 0dai cannot locate a suitable place to insert a managed block (for example, if your file has an unusual structure), it writes its output to a `.generated` fallback file instead:

- `CLAUDE.md` stays untouched
- `CLAUDE.generated.md` receives 0dai's additions

You can then manually merge the two, or reference `.generated.md` in your own file.

---

## Step 5: Commit and Verify

Add the new `ai/` and `.0dai/` directories to version control:

```bash
git add ai/ .0dai/ CLAUDE.md AGENTS.md
git commit -m "migrate to 0dai"
```

Then run the doctor to confirm everything is wired up correctly:

```bash
0dai doctor
```

The doctor checks:

- Manifest validity
- Agent file sync status
- Session state consistency
- MCP server reachability (if configured)
- Known stack detection

A healthy output looks like:

```
[ok] manifest valid
[ok] CLAUDE.md synced
[ok] AGENTS.md synced
[ok] stack detected: Node.js / TypeScript
[ok] no drift detected
```

Fix any warnings before treating the migration as complete.

---

## FAQ

**Will my custom CLAUDE.md be overwritten?**

No. Managed blocks preserve your content. 0dai only writes within `<!-- 0dai:managed:start -->` and `<!-- 0dai:managed:end -->` delimiters. Everything you've written outside those delimiters is untouched on every `sync`.

**What if I don't have an AGENTS.md yet?**

0dai will create one, populated with the content it generates from your manifest. You can then add your own content outside the managed blocks.

**Can I go back to managing files manually?**

Yes. Run `0dai sync --eject` to remove all managed blocks and leave plain Markdown files that you can maintain by hand. Your content is preserved; only 0dai's injected sections are removed.

**Does 0dai commit anything automatically?**

No. 0dai never runs `git commit` on your behalf. All file changes are staged for you to review and commit yourself.

**What if my project uses a monorepo?**

Run `init-existing` once per package that has its own AI agent context. Each subdirectory gets its own `ai/` directory and manifest. A root-level manifest can declare the workspace structure.
