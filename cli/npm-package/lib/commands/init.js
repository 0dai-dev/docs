"use strict";
const shared = require("../shared");
const {
  T, R, D, log,
  fs, path,
  VERSION, SUPPORTED_CLIS,
  apiCall, makeEnsureAuthenticated, ensureLicenseActivation,
  collectMetadata, buildProjectIdentity, registerProject,
  writeFiles, sendProjectHeartbeat, recordExperienceEvent,
} = shared;
const { cmdAuthLogin } = require("./auth");

const ensureAuthenticated = makeEnsureAuthenticated(cmdAuthLogin);

// bindProjectForCloud — binds project to cloud via /v1/projects/bind
async function bindProjectForCloud(target, metadata, identity) {
  const result = await apiCall("/v1/projects/bind", {
    ...identity,
    stack: identity.stack || "unknown",
  });
  if (result.error) {
    log(`error: ${result.error}`);
    if (result.hint) console.log(`  ${result.hint}`);
    process.exit(1);
  }
  return result.project || {
    project_id: identity.project_id,
    name: identity.project_name,
    stack: identity.stack || "unknown",
    binding_status: "bound",
  };
}

async function cmdInit(target, args = []) {
  const dryRun = args.includes("--dry-run");
  const minimal = args.includes("--minimal");
  const noWizard = args.includes("--no-wizard");

  if (fs.existsSync(path.join(target, "ai", "VERSION"))) {
    const v = fs.readFileSync(path.join(target, "ai", "VERSION"), "utf8").trim();
    log(`ai/ layer already exists (v${v}). Run '0dai sync' to update.`);
    return;
  }

  // Pre-check: verify init quota before starting wizard (avoid 10 min wizard → "limit reached")
  if (!dryRun) {
    try {
      const precheck = await apiCall("/v1/projects/precheck", {
        device_id: shared.deviceFingerprint(),
      });
      if (precheck.error && precheck.error.includes("limit")) {
        log(`${precheck.error}`);
        if (precheck.hint) console.log(`  ${D}${precheck.hint}${R}`);
        return;
      }
    } catch {}
  }

  // First-run wizard (unless --no-wizard or non-interactive)
  if (!noWizard && !dryRun && !minimal) {
    try {
      const { runWizard, isInteractive } = require("../wizard");
      if (isInteractive()) {
        const result = await runWizard(target);
        if (result.completed) {
          try {
            const ob = require("../onboarding");
            ob.trackFirstInit(target);
            ob.showWhatsNext(result.mode || "local", false);
          } catch {}
          return;
        }
      }
    } catch {}
  }

  const isTTY = process.stdout.isTTY;
  let spinner = null;
  if (isTTY) {
    try { spinner = require("@clack/prompts").spinner(); } catch {}
  }

  const metadata = collectMetadata(target);
  const { projectFiles, manifestContents, clis } = metadata;
  const authStatus = await ensureAuthenticated("init");
  const license = await ensureLicenseActivation();
  const identity = buildProjectIdentity(target, metadata);
  const boundProject = await bindProjectForCloud(target, metadata, identity);
  if (dryRun) log(`${D}dry-run: would generate ai/ layer (${projectFiles.length} files, ${clis.length} CLIs)${R}`);
  if (spinner) spinner.start(`${dryRun ? "[dry-run] " : ""}Generating ai/ layer (${projectFiles.length} files, ${clis.length} CLIs)...`);
  else if (!dryRun) log(`sending to API (${projectFiles.length} files, ${clis.length} CLIs)...`);
  const result = await apiCall("/v1/init", {
    project_files: projectFiles,
    manifest_contents: manifestContents,
    available_clis: clis,
    dry_run: dryRun,
    minimal: minimal,
    project_name: identity.project_name,
    project_id: boundProject.project_id || identity.project_id,
    remote_origin: identity.remote_origin,
    origin: identity.origin,
    binding_source: "init",
  });

  if (result.error) {
    if (result.hint) {
      log(`${result.message || result.error}`);
      console.log(`  ${result.hint}\n`);
    } else {
      log(`error: ${result.error}`);
    }
    process.exit(1);
  }

  if (spinner) spinner.stop(`${dryRun ? "[dry-run] " : ""}Detected: ${result.stack || "?"}`);
  else log(`detected: ${result.stack || "?"}`);
  if (dryRun) {
    const files = Object.keys(result.files || {});
    log(`${D}dry-run: would write ${files.length} files:${R}`);
    for (const f of files.slice(0, 20)) console.log(`  ${D}+ ${f}${R}`);
    if (files.length > 20) console.log(`  ${D}… and ${files.length - 20} more${R}`);
    return;
  }
  writeFiles(target, result.files || {});

  // Ensure ai/VERSION matches CLI version
  const versionFile = path.join(target, "ai", "VERSION");
  fs.mkdirSync(path.dirname(versionFile), { recursive: true });
  fs.writeFileSync(versionFile, VERSION + "\n", "utf8");

  // Add to .gitignore
  const gi = path.join(target, ".gitignore");
  try {
    const text = fs.existsSync(gi) ? fs.readFileSync(gi, "utf8") : "";
    if (!text.includes(".0dai")) fs.appendFileSync(gi, "\n.0dai/\n");
  } catch {}

  // Register in global portfolio
  registerProject(target, path.basename(target), result.stack);

  log(`initialized (${result.file_count || "?"} files)`);
  console.log(`  account: ${authStatus.email} · plan: ${authStatus.plan || license.plan || "free"} · activation: ${license.status}`);
  console.log(`  project: ${boundProject.project_id || identity.project_id}`);
  console.log("  skills: /build /review /status /feedback /bugfix /delegate");

  // Detect agent auth status for smart onboarding hints
  const { execFileSync: _ef } = require("child_process");
  const agents = [];
  try { _ef("claude", ["--version"], { timeout: 8000 }); agents.push("claude"); } catch {}
  try { _ef("codex", ["--version"], { timeout: 8000 }); agents.push("codex"); } catch {}
  try { _ef("gemini", ["--version"], { timeout: 8000 }); agents.push("gemini"); } catch {}

  // Next steps — guide user to first value
  console.log(`\n  ${T}Next steps:${R}`);
  console.log(`  ${D}1.${R} Check health:  ${D}0dai doctor${R}`);
  if (agents.length > 0) {
    const a = agents[0];
    console.log(`  ${D}2.${R} Try delegation: ${D}0dai run "write tests for auth"${R}`);
    console.log(`     ${D}(${agents.join(", ")} detected — delegation will use ${a} by default)${R}`);
  } else {
    console.log(`  ${D}2.${R} Install an agent CLI to enable delegation:`);
    console.log(`     ${D}claude:${R} npm i -g @anthropic-ai/claude-code  ${D}(or Pro subscription)${R}`);
    console.log(`     ${D}codex:${R}  npm i -g @openai/codex              ${D}(or ChatGPT Pro)${R}`);
  }
  console.log(`  ${D}3.${R} Open dashboard: ${D}https://0dai.dev/dashboard${R}`);

  await sendProjectHeartbeat(target, identity, result, {
    project_id: boundProject.project_id || identity.project_id,
  }).catch(() => {});
  recordExperienceEvent(target, {
    event_type: "config_generated",
    agent: "cli",
    model: "0dai-cli",
    effort: "medium",
    task: { goal: "initialize ai layer", task_type: "feat", result: "success", elapsed_seconds: 0, cost_usd: 0 },
    context: { stack: result.stack || identity.stack || "unknown", files_touched: Number(result.file_count || 0), tests_passed: true },
  });

  // Send anonymous usage ping
  apiCall("/v1/feedback", { report: {
    stack_detected: result.stack || "?", _auto: true, _plan: result.plan || "trial",
    _cli_version: VERSION, _files_generated: result.file_count || 0,
  }}).catch(() => {});
}

