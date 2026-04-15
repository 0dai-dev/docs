"use strict";
const shared = require("../shared");
const {
  T, R, D, log,
  fs, os,
  CONFIG_DIR, AUTH_FILE, API_URL,
  apiCall, loadAuthState, fetchAuthStatus, updateAuthState,
  makeEnsureAuthenticated, ensureLicenseActivation,
} = shared;

async function cmdAuthLogin() {
  const isTTY = process.stdout.isTTY && process.stdin.isTTY;

  // Check if already authenticated
  try {
    const existing = JSON.parse(fs.readFileSync(AUTH_FILE, "utf8"));
    if (existing.access_token || existing.email) {
      if (isTTY) {
        const p = require("@clack/prompts");
        p.intro(`${T}0dai${R} authentication`);
        p.log.success(`Already logged in as ${T}${existing.email || "unknown"}${R} (${existing.plan || "free"} plan)`);
        const reauth = await p.confirm({ message: "Sign in with a different account?" });
        if (p.isCancel(reauth) || !reauth) {
          p.outro("Current session kept");
          return;
        }
      } else {
        log(`Already logged in as ${existing.email || "unknown"} (${existing.plan || "free"} plan)`);
        log("To switch accounts, delete ~/.0dai/auth.json and run again");
        return;
      }
    }
  } catch {}

  if (isTTY) {
    // Interactive TUI flow
    const p = require("@clack/prompts");
    if (!p._intro_shown) p.intro(`${T}0dai${R} authentication`);

    p.note(
      "0dai auth is separate from agent CLIs (Claude Code, Codex).\n" +
      "It tracks your projects, usage limits, and team features.\n" +
      "Your agent CLIs keep their own auth (subscription/API key).",
      "Why sign in?"
    );

    const method = await p.select({
      message: "How would you like to sign in?",
      options: [
        { value: "github", label: "GitHub", hint: "recommended" },
        { value: "google", label: "Google" },
        { value: "device", label: "Device code", hint: "no browser needed" },
      ],
    });
    if (p.isCancel(method)) { p.cancel("Cancelled"); process.exit(0); }

    if (method === "github" || method === "google") {
      const url = `${API_URL}/v1/auth/${method}?cli=true`;
      p.log.info(`Opening browser: ${url}`);
      try {
        const { execFileSync } = require("child_process");
        const cmd = os.platform() === "darwin" ? "open" : os.platform() === "win32" ? "start" : "xdg-open";
        // MED: use execFileSync to avoid shell injection via URL metacharacters
        execFileSync(cmd, [url], { stdio: "ignore" });
      } catch {
        p.log.warn(`Could not open browser. Visit manually:\n  ${url}`);
      }

      const s = p.spinner();
      s.start("Waiting for browser confirmation...");

      // Poll auth/status until we get a new token (check every 3s, 5min timeout)
      // For now, ask user to paste token from success page
      s.stop("Browser opened");
      const token = await p.text({
        message: "Paste your token from the success page (or press Enter to skip):",
        placeholder: "0dai_at_...",
      });
      if (token && !p.isCancel(token) && token.startsWith("0dai_at_")) {
        fs.mkdirSync(CONFIG_DIR, { recursive: true, mode: 0o700 });
        fs.writeFileSync(AUTH_FILE, JSON.stringify({
          access_token: token,
          authenticated_at: new Date().toISOString(),
        }, null, 2) + "\n", { mode: 0o600 });
        // Fetch profile
        const status = await apiCall("/v1/auth/status");
        if (status.email) {
          const auth = JSON.parse(fs.readFileSync(AUTH_FILE, "utf8"));
          auth.email = status.email;
          auth.plan = status.plan;
          auth.name = status.name;
          fs.writeFileSync(AUTH_FILE, JSON.stringify(auth, null, 2) + "\n", { mode: 0o600 });
          p.outro(`${T}Logged in${R} as ${status.email} (${status.plan} plan)`);
        } else {
          p.outro(`${T}Token saved${R}`);
        }
        return;
      }
      p.log.info("Skipped. You can also use device code flow:");
    }

    // Device code fallback
    const result = await apiCall("/v1/auth/device", { client_id: "cli" });
    if (result.error) { p.log.error(result.error); process.exit(1); }

    p.log.step(`Open: ${result.verification_uri}`);
    p.log.step(`Code: ${T}${result.user_code}${R}`);

    const s = p.spinner();
    s.start("Waiting for confirmation...");

    const interval = (result.interval || 5) * 1000;
    const deadline = Date.now() + (result.expires_in || 600) * 1000;
    while (Date.now() < deadline) {
      await new Promise(r => setTimeout(r, interval));
      const poll = await apiCall("/v1/auth/token", { device_code: result.device_code });
      if (poll.access_token) {
        s.stop("Authorized!");
        fs.mkdirSync(CONFIG_DIR, { recursive: true, mode: 0o700 });
        fs.writeFileSync(AUTH_FILE, JSON.stringify({
          access_token: poll.access_token, email: poll.email,
          plan: poll.plan || "free", authenticated_at: new Date().toISOString(),
          expires_at: poll.expires_at,
        }, null, 2) + "\n", { mode: 0o600 });
        p.outro(`${T}Logged in${R} as ${poll.email} (${poll.plan} plan)`);
        return;
      }
      if (poll.error && poll.error !== "authorization_pending") {
        s.stop("Failed");
        p.log.error(poll.error);
        process.exit(1);
      }
    }
    s.stop("Device code expired");
    p.log.error("The code expired after 10 minutes. Run '0dai auth login' to get a new code.");
    process.exit(1);

  } else {
    // Non-interactive: device code only
    log("0dai auth is separate from agent CLIs. It tracks projects, limits, and team features.");
    const result = await apiCall("/v1/auth/device", { client_id: "cli" });
    if (result.error) { log(`error: ${result.error}`); process.exit(1); }
    log(`Open: ${result.verification_uri}`);
    log(`Code: ${result.user_code}`);
    log("Waiting...");
    const interval = (result.interval || 5) * 1000;
    const deadline = Date.now() + (result.expires_in || 600) * 1000;
    while (Date.now() < deadline) {
      await new Promise(r => setTimeout(r, interval));
      const poll = await apiCall("/v1/auth/token", { device_code: result.device_code });
      if (poll.access_token) {
        fs.mkdirSync(CONFIG_DIR, { recursive: true, mode: 0o700 });
        fs.writeFileSync(AUTH_FILE, JSON.stringify({
          access_token: poll.access_token, email: poll.email,
          plan: poll.plan || "free", authenticated_at: new Date().toISOString(),
        }, null, 2) + "\n", { mode: 0o600 });
        log(`Logged in as ${poll.email}`);
        return;
      }
    }
    log("Device code expired after 10 minutes. Run '0dai auth login' again.");
    process.exit(1);
  }
}

