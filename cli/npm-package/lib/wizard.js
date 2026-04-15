/**
 * First-run interactive wizard for 0dai.
 *
 * Guides new users through: agent selection → auth → stack detection →
 * config generation → what's next. Safe to Ctrl+C at any step.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const readline = require("readline");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const AGENTS = [
  { id: "claude", name: "Claude Code" },
  { id: "codex", name: "Codex" },
  { id: "gemini", name: "Gemini CLI" },
  { id: "aider", name: "Aider" },
  { id: "opencode", name: "OpenCode" },
];

function isInteractive() {
  return Boolean(process.stdin.isTTY && process.stdout.isTTY);
}

function needsWizard(target) {
  return !fs.existsSync(path.join(target, "ai", "VERSION"));
}

function ask(rl, question, defaultVal) {
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      resolve(answer.trim() || defaultVal || "");
    });
  });
}

// ---------------------------------------------------------------------------
// Wizard steps
// ---------------------------------------------------------------------------

async function stepAgent(rl) {
  console.log("");
  console.log("  Welcome to 0dai! Let's set up your project.");
  console.log("");
  console.log("  Which AI coding agent do you use most?");
  console.log("");
  AGENTS.forEach((a, i) => {
    console.log(`    ${i + 1}) ${a.name}`);
  });
  console.log(`    6) Multiple / all of them`);
  console.log("");

  const choice = await ask(rl, "  Choose [1-6, default 6]: ", "6");
  const idx = parseInt(choice, 10);
  if (idx >= 1 && idx <= 5) {
    console.log(`  → Primary agent: ${AGENTS[idx - 1].name}`);
    return AGENTS[idx - 1].id;
  }
  console.log("  → All agents will be configured.");
  return "all";
}

async function stepAuth(rl) {
  console.log("");
  console.log("  0dai works in two modes:");
  console.log("");
  console.log("    Local mode  — generate configs offline, no account needed");
  console.log("    Cloud mode  — full graph, swarm, roaming, 56 MCP tools");
  console.log("");

  const answer = await ask(rl, "  Sign in now? [Y/n]: ", "y");
  if (answer.toLowerCase() === "n" || answer.toLowerCase() === "no") {
    console.log("  → Local mode. Sign in later: 0dai auth login");
    return "local";
  }
  console.log("  → Cloud mode. Run: 0dai auth login");
  console.log("  (Authentication happens after wizard completes.)");
  return "cloud";
}

async function stepDetect(rl, target) {
  console.log("");
  console.log("  Detecting project stack...");
  console.log("");

  const detected = [];
  const checks = [
    { file: "package.json", label: "Node.js" },
    { file: "next.config.js", label: "Next.js" },
    { file: "next.config.ts", label: "Next.js" },
    { file: "next.config.mjs", label: "Next.js" },
    { file: "tsconfig.json", label: "TypeScript" },
    { file: "pyproject.toml", label: "Python" },
    { file: "go.mod", label: "Go" },
    { file: "Cargo.toml", label: "Rust" },
    { file: "pubspec.yaml", label: "Flutter/Dart" },
    { file: "Gemfile", label: "Ruby" },
    { file: "prisma/schema.prisma", label: "Prisma" },
    { file: "docker-compose.yml", label: "Docker" },
    { file: "docker-compose.yaml", label: "Docker" },
    { file: ".github/workflows", label: "GitHub Actions" },
  ];

  const seen = new Set();
  for (const c of checks) {
    try {
      fs.statSync(path.join(target, c.file));
      if (!seen.has(c.label)) {
        detected.push(c.label);
        seen.add(c.label);
        console.log(`  ✓ ${c.label}`);
      }
    } catch {}
  }

  // Check package.json for framework hints
  try {
    const pkg = JSON.parse(fs.readFileSync(path.join(target, "package.json"), "utf8"));
    const deps = { ...pkg.dependencies, ...pkg.devDependencies };
    if (deps["react"] && !seen.has("React")) { detected.push("React"); seen.add("React"); console.log("  ✓ React"); }
    if (deps["vue"] && !seen.has("Vue")) { detected.push("Vue"); seen.add("Vue"); console.log("  ✓ Vue"); }
    if (deps["jest"] || deps["vitest"]) { const t = deps["vitest"] ? "Vitest" : "Jest"; if (!seen.has(t)) { detected.push(t); seen.add(t); console.log(`  ✓ ${t}`); } }
  } catch {}

  if (detected.length === 0) {
    console.log("  Could not auto-detect stack.");
    const manual = await ask(rl, "  What's your stack? (comma separated): ", "");
    if (manual) {
      detected.push(...manual.split(",").map(s => s.trim()).filter(Boolean));
    }
  } else {
    console.log("");
    const ok = await ask(rl, "  Looks right? [Y/n]: ", "y");
    if (ok.toLowerCase() === "n" || ok.toLowerCase() === "no") {
      const manual = await ask(rl, "  What's your stack? (comma separated): ", "");
      if (manual) {
        detected.length = 0;
        detected.push(...manual.split(",").map(s => s.trim()).filter(Boolean));
      }
    }
  }

  return detected;
}

function stepGenerate(target, agent, stack) {
  console.log("");
  console.log("  Generating AI agent configs...");
  console.log("");

  // Create minimal ai/ directory with generated configs
  const aiDir = path.join(target, "ai");
  const manifestDir = path.join(aiDir, "manifest");
  fs.mkdirSync(manifestDir, { recursive: true });

  // VERSION
  fs.writeFileSync(path.join(aiDir, "VERSION"), "3.10.1\n");

  // Discovery
  const discovery = {
    project_name: path.basename(target),
    stack: stack[0] || "unknown",
    detected_stack: stack,
    selected_agents: agent === "all" ? AGENTS.map(a => a.id) : [agent],
    detected_at: new Date().toISOString(),
    wizard: true,
  };
  fs.writeFileSync(
    path.join(manifestDir, "discovery.json"),
    JSON.stringify(discovery, null, 2) + "\n",
  );

  // Project YAML
  fs.writeFileSync(
    path.join(manifestDir, "project.yaml"),
    `plan: free\nname: ${discovery.project_name}\nstack: ${discovery.stack}\n`,
  );

  // CLAUDE.md
  const claudeMd = `# ${discovery.project_name}\n\nStack: ${stack.join(", ") || "unknown"}\nGenerated by 0dai wizard.\n\n## Commands\n\nSee ai/manifest/ for full configuration.\n`;
  fs.writeFileSync(path.join(target, "CLAUDE.md"), claudeMd);
  console.log("  ✓ CLAUDE.md");

  // AGENTS.md
  fs.writeFileSync(
    path.join(target, "AGENTS.md"),
    `# Agent Configuration\n\nProject: ${discovery.project_name}\nStack: ${stack.join(", ") || "unknown"}\n\nSee ai/manifest/ for configuration details.\n`,
  );
  console.log("  ✓ AGENTS.md");

  // ai/manifest files
  console.log("  ✓ ai/manifest/discovery.json");
  console.log("  ✓ ai/manifest/project.yaml");
  console.log("  ✓ ai/VERSION");

  const count = 5; // CLAUDE.md, AGENTS.md, discovery.json, project.yaml, VERSION
  console.log("");
  console.log(`  ${count} configs generated in ai/ directory.`);
  return count;
}

function stepNext(mode) {
  console.log("");
  console.log("  ✅ 0dai is ready!");
  console.log("");
  console.log("  Try these commands:");
  console.log("    0dai status     — see your project config");
  console.log("    0dai doctor     — check config health");
  if (mode === "cloud") {
    console.log("    0dai auth login — sign in for cloud features");
    console.log("    0dai sync       — refresh configs from server");
  }
  console.log("");
  console.log("  Pro features ($15/mo):");
  console.log("    0dai swarm run  — delegate tasks to AI agents");
  console.log("    0dai graph push — sync project intelligence");
  console.log("    0dai upgrade    — unlock all features");
  console.log("");
  console.log("  Docs: https://0dai.dev/docs");
  console.log("");
}

// ---------------------------------------------------------------------------
// Main wizard
// ---------------------------------------------------------------------------

async function runWizard(target) {
  if (!isInteractive()) {
    // Non-interactive: use defaults silently
    stepGenerate(target, "all", []);
    return { completed: true, interactive: false };
  }

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  // Clean exit on Ctrl+C — no partial state
  let aborted = false;
  rl.on("close", () => {
    if (!aborted) {
      aborted = true;
    }
  });

  try {
    const agent = await stepAgent(rl);
    if (aborted) return { completed: false };

    const mode = await stepAuth(rl);
    if (aborted) return { completed: false };

    const stack = await stepDetect(rl, target);
    if (aborted) return { completed: false };

    stepGenerate(target, agent, stack);
    stepNext(mode);

    return { completed: true, interactive: true, agent, mode, stack };
  } catch (err) {
    // Ctrl+C or other interrupt
    if (err && err.code !== "ERR_USE_AFTER_CLOSE") {
      console.error(`\n  Wizard error: ${err.message || err}`);
    }
    return { completed: false };
  } finally {
    rl.close();
  }
}

/**
 * Prompt user to run wizard if ai/ doesn't exist.
 * Returns true if wizard ran (or was declined), false to continue normal flow.
 */
async function maybeWizard(target, cmd) {
  if (!needsWizard(target)) return false;

  // init command goes straight to wizard
  if (cmd === "init") return false; // let cmdInit handle it with --no-wizard check

  if (!isInteractive()) return false;

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  try {
    const answer = await ask(rl, "\n  No 0dai config found. Run the setup wizard? [Y/n]: ", "y");
    rl.close();
    if (answer.toLowerCase() === "n" || answer.toLowerCase() === "no") {
      console.log("  Run '0dai init' when ready.\n");
      return true; // handled — don't continue to the command
    }
    await runWizard(target);
    return true;
  } catch {
    rl.close();
    return false;
  }
}

module.exports = {
  runWizard,
  maybeWizard,
  needsWizard,
  isInteractive,
  stepGenerate,
  AGENTS,
};
