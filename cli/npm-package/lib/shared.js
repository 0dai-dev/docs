/**
 * Shared configuration and utilities for 0dai CLI commands.
 *
 * Phase 2: Thin re-export layer. Logic extracted into lib/utils/*.
 * All command modules require from here — API is unchanged.
 */
"use strict";

const https = require("https");
const http = require("http");
const fs = require("fs");
const path = require("path");
const os = require("os");
const crypto = require("crypto");
const { spawnSync } = require("child_process");

const VERSION = require("../package.json").version;

// --- Re-export from extracted modules ---
const { SUPPORTED_CLIS, MANIFEST_FILES, PROBE_DIRS, SETTINGS_PRESERVE_FIELDS } = require("./utils/constants");
const {
  deviceFingerprint, registerProject, projectIdFor,
  getGitRemoteOrigin, inferProjectName, detectStackHint,
  collectMetadata, buildProjectIdentity,
} = require("./utils/identity");
const { PLAN_LEVELS, _detectPlanLocal, requirePlan, getSwarmQuotaLocal } = require("./utils/plan");

// --- Colors & logging ---
function _validateApiUrl(url) {
  const DEFAULT = "https://api.0dai.dev";
  if (!url) return DEFAULT;
  try {
    const u = new URL(url);
    if (u.protocol === "https:") return url;
    if (u.protocol === "http:" && (u.hostname === "localhost" || u.hostname === "127.0.0.1" || u.hostname === "::1")) return url;
    return DEFAULT;
  } catch { return DEFAULT; }
}

const API_URL = _validateApiUrl(process.env.ODAI_API_URL);
const T = process.stdout.isTTY ? "\x1b[38;2;45;212;168m" : "";
const R = process.stdout.isTTY ? "\x1b[0m" : "";
const D = process.stdout.isTTY ? "\x1b[2m" : "";
const E = process.stdout.isTTY ? "\x1b[31m" : "";
const G = process.stdout.isTTY ? "\x1b[32m" : "";
const W = process.stdout.isTTY ? "\x1b[33m" : "";
const log = (msg) => console.log(`${T}[0dai]${R} ${msg}`);
const CONFIG_DIR = path.join(os.homedir(), ".0dai");
const AUTH_FILE = path.join(CONFIG_DIR, "auth.json");
const VERSION_CHECK_FILE = path.join(CONFIG_DIR, ".version_check");
const PROJECTS_FILE = path.join(CONFIG_DIR, "projects.json");
const DRIFT_TRACKED_CONFIGS = [
  "CLAUDE.md",
  "AGENTS.md",
  "GEMINI.md",
  "opencode.json",
  ".cursorrules",
  ".windsurfrules",
  ".aider.conf.yml",
];

// --- API ---
function apiCall(endpoint, data) {
  return new Promise((resolve) => {
    const url = new URL(endpoint, API_URL);
    const mod = url.protocol === "https:" ? https : http;
    const body = data ? JSON.stringify(data) : null;
    const headers = {
      "Content-Type": "application/json",
      "X-Device-ID": deviceFingerprint(),
      "X-CLI-Version": VERSION,
      "X-Client-Channel": "npm",
    };
    try {
      const auth = JSON.parse(fs.readFileSync(AUTH_FILE, "utf8"));
      const token = auth.api_key || auth.access_token || auth.token;
      if (token) headers["Authorization"] = `Bearer ${token}`;
    } catch {}
    const opts = {
      hostname: url.hostname,
      port: url.port || (url.protocol === "https:" ? 443 : 80),
      path: url.pathname,
      method: body ? "POST" : "GET",
      headers,
      timeout: 60000,
    };
    if (body) opts.headers["Content-Length"] = Buffer.byteLength(body);
    const req = mod.request(opts, (res) => {
      let chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => {
        try { resolve(JSON.parse(Buffer.concat(chunks).toString())); }
        catch { resolve({ error: `HTTP ${res.statusCode}` }); }
      });
    });
    req.on("error", (e) => resolve({ error: `${e.message}. Is ${API_URL} reachable?` }));
    req.on("timeout", () => { req.destroy(); resolve({ error: "request timed out after 60s. Check your internet connection or try again." }); });
    if (body) req.write(body);
    req.end();
  });
}

// --- Auth State ---
function loadAuthState() {
  try { return JSON.parse(fs.readFileSync(AUTH_FILE, "utf8")); }
  catch { return null; }
}

function saveAuthState(next) {
  fs.mkdirSync(CONFIG_DIR, { recursive: true, mode: 0o700 });
  fs.writeFileSync(AUTH_FILE, JSON.stringify(next, null, 2) + "\n", { mode: 0o600 });
}