function cmdAuthLogout() {
  try { fs.unlinkSync(AUTH_FILE); } catch {}
  log("Logged out");
}

async function cmdRedeem(code) {
  if (!code) {
    console.log("Usage: 0dai redeem <CODE>");
    console.log("Example: 0dai redeem ESSE-ABCD-1234");
    process.exit(1);
  }
  try {
    JSON.parse(fs.readFileSync(AUTH_FILE, "utf8"));
  } catch {
    log("Not logged in. Run: 0dai auth login");
    process.exit(1);
  }
  log(`Redeeming code ${T}${code.toUpperCase()}${R}...`);
  const result = await apiCall("/v1/redeem", { code: code.toUpperCase().trim() });
  if (result.ok) {
    log(`${T}✓${R} ${result.message}`);
    if (result.duration_days) {
      log(`  Plan active for ${result.duration_days} days`);
    }
    log(`  Run ${D}0dai auth status${R} to see updated limits`);
  } else {
    log(`error: ${result.error || "unknown"}`);
    if (result.hint) log(`hint: ${result.hint}`);
    process.exit(1);
  }
}

async function cmdAuthStatus() {
  try {
    const auth = loadAuthState();
    if (!auth) throw new Error("missing auth");
    // Backwards compat: old auth.json used `user`, new uses `email`
    const email = auth.email || auth.user || "unknown";
    log(`${email} (${auth.plan || "free"} plan)`);
    // Get usage from API
    const status = await fetchAuthStatus();
    if (status.usage_today) {
      console.log("  Usage today:");
      for (const [k, v] of Object.entries(status.usage_today))
        console.log(`    ${k}: ${v} / ${status.limits[k]}`);
    }
    const license = status.license || auth.license || { status: "inactive" };
    console.log(`  Activation: ${license.status || "inactive"}${license.activation_id ? ` (${license.activation_id})` : ""}`);
    if (status.projects && status.projects.length) {
      console.log(`  Projects bound: ${status.projects.length} / ${status.project_limit || "?"}`);
    }
  } catch {
    log("Not logged in. Run: 0dai auth login");
  }
}

async function cmdActivateFree() {
  const ensureAuthenticated = makeEnsureAuthenticated(cmdAuthLogin);
  await ensureAuthenticated("activation");
  const license = await ensureLicenseActivation();
  log(`license ${license.status}`);
  console.log(`  activation id: ${license.activation_id}`);
  console.log(`  plan: ${license.plan || "free"}`);
}

async function cmdActivateStatus() {
  const ensureAuthenticated = makeEnsureAuthenticated(cmdAuthLogin);
  const status = await ensureAuthenticated("activation status");
  const license = status.license || (await apiCall("/v1/licenses/status")).license || { status: "inactive" };
  updateAuthState({ license });
  log(`license ${license.status || "inactive"}`);
  if (license.activation_id) console.log(`  activation id: ${license.activation_id}`);
  console.log(`  plan: ${license.plan || status.plan || "free"}`);
}

module.exports = { cmdAuthLogin, cmdAuthLogout, cmdRedeem, cmdAuthStatus, cmdActivateFree, cmdActivateStatus };