async function cmdSync(target, args = []) {
  const dryRun = args.includes("--dry-run");
  const quiet = args.includes("--quiet") || args.includes("-q");
  const force = args.includes("--force");

  // Quick local check: skip API if already at current version (unless dry-run or force)
  let version = "unknown";
  try { version = fs.readFileSync(path.join(target, "ai", "VERSION"), "utf8").trim(); } catch {}

  const metadata = collectMetadata(target);
  const { manifestContents, clis } = metadata;
  const authStatus = await ensureAuthenticated("sync");
  const license = await ensureLicenseActivation();
  let stack = "generic", agents = [];
  try {
    const d = JSON.parse(fs.readFileSync(path.join(target, "ai", "manifest", "discovery.json"), "utf8"));
    stack = d.stack || "generic";
    agents = d.selected_agents || [];
  } catch {}
  const identity = buildProjectIdentity(target, metadata, stack);
  const boundProject = await bindProjectForCloud(target, metadata, identity);

  // Collect current ai/ files
  const currentFiles = {};
  const aiDir = path.join(target, "ai");
  if (fs.existsSync(aiDir)) {
    const walk = (dir) => {
      for (const f of fs.readdirSync(dir, { withFileTypes: true })) {
        const p = path.join(dir, f.name);
        if (f.isDirectory()) walk(p);
        else {
          try {
            const stat = fs.statSync(p);
            if (stat.size < 10000) currentFiles[path.relative(target, p)] = fs.readFileSync(p, "utf8");
          } catch {}
        }
      }
    };
    walk(aiDir);
  }

  if (dryRun) log(`${D}dry-run: checking what sync would change...${R}`);
  if (force && !dryRun) log(`${T}force mode: will overwrite native configs from ai/ source${R}`);

  const result = await apiCall("/v1/sync", {
    ai_version: version, stack, agents: agents.length ? agents : clis,
    current_files: currentFiles, manifest_contents: manifestContents,
    dry_run: dryRun, quiet, force,
    project_name: identity.project_name,
    project_id: boundProject.project_id || identity.project_id,
    remote_origin: identity.remote_origin,
    origin: identity.origin,
    binding_source: "sync",
  });

  if (result.error) {
    log(`error: ${result.error}`);
    if (result.hint) console.log(`  ${result.hint}`);
    process.exit(1);
  }

  const updated = result.files_updated || {};
  if (dryRun) {
    const files = Object.keys(updated);
    if (files.length) {
      log(`${D}dry-run: would update ${files.length} file(s):${R}`);
      for (const f of files) console.log(`  ${D}~ ${f}${R}`);
    } else {
      log(`${D}dry-run: nothing to update${R}`);
    }
    return;
  }
  const changedCount = Object.keys(updated).length;
  if (changedCount) {
    writeFiles(target, updated);
    if (!quiet) {
      for (const f of Object.keys(updated)) console.log(`  ~ ${f}`);
    }
    log(`sync: ${changedCount} file(s) updated`);
    console.log(`  ${D}Run: 0dai doctor to verify project health${R}`);
  } else {
    log("already up to date");
  }

  // --force: also overwrite native configs (CLAUDE.md, AGENTS.md, etc.) from ai/ source
  if (force && result.native_configs) {
    const NATIVE_CONFIGS = ["CLAUDE.md", "AGENTS.md", "GEMINI.md", "opencode.json", ".cursorrules", ".windsurfrules", ".aider.conf.yml"];
    let overwritten = 0;
    for (const name of NATIVE_CONFIGS) {
      if (result.native_configs[name]) {
        fs.writeFileSync(path.join(target, name), result.native_configs[name], "utf8");
        overwritten++;
        if (!quiet) console.log(`  [force] ${name} overwritten from ai/ source`);
      }
    }
    if (overwritten && !quiet) {
      log(`force: ${overwritten} native config file(s) overwritten`);
    }
  }

  // --force: update drift baseline hashes so drift clears after regeneration
  if (force) {
    try {
      const { spawnSync } = require("child_process");
      const driftScript = path.join(target, "scripts", "drift_detector.py");
      if (fs.existsSync(driftScript)) {
        spawnSync("python3", [driftScript, "record", "--target", target], { stdio: "inherit" });
      }
    } catch {}
  }

  if (!quiet) {
    console.log(`  account: ${authStatus.email} · plan: ${authStatus.plan || license.plan || "free"} · activation: ${license.status}`);
    console.log(`  project: ${boundProject.project_id || identity.project_id}`);
  }

  // Ensure ai/VERSION matches CLI version after successful sync
  const versionFile = path.join(target, "ai", "VERSION");
  try {
    const current = fs.existsSync(versionFile) ? fs.readFileSync(versionFile, "utf8").trim() : "";
    if (current !== VERSION) {
      fs.writeFileSync(versionFile, VERSION + "\n", "utf8");
    }
  } catch {}

  // Update portfolio registry
  registerProject(target, path.basename(target), stack);
  await sendProjectHeartbeat(target, identity, result, {
    project_id: boundProject.project_id || identity.project_id,
  }).catch(() => {});
  recordExperienceEvent(target, {
    event_type: "config_generated",
    agent: "cli",
    model: "0dai-cli",
    effort: "medium",
    task: { goal: "sync ai layer", task_type: "feat", result: "success", elapsed_seconds: 0, cost_usd: 0 },
    context: { stack: stack || identity.stack || "unknown", files_touched: changedCount, tests_passed: true },
  });
}

module.exports = { cmdInit, cmdSync };
