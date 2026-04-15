"use strict";
const shared = require("../shared");
const { log, T, R, D, fs, path, https, requirePlan } = shared;

function cmdSwarm(target, sub, args) {
  const swarmDir = path.join(target, "ai", "swarm");
  const queueDir = path.join(swarmDir, "queue");

  if (sub === "status") {
    const count = (d) => { try { return fs.readdirSync(d).filter(f => f.endsWith(".json")).length; } catch { return 0; } };
    const q = count(path.join(swarmDir, "queue"));
    const a = count(path.join(swarmDir, "active"));
    const d = count(path.join(swarmDir, "done"));
    log(`swarm: ${q} queued, ${a} active, ${d} done`);
    return;
  }
  if (sub === "add" || sub === "delegate") {
    const gate = requirePlan("pro", "Swarm", target);
    if (gate) { log(gate.error); log(gate.hint); return; }
    fs.mkdirSync(queueDir, { recursive: true });
    const task = args.find((_, i) => args[i - 1] === "--task") || "untitled";
    const forAgent = args.find((_, i) => ["--for", "--to"].includes(args[i - 1])) || "any";
    const id = `swarm-${Date.now()}`;
    const t = { id, title: task, assigned_to: forAgent, status: "pending", created_at: new Date().toISOString(), created_by: "cli" };
    fs.writeFileSync(path.join(queueDir, `${id}.json`), JSON.stringify(t, null, 2));
    log(`task created: ${id} → ${forAgent}`);
    return;
  }
  if (sub === "webhook") {
    const webhooksFile = path.join(swarmDir, "webhooks.json");
    const loadHooks = () => { try { return JSON.parse(fs.readFileSync(webhooksFile, "utf8")); } catch { return []; } };
    const saveHooks = (h) => { fs.mkdirSync(swarmDir, { recursive: true }); fs.writeFileSync(webhooksFile, JSON.stringify(h, null, 2)); };
    const action = args[2] || "";

    if (action === "add") {
      const url = args[3] || args.find((_, i) => args[i-1] === "--url");
      const event = args.find((_, i) => args[i-1] === "--event") || "all";
      const secret = args.find((_, i) => args[i-1] === "--secret") || "";
      if (!url || !url.startsWith("http")) { log("Usage: 0dai swarm webhook add <url> [--event task_done|task_failed|all] [--secret TOKEN]"); return; }
      // MED: SSRF protection — block internal/metadata endpoints
      try {
        const u = new URL(url);
        const host = u.hostname;
        const BLOCKED = /^(127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.|169\.254\.|::1$|fc00:|fe80:|localhost$|0\.0\.0\.0$)/i;
        if (BLOCKED.test(host) || host === "metadata.google.internal") {
          log(`rejected: ${host} is a private/internal address (SSRF protection)`);
          return;
        }
        if (u.protocol !== "https:" && u.protocol !== "http:") {
          log(`rejected: only http/https allowed, got ${u.protocol}`);
          return;
        }
      } catch {
        log(`invalid URL: ${url}`);
        return;
      }
      const hooks = loadHooks();
      if (hooks.find(h => h.url === url)) { log(`already registered: ${url}`); return; }
      hooks.push({ url, event, secret: secret || undefined, added_at: new Date().toISOString() });
      saveHooks(hooks);
      log(`webhook added: ${url} (event: ${event})`);
      return;
    }
    if (action === "list") {
      const hooks = loadHooks();
      if (hooks.length === 0) { log("no webhooks registered. Use: 0dai swarm webhook add <url>"); return; }
      console.log(`\n  ${T}Registered webhooks${R}\n`);
      hooks.forEach((h, i) => {
        console.log(`  ${i+1}. ${h.url}`);
        console.log(`     ${D}event: ${h.event}  added: ${h.added_at?.slice(0,10)}${R}`);
      });
      console.log();
      return;
    }
    if (action === "remove") {
      const url = args[3] || "";
      if (!url) { log("Usage: 0dai swarm webhook remove <url>"); return; }
      const hooks = loadHooks().filter(h => h.url !== url);
      saveHooks(hooks);
      log(`removed: ${url}`);
      return;
    }
    if (action === "test") {
      const url = args[3] || loadHooks()[0]?.url;
      if (!url) { log("Usage: 0dai swarm webhook test <url>"); return; }
      const payload = JSON.stringify({ event: "test", task_id: "test-ping", title: "Webhook test from 0dai", status: "done", timestamp: new Date().toISOString() });
      const req = https.request(url, { method: "POST", headers: { "Content-Type": "application/json", "User-Agent": "0dai-swarm/1.0", "Content-Length": Buffer.byteLength(payload) } }, (res) => {
        log(`test sent to ${url} → HTTP ${res.statusCode}`);
      });
      req.on("error", (e) => log(`test failed: ${e.message}`));
      req.setTimeout(5000, () => { req.destroy(); log("test timed out"); });
      req.write(payload);
      req.end();
      return;
    }
    console.log("Usage: 0dai swarm webhook [add|list|remove|test] <url> [--event all|task_done|task_failed] [--secret TOKEN]");
    return;
  }
  if (sub === "budget") {
    const budgetFile = path.join(swarmDir, "budget.json");
    if (!fs.existsSync(budgetFile)) { log("no budget data yet"); return; }
    const b = JSON.parse(fs.readFileSync(budgetFile, "utf8"));
    const B2 = process.stdout.isTTY ? "\x1b[1m" : "";
    const R2 = process.stdout.isTTY ? "\x1b[0m" : "";
    const D2 = process.stdout.isTTY ? "\x1b[2m" : "";
    const G2 = process.stdout.isTTY ? "\x1b[32m" : "";
    const W2 = process.stdout.isTTY ? "\x1b[33m" : "";
    const today = new Date().toISOString().slice(0, 10);
    const sessionKey = process.env.ODAI_SESSION_ID ||
      new Date().toISOString().slice(0, 13).replace("T", "-");
    const dailySpent = b.daily?.[today] || 0;
    const totalSpent = b.total_spent || 0;
    const sess = b.sessions?.[sessionKey];
    // Tier distribution across all tasks
    const tierCount = { fast: 0, balanced: 0, deep: 0 };
    for (const t of Object.values(b.tasks || {})) {
      if (t.tier && tierCount[t.tier] !== undefined) tierCount[t.tier]++;
    }
    const tieredTotal = tierCount.fast + tierCount.balanced + tierCount.deep;
    console.log(`\n  ${B2}Swarm Budget${R2}`);
    if (sess && sess.total_cost > 0) {
      const taskCount = (sess.tasks || []).length;
      const avgCost = taskCount > 0 ? (sess.total_cost / taskCount).toFixed(4) : "0";
      console.log(`    ${B2}This session${R2}  $${sess.total_cost.toFixed(4)} · ${taskCount} tasks · avg $${avgCost}/task`);
      if (sess.tiers) {
        const tiers = Object.entries(sess.tiers).filter(([, n]) => n > 0).map(([t, n]) => `${n}×${t}`).join("  ");
        if (tiers) console.log(`    ${D2}Tiers          ${tiers}${R2}`);
      }
    } else {
      console.log(`    ${D2}This session   no tracked spend${R2}`);
    }
    if (dailySpent > 0) {
      const dailyLimit = parseFloat(process.env.ODAI_DAILY_BUDGET || "5");
      const pct = Math.round((dailySpent / dailyLimit) * 100);
      const bar = "█".repeat(Math.round(pct / 5)).padEnd(20, "░");
      const col = pct < 50 ? G2 : pct < 80 ? W2 : "\x1b[31m";
      console.log(`    ${B2}Today${R2}         ${col}$${dailySpent.toFixed(4)}${R2} / $${dailyLimit.toFixed(2)} ${D2}${bar} ${pct}%${R2}`);
    }
    console.log(`    ${B2}All time${R2}      ${D2}$${totalSpent.toFixed(4)} (${Object.keys(b.tasks || {}).length} tasks)${R2}`);
    if (tieredTotal > 0) {
      const fastPct = Math.round((tierCount.fast / tieredTotal) * 100);
      console.log(`    ${D2}Model routing  ${tierCount.fast}×fast  ${tierCount.balanced}×balanced  ${tierCount.deep}×deep  (${fastPct}% cheap)${R2}`);
    }
    // Recent sessions (last 5)
    const sessions = Object.entries(b.sessions || {})
      .sort(([a], [bb]) => bb.localeCompare(a))
      .slice(0, 5);
    if (sessions.length > 1) {
      console.log(`    ${D2}Recent sessions:${R2}`);
      for (const [key, s] of sessions) {
        const tasks = (s.tasks || []).length;
        console.log(`      ${D2}${key}  $${(s.total_cost || 0).toFixed(4)} · ${tasks} tasks${R2}`);
      }
    }
    console.log();
    return;
  }
  if (sub === "estimate") {
    const gate = requirePlan("pro", "Swarm Estimate", target);
    if (gate) { log(gate.error); log(gate.hint); return; }
    const goal = args.find((_, i) => args[i - 1] === "--goal") || "";
    if (!goal) { console.log("Usage: 0dai swarm estimate --goal '...' [--agent claude|codex] [--model tier] [--json]"); return; }
    const agent = args.find((_, i) => args[i - 1] === "--agent") || "";
    const model = args.find((_, i) => args[i - 1] === "--model") || "";
    const asJson = args.includes("--json");
    // Call API for cost estimate
    const identity = shared.buildProjectIdentity(target, shared.collectMetadata(target));
    shared.apiCall("/v1/swarm/estimate", { goal, agent, model_tier: model, project_id: identity.project_id }).then((result) => {
      if (result.error) { log(`error: ${result.error}`); return; }
      if (asJson) { console.log(JSON.stringify(result, null, 2)); return; }
      log(`Cost estimate for: ${goal}`);
      console.log(`  ${D}Estimated: $${(result.estimated_cost_usd || 0).toFixed(4)} · ${result.estimated_tokens || "?"} tokens · ${result.estimated_time_s || "?"}s${R}`);
      if (result.model_recommendation) console.log(`  ${T}Recommended: ${result.model_recommendation}${R}`);
      if (result.tier_breakdown) {
        for (const [tier, cost] of Object.entries(result.tier_breakdown)) {
          console.log(`    ${tier}: $${cost.toFixed(4)}`);
        }
      }
    });
    return;
  }
  if (sub === "quality") {
    const scorerScript = findRepoScript(target, "quality_scorer.py");
    if (!scorerScript) { log("quality scorer unavailable"); return; }
    const fwd = [scorerScript, "--target", target];
    if (args.includes("--json")) fwd.push("--json");
    for (let i = 2; i < args.length; i++) {
      if (args[i] === "--last" && args[i + 1]) { fwd.push("--last", args[i + 1]); i++; }
      else if (args[i] === "--details" && args[i + 1]) { fwd.push("--details", args[i + 1]); i++; }
    }
    const result = spawnSync("python3", fwd, { stdio: "inherit", timeout: 15000 });
    if (typeof result.status === "number" && result.status !== 0) process.exit(result.status);
    return;
  }
  console.log("Usage: 0dai swarm [status|add|delegate|budget|estimate|quality] [--task '...'] [--to agent]");
  console.log("  quality   Show quality scores for recent tasks (--last N / --details TASK_ID)");
}

module.exports = { cmdSwarm };
