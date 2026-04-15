/**
 * Onboarding helpers — post-install welcome, post-init checklist,
 * first-status tip, time-to-init tracking.
 */
"use strict";

const fs = require("fs");
const path = require("path");

// ---------------------------------------------------------------------------
// State file
// ---------------------------------------------------------------------------

function _statePath(target) {
  return path.join(target, "ai", ".0dai_state.json");
}

function _loadState(target) {
  try {
    return JSON.parse(fs.readFileSync(_statePath(target), "utf8"));
  } catch {
    return {};
  }
}

function _saveState(target, state) {
  try {
    const dir = path.join(target, "ai");
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(_statePath(target), JSON.stringify(state, null, 2) + "\n");
  } catch {}
}

// ---------------------------------------------------------------------------
// Post-init What's Next
// ---------------------------------------------------------------------------

function showWhatsNext(mode, isAuthed) {
  console.log("");
  console.log("  \u2705 0dai initialized! Your AI agents are configured.");
  console.log("");
  console.log("  What's next:");
  console.log("    \u2610 0dai status     \u2014 check your config");
  console.log("    \u2610 0dai doctor     \u2014 verify everything works");
  if (mode === "local" && !isAuthed) {
    console.log("    \u2610 0dai auth login \u2014 sign in for full features (optional)");
  } else if (mode === "cloud") {
    console.log("    \u2610 0dai sync       \u2014 refresh configs from server");
  }
  console.log("");
  console.log("  Pro features: 0dai upgrade");
  console.log("");
}

// ---------------------------------------------------------------------------
// First-status tip
// ---------------------------------------------------------------------------

function showFirstStatusTip(target) {
  const state = _loadState(target);
  if (state.first_status_shown) return;
  console.log("");
  console.log("  \ud83d\udca1 Tip: Run 0dai doctor to check config health");
  state.first_status_shown = true;
  _saveState(target, state);
}

// ---------------------------------------------------------------------------
// Time-to-init tracking
// ---------------------------------------------------------------------------

function trackFirstRun(target) {
  const state = _loadState(target);
  if (!state.first_run_at) {
    state.first_run_at = new Date().toISOString();
    _saveState(target, state);
  }
}

function trackFirstInit(target) {
  const state = _loadState(target);
  if (!state.first_init_at) {
    state.first_init_at = new Date().toISOString();
    _saveState(target, state);
  }
}

function getTimeToInit(target) {
  const state = _loadState(target);
  if (!state.first_run_at || !state.first_init_at) return null;
  const start = new Date(state.first_run_at).getTime();
  const end = new Date(state.first_init_at).getTime();
  if (isNaN(start) || isNaN(end)) return null;
  return Math.round((end - start) / 1000);
}

// ---------------------------------------------------------------------------
// Quickstart
// ---------------------------------------------------------------------------

async function cmdQuickstart(target, { cmdDoctor, cmdStatus, cmdInit, log, ensureAuthenticated }) {
  const start = Date.now();
  const steps = 5;

  // Step 1: Auth
  console.log(`\n  [1/${steps}] Checking authentication...`);
  let authInfo = "not signed in";
  try {
    const auth = JSON.parse(fs.readFileSync(path.join(require("os").homedir(), ".0dai", "auth.json"), "utf8"));
    if (auth.access_token) {
      authInfo = `signed in (${auth.plan || "free"} plan)`;
    }
  } catch {}
  console.log(`           \u2713 ${authInfo}`);

  // Step 2: Init
  console.log(`  [2/${steps}] Checking project config...`);
  const aiExists = fs.existsSync(path.join(target, "ai", "VERSION"));
  if (aiExists) {
    console.log("           \u2713 ai/ layer found");
  } else {
    console.log("           initializing...");
    try {
      await cmdInit(target, ["--quickstart"]);
      trackFirstInit(target);
      console.log("           \u2713 project initialized");
    } catch (err) {
      console.log(`           \u2717 init failed: ${err.message || err}`);
      console.log("           Run: 0dai init");
    }
  }

  // Step 3: Doctor
  console.log(`  [3/${steps}] Running health check...`);
  if (fs.existsSync(path.join(target, "ai"))) {
    try {
      cmdDoctor(target);
    } catch {}
    console.log("           \u2713 health check complete");
  } else {
    console.log("           \u2717 skipped (no ai/ layer)");
  }

  // Step 4: Status
  console.log(`  [4/${steps}] Project status:`);
  if (fs.existsSync(path.join(target, "ai"))) {
    try {
      cmdStatus(target);
    } catch {}
  } else {
    console.log("           (no project configured)");
  }

  // Step 5: Summary
  const elapsed = ((Date.now() - start) / 1000).toFixed(1);
  console.log(`  [5/${steps}] Ready! (${elapsed}s)`);
  console.log("");
  console.log("  Your project is set up. Try:");
  console.log("    0dai swarm run --goal \"add auth\"  (Pro)");
  console.log("    0dai graph push                   (Pro)");
  console.log("");
}

module.exports = {
  showWhatsNext,
  showFirstStatusTip,
  trackFirstRun,
  trackFirstInit,
  getTimeToInit,
  cmdQuickstart,
};