function updateAuthState(patch) {
  const current = loadAuthState() || {};
  saveAuthState({ ...current, ...patch });
}

async function fetchAuthStatus() {
  const status = await apiCall("/v1/auth/status");
  if (status && !status.error && status.email) {
    updateAuthState({
      email: status.email, plan: status.plan || "free",
      name: status.name || "", license: status.license || {},
    });
  }
  return status;
}

function makeEnsureAuthenticated(cmdAuthLogin) {
  return async function ensureAuthenticated(actionLabel) {
    let auth = loadAuthState();
    if (!auth || !(auth.api_key || auth.access_token || auth.token)) {
      if (cmdAuthLogin && process.stdout.isTTY && process.stdin.isTTY) {
        log(`${actionLabel} requires 0dai account auth`);
        await cmdAuthLogin();
        auth = loadAuthState();
      } else {
        log(`authentication required for ${actionLabel}`);
        console.log(`  ${D}Run: 0dai auth login${R}`);
        process.exit(1);
      }
    }
    const status = await fetchAuthStatus();
    if (status.error) {
      log(`${actionLabel} requires a valid 0dai session`);
      console.log(`  ${D}Run: 0dai auth login${R}`);
      process.exit(1);
    }
    return status;
  };
}

async function ensureLicenseActivation() {
  const status = await apiCall("/v1/licenses/status");
  if (!status.error && status.license && status.license.status === "active") {
    updateAuthState({ license: status.license });
    return status.license;
  }
  log("activating free open-source license...");
  const activated = await apiCall("/v1/licenses/activate", {
    device_id: deviceFingerprint(), cli_version: VERSION, channel: "npm",
  });
  if (activated.error || !activated.license) {
    log(`error: ${activated.error || "activation failed"}`);
    process.exit(1);
  }
  updateAuthState({ license: activated.license });
  return activated.license;
}

// --- Project Heartbeat ---
function _hashFileSha256(filePath) {
  const buf = fs.readFileSync(filePath);
  return crypto.createHash("sha256").update(buf).digest("hex");
}

function computeProjectDriftSummary(target) {
  const hashesPath = path.join(target, "ai", "manifest", "config_hashes.json");
  if (!fs.existsSync(hashesPath)) return null;
  let hashes;
  try {
    hashes = JSON.parse(fs.readFileSync(hashesPath, "utf8"));
  } catch {
    return null;
  }
  const findings = [];
  let totalConfigs = 0;
  for (const name of DRIFT_TRACKED_CONFIGS) {
    const filePath = path.join(target, name);
    const exists = fs.existsSync(filePath) && fs.statSync(filePath).isFile();
    const recorded = hashes[name];
    if (exists) totalConfigs += 1;
    if (recorded && !exists) {
      findings.push({ config: name, type: "missing", severity: "warning" });
      continue;
    }
    if (!recorded && exists) {
      findings.push({ config: name, type: "extra", severity: "info" });
      continue;
    }
    if (recorded && exists) {
      try {
        const currentHash = _hashFileSha256(filePath);
        if (currentHash !== String(recorded.hash || "")) {
          findings.push({ config: name, type: "modified", severity: "warning" });
        }
      } catch {
        findings.push({ config: name, type: "unreadable", severity: "warning" });
      }
    }
  }
  const driftedCount = findings.filter((f) => f.type === "modified" || f.type === "missing").length;
  return {
    available: true,
    clean: findings.length === 0,
    drifted_count: driftedCount,
    total_configs: totalConfigs,
    findings,
    updated_at: new Date().toISOString(),
  };
}

async function sendProjectHeartbeat(target, identity, result, extra = {}) {
  const drift = computeProjectDriftSummary(target);
  return apiCall("/v1/projects/heartbeat", {
    project_id: identity.project_id, stack: result.stack || identity.stack || "unknown",
    cli_version: VERSION, activation_status: "active", binding_status: "bound",
    runtime_sessions: 0, swarm_active: 0, swarm_done: 0, channel: "npm",
    ...(drift ? { drift } : {}),
    ...extra,
  });
}

// --- File Writing ---
function mergeSettingsJson(existing, incoming) {
  try {
    const base = JSON.parse(incoming);
    const user = JSON.parse(existing);
    for (const field of SETTINGS_PRESERVE_FIELDS) {
      if (field in user && user[field] !== base[field]) base[field] = user[field];
    }
    return JSON.stringify(base, null, 2) + "\n";
  } catch { return incoming; }
}

