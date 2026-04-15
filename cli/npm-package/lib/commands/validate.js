"use strict";
const shared = require("../shared");
const { log, fs, path, SUPPORTED_CLIS } = shared;

function cmdValidate(target) {
  const ai = path.join(target, "ai");
  if (!fs.existsSync(ai)) {
    log("No 0dai config found. Run: 0dai init");
    process.exitCode = 1;
    return;
  }
  const E = process.stdout.isTTY ? "\x1b[31m" : "";
  const G = process.stdout.isTTY ? "\x1b[32m" : "";
  const D2 = process.stdout.isTTY ? "\x1b[2m" : "";
  const R2 = process.stdout.isTTY ? "\x1b[0m" : "";

  const required = [
    "ai/VERSION", "ai/VERSION_SCHEMA",
    "ai/manifest/project.yaml", "ai/manifest/discovery.json",
    "ai/manifest/applied-lock.json", "ai/manifest/environment.yaml",
    "ai/manifest/commands.yaml",
  ];

  let agents = [];
  try {
    agents = JSON.parse(fs.readFileSync(path.join(ai, "manifest", "discovery.json"), "utf8")).selected_agents || [];
  } catch {}

  const agentFiles = Object.fromEntries(
    SUPPORTED_CLIS
      .filter((c) => c.agentFiles && c.agentFiles.length > 0)
      .map((c) => [c.name, c.agentFiles])
  );
  for (const agent of agents) {
    for (const f of agentFiles[agent] || []) required.push(f);
  }

  const FIX_HINTS = {
    "ai/VERSION": "run: 0dai init",
    "ai/VERSION_SCHEMA": "run: 0dai sync",
    "ai/manifest/project.yaml": "run: 0dai init",
    "ai/manifest/discovery.json": "run: 0dai init",
    "ai/manifest/applied-lock.json": "run: 0dai sync",
    "ai/manifest/environment.yaml": "run: 0dai sync",
    "ai/manifest/commands.yaml": "run: 0dai sync",
    "AGENTS.md": "run: 0dai sync",
    ".claude/settings.json": "run: 0dai sync",
    ".claude/CLAUDE.md": "run: 0dai sync",
    ".mcp.json": "run: 0dai sync",
    ".codex/config.toml": "install codex, then: 0dai sync",
    "opencode.json": "install opencode, then: 0dai sync",
  };

  const present = required.filter(f => fs.existsSync(path.join(target, f)));
  const missing = required.filter(f => !fs.existsSync(path.join(target, f)));

  for (const f of present) console.log(`  ${G}✓${R2} ${f}`);
  for (const f of missing) {
    const hint = FIX_HINTS[f] || "run: 0dai sync";
    console.log(`  ${E}✗${R2} ${f} ${D2}— ${hint}${R2}`);
  }

  if (missing.length) {
    console.log(`\n${E}${missing.length} missing${R2} / ${present.length + missing.length} total`);
    process.exitCode = 1;
  } else {
    log(`${G}validate ok${R2} — all ${present.length} required files present`);
  }
}

module.exports = { cmdValidate };
