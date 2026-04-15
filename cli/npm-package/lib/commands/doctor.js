"use strict";
const shared = require("../shared");
const { log, T, R, D, fs, path, spawnSync, findRepoScript, SUPPORTED_CLIS, recordExperienceEvent } = shared;

function cmdDoctor(target) {
  const ai = path.join(target, "ai");
  if (!fs.existsSync(ai)) { log("No 0dai config found. Run: 0dai init"); return; }
  let v = "?", stack = "generic";
  try { v = fs.readFileSync(path.join(ai, "VERSION"), "utf8").trim(); } catch {}
  try { stack = JSON.parse(fs.readFileSync(path.join(ai, "manifest", "discovery.json"), "utf8")).stack || "generic"; } catch {}

  const W = process.stdout.isTTY ? "\x1b[33m" : "";  // yellow
  const E = process.stdout.isTTY ? "\x1b[31m" : "";  // red
  const G = process.stdout.isTTY ? "\x1b[32m" : "";  // green
  const R2 = process.stdout.isTTY ? "\x1b[0m" : "";

  // --- ai/ layer checks ---
  const layerChecks = {
    "ai/VERSION":                  { path: path.join(ai, "VERSION"),                   sev: "error" },
    "ai/manifest/project.yaml":    { path: path.join(ai, "manifest", "project.yaml"),  sev: "error" },
    "ai/manifest/commands.yaml":   { path: path.join(ai, "manifest", "commands.yaml"), sev: "warn"  },
    "ai/manifest/discovery.json":  { path: path.join(ai, "manifest", "discovery.json"),sev: "warn"  },
    ".claude/settings.json":       { path: path.join(target, ".claude", "settings.json"), sev: "warn" },
    "AGENTS.md":                   { path: path.join(target, "AGENTS.md"),             sev: "warn"  },
  };

  // --- credentials checklist ---
  // Detect subscription-based auth (not just env API keys)
  const { execFileSync: _execFile } = require("child_process");
  function cliAuthed(cli) {
    try {
      if (cli === "claude") {
        const out = _execFile("claude", ["auth", "status"], { timeout: 5000 }).toString();
        try { return JSON.parse(out).loggedIn === true; } catch {}
        return out.includes("loggedIn");
      }
      _execFile("which", [cli], { timeout: 2000 });
      return true;
    } catch { return false; }
  }

  const claudeAuth = cliAuthed("claude");
  const codexAuth = cliAuthed("codex");

  const credChecks = [
    {
      name: "Claude Code",
      present: claudeAuth || !!process.env.ANTHROPIC_API_KEY,
      sev: (claudeAuth || process.env.ANTHROPIC_API_KEY) ? "ok" : "warn",
      hint: claudeAuth ? "authenticated via subscription" : "run: claude auth login (or set ANTHROPIC_API_KEY)",
    },
    {
      name: "Codex CLI",
      present: codexAuth || !!process.env.OPENAI_API_KEY,
      sev: (codexAuth || process.env.OPENAI_API_KEY) ? "ok" : "warn",
      hint: codexAuth ? "installed (uses ChatGPT subscription)" : "run: npm i -g @openai/codex (or set OPENAI_API_KEY)",
    },
    {
      name: "GITHUB_TOKEN",
      present: !!process.env.GITHUB_TOKEN,
      sev: process.env.GITHUB_TOKEN ? "ok" : "info",
      hint: "Optional — for gh CLI, PR creation",
    },
  ];

  // Stack-specific creds
  if (stack.includes("vercel") || stack.includes("next")) {
    credChecks.push({ name: "VERCEL_TOKEN", present: !!process.env.VERCEL_TOKEN, sev: process.env.VERCEL_TOKEN ? "ok" : "info", hint: "Optional — for Vercel deployments" });
  }
  if (stack.includes("aws") || stack.includes("lambda") || stack.includes("cdk")) {
    credChecks.push({ name: "AWS_ACCESS_KEY_ID", present: !!process.env.AWS_ACCESS_KEY_ID, sev: process.env.AWS_ACCESS_KEY_ID ? "ok" : "info", hint: "Optional — for AWS deployments" });
  }
  if (stack.includes("gcp") || stack.includes("firebase") || stack.includes("flutter")) {
    credChecks.push({ name: "GCP_CREDENTIALS", present: !!process.env.GOOGLE_APPLICATION_CREDENTIALS, sev: process.env.GOOGLE_APPLICATION_CREDENTIALS ? "ok" : "info", hint: "Optional — for GCP/Firebase" });
  }

  // --- run checks ---
  let errors = 0, warnings = 0;
  log(`v${v} | stack: ${stack}\n`);

  const missingConfigs = [];
  console.log("  ai/ layer:");
  for (const [name, { path: p, sev }] of Object.entries(layerChecks)) {
    const exists = fs.existsSync(p);
    if (!exists) {
      sev === "error" ? errors++ : warnings++;
      if (sev === "warn") missingConfigs.push(name);
    }
    const mark = exists ? `${G}ok${R2}` : sev === "error" ? `${E}MISSING${R2}` : `${W}missing${R2}`;
    console.log(`    ${mark.padEnd(22)} ${name}`);
  }
  // Explain WHY native configs are missing and what to do
  if (missingConfigs.length > 0) {
    const hasDiscovery = fs.existsSync(path.join(ai, "manifest", "discovery.json"));
    if (hasDiscovery) {
      console.log(`\n    ${W}→ Native configs not generated yet.${R2}`);
      console.log(`      ${D}Run: 0dai sync --target .${R2}`);
    } else {
      console.log(`\n    ${W}→ ai/ layer incomplete — run '0dai init' first.${R2}`);
    }
  }

  console.log("\n  credentials:");
  for (const c of credChecks) {
    if (!c.present && c.sev === "warn") warnings++;
    const mark = c.present ? `${G}ok${R2}` : c.sev === "warn" ? `${W}not set${R2}` : `${D}not set${R2}`;
    const hint = c.present && c.hint.includes("subscription") ? ` ${D}(${c.hint})${R2}` : (!c.present ? `\n      ${D}→ ${c.hint}${R2}` : "");
    console.log(`    ${mark.padEnd(22)} ${c.name}${hint}`);
  }

  // --- agent CLIs check ---
  const { execFileSync: _ef2 } = require("child_process");
  let updatesAvailable = 0;
  console.log("\n  agent CLIs:");
  for (const cli of SUPPORTED_CLIS) {
    let installed = false, ver = null;
    try {
      const out = _ef2(cli.bin, ["--version"], { timeout: 8000 }).toString().trim();
      installed = true;
      const m = out.match(/(\d+\.\d+\.\d+)/);
      if (m) ver = m[1];
    } catch {}

    if (installed) {
      let latest = null;
      if (cli.pkg) {
        try {
          const npmOut = _ef2("npm", ["view", cli.pkg, "version"], { timeout: 5000 }).toString().trim();
          if (npmOut.match(/^\d+\.\d+\.\d+$/)) latest = npmOut;
        } catch {}
      }
      if (latest && ver && latest !== ver) {
        updatesAvailable++;
        console.log(`    ${W}update${R2}  ${cli.name} ${D}${ver} → ${latest}${R2}`);
        console.log(`      ${D}→ ${cli.install}${R2}`);
      } else {
        console.log(`    ${G}ok${R2}      ${cli.name}${ver ? ` ${D}v${ver}${R2}` : ""}`);
      }
    } else {
      console.log(`    ${D}—${R2}       ${cli.name} ${D}not installed${R2}`);
      console.log(`      ${D}→ ${cli.install}${cli.altAuth ? ` (or ${cli.altAuth})` : ""}${R2}`);
    }
  }
  if (updatesAvailable) {
    console.log(`\n    ${D}Run: 0dai update${R2} to update all`);
  }

  // --- swarm check ---
  const swarmDir = path.join(ai, "swarm");
  const countDir = (d) => { try { return fs.readdirSync(d).filter(f => f.endsWith(".json")).length; } catch { return 0; } };
  const qCount = countDir(path.join(swarmDir, "queue"));
  const dCount = countDir(path.join(swarmDir, "done"));
  if (qCount || dCount) {
    console.log(`\n  swarm: ${qCount} queued, ${dCount} done`);
    if (qCount) console.log(`    ${W}→ run '0dai reflect' to review pending tasks${R2}`);
  }

  const summary = errors ? `${E}${errors} error(s)${R2}` : warnings ? `${W}${warnings} warning(s)${R2}` : `${G}healthy${R2}`;
  console.log(`\n  status: ${summary}`);
  recordExperienceEvent(target, {
    event_type: "doctor_run",
    agent: "cli",
    model: "0dai-cli",
    effort: "low",
    task: { goal: "doctor health check", task_type: "review", result: errors ? "failure" : "success", elapsed_seconds: 0, cost_usd: 0 },
    context: { stack, files_touched: 0, tests_passed: errors === 0 },
    quality: {
      lint_clean: errors === 0,
      no_secrets: true,
      commit_message_valid: true,
      acceptance_criteria_met: errors === 0,
      review_needed: warnings > 0,
    },
  });
  if (errors) process.exitCode = 1;

  // Drift summary (lightweight — full report via --drift flag)
  try {
    const ds = findRepoScript(target, "drift_detector.py");
    if (ds) {
      const dr = spawnSync("python3", [ds, "report", "--target", target],
                           { stdio: ["ignore", "pipe", "ignore"], encoding: "utf8", timeout: 5000 });
      if (dr.stdout && dr.stdout.includes("MODIFIED")) {
        const lines = dr.stdout.trim().split("\n");
        const driftCount = lines.filter(l => l.includes("MODIFIED") || l.includes("CONTRADICTS")).length;
        if (driftCount > 0) {
          console.log(`\n  config drift: ${driftCount} issue(s) — run: 0dai doctor --drift`);
        }
      }
    }
  } catch {}
}

module.exports = { cmdDoctor };