function writeFiles(target, files) {
  let created = 0, updated = 0, unchanged = 0, merged = 0, skipped = 0;
  const targetResolved = path.resolve(target);
  for (const [rel, content] of Object.entries(files)) {
    if (typeof rel !== "string" || !rel || path.isAbsolute(rel) || rel.split(/[/\\]/).includes("..")) {
      skipped++; continue;
    }
    const p = path.resolve(targetResolved, rel);
    if (!p.startsWith(targetResolved + path.sep) && p !== targetResolved) { skipped++; continue; }
    fs.mkdirSync(path.dirname(p), { recursive: true });
    let finalContent = content;
    if (fs.existsSync(p)) {
      const existing = fs.readFileSync(p, "utf8");
      if (existing === content) { unchanged++; continue; }
      if (rel.endsWith("settings.json")) { finalContent = mergeSettingsJson(existing, content); merged++; }
      else if (rel === "AGENTS.md") {
        if (existing.includes("managed: false")) { unchanged++; continue; }
        const backupDir = path.join(target, "ai", ".backups");
        fs.mkdirSync(backupDir, { recursive: true });
        fs.writeFileSync(path.join(backupDir, "AGENTS.md.bak"), existing, "utf8");
        updated++;
      } else { updated++; }
    } else { created++; }
    fs.writeFileSync(p, finalContent, "utf8");
  }
  const parts = [`${created} created`, `${updated} updated`, `${unchanged} unchanged`];
  if (merged) parts.push(`${merged} merged`);
  if (skipped) parts.push(`${skipped} skipped (unsafe path)`);
  log(parts.join(", "));
  return created + updated;
}

// --- Repo Script Lookup ---
function findRepoScript(target, scriptName) {
  const candidates = [
    path.join(target, "scripts", scriptName),
    path.join(process.cwd(), "scripts", scriptName),
    path.join(__dirname, "..", "..", "..", "scripts", scriptName),
  ];
  for (const c of candidates) { if (fs.existsSync(c)) return c; }
  return null;
}

// --- Version Check ---
async function checkVersion() {
  try {
    const intervalSec = parseInt(process.env.ODAI_UPDATE_CHECK_INTERVAL || "3600");
    let lastCheck = 0;
    try { lastCheck = parseFloat(fs.readFileSync(VERSION_CHECK_FILE, "utf8")); } catch {}
    if (Date.now() / 1000 - lastCheck < intervalSec) return;
    fs.mkdirSync(CONFIG_DIR, { recursive: true, mode: 0o700 });
    fs.writeFileSync(VERSION_CHECK_FILE, String(Date.now() / 1000));
    const result = await apiCall("/v1/version");
    if (result.version && result.version !== VERSION) {
      const cmp = (a, b) => { const [a1,a2,a3] = a.split(".").map(Number); const [b1,b2,b3] = b.split(".").map(Number); return a1 - b1 || a2 - b2 || a3 - b3; };
      if (cmp(result.version, VERSION) > 0) {
        log(`Update available: ${VERSION} → ${result.version}`);
        console.log(`  Run: npm update -g @0dai-dev/cli\n`);
      }
    }
  } catch {}
}

// --- Experience ---
function recordExperienceEvent(target, payload) {
  const script = findRepoScript(target, "experience_pipeline.py");
  if (!script) return;
  try {
    spawnSync("python3", [script, "record-json", "--target", target], {
      input: JSON.stringify(payload), stdio: ["pipe", "ignore", "ignore"],
    });
  } catch {}
}

// --- Re-export everything for backward compatibility ---
module.exports = {
  // Core
  VERSION, API_URL, T, R, D, E, G, W,
  log, CONFIG_DIR, AUTH_FILE, VERSION_CHECK_FILE, PROJECTS_FILE,
  // Constants
  PLAN_LEVELS, MANIFEST_FILES, PROBE_DIRS, SUPPORTED_CLIS, SETTINGS_PRESERVE_FIELDS,
  // API
  apiCall,
  // Auth
  loadAuthState, saveAuthState, updateAuthState,
  fetchAuthStatus, makeEnsureAuthenticated, ensureLicenseActivation,
  // Identity
  deviceFingerprint, registerProject, projectIdFor,
  getGitRemoteOrigin, inferProjectName, detectStackHint,
  collectMetadata, buildProjectIdentity,
  // Plan / Tier
  _detectPlanLocal, requirePlan, getSwarmQuotaLocal,
  // Project
  sendProjectHeartbeat, recordExperienceEvent,
  // Files
  mergeSettingsJson, writeFiles, findRepoScript,
  // Version
  checkVersion,
  // Re-exports for convenience
  spawnSync, fs, path, os, https, http,
};
