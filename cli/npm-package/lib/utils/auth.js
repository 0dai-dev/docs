/**
 * Authentication and license management utilities.
 * Extracted from shared.js to reduce module size.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const os = require("os");

const CONFIG_DIR = path.join(os.homedir(), ".0dai");
const AUTH_FILE = path.join(CONFIG_DIR, "auth.json");

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

function deviceFingerprint() {
  const crypto = require("crypto");
  const parts = [os.hostname(), os.userInfo().username, os.platform(), os.arch(), os.cpus().length.toString(), os.totalmem().toString()];
  try {
    if (os.platform() === "linux") parts.push(fs.readFileSync("/etc/machine-id", "utf8").trim());
  } catch {}
  return crypto.createHash("sha256").update(parts.join(":")).digest("hex").slice(0, 32);
}

async function apiCall(endpoint, data, API_URL, VERSION) {
  const https = require("https");
  const http = require("http");
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
    req.on("timeout", () => { req.destroy(); resolve({ error: "timeout" }); });
    if (body) req.write(body);
    req.end();
  });
}

async function fetchAuthStatus(apiCallFn, API_URL) {
  const status = await apiCallFn("/v1/auth/status", undefined, API_URL);
  if (status && !status.error && status.email) {
    updateAuthState({
      email: status.email,
      plan: status.plan || "free",
      name: status.name || "",
      license: status.license || {},
    });
  }
  return status;
}

function makeEnsureAuthenticated(cmdAuthLogin, apiCallFn, API_URL, log, D, R) {
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
    const status = await fetchAuthStatus(apiCallFn, API_URL);
    if (status.error) {
      log(`${actionLabel} requires a valid 0dai session`);
      console.log(`  ${D}Run: 0dai auth login${R}`);
      process.exit(1);
    }
    return status;
  };
}

async function ensureLicenseActivation(apiCallFn, API_URL, VERSION, log) {
  const status = await apiCallFn("/v1/licenses/status", undefined, API_URL);
  if (!status.error && status.license && status.license.status === "active") {
    updateAuthState({ license: status.license });
    return status.license;
  }
  log("activating free open-source license...");
  const activated = await apiCallFn("/v1/licenses/activate", {
    device_id: deviceFingerprint(),
    cli_version: VERSION,
    channel: "npm",
  }, API_URL);
  if (activated.error || !activated.license) {
    log(`error: ${activated.error || "activation failed"}`);
    process.exit(1);
  }
  updateAuthState({ license: activated.license });
  return activated.license;
}

module.exports = {
  CONFIG_DIR, AUTH_FILE,
  loadAuthState, saveAuthState, updateAuthState,
  deviceFingerprint, apiCall, fetchAuthStatus,
  makeEnsureAuthenticated, ensureLicenseActivation,
};
