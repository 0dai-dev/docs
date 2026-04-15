"use strict";
const shared = require("../shared");
const { log, T, R, D, fs, path, spawnSync, findRepoScript, getSwarmQuotaLocal, _detectPlanLocal, PLAN_LEVELS } = shared;

function cmdStatus(target) {
  const ai = path.join(target, "ai");
  let v = "?", stack = "?";
  try { v = fs.readFileSync(path.join(ai, "VERSION"), "utf8").trim(); } catch {}
  try { stack = JSON.parse(fs.readFileSync(path.join(ai, "manifest", "discovery.json"), "utf8")).stack || "?"; } catch {}
  log(`v${v} | stack: ${stack}`);

  const count = (dir) => { try { return fs.readdirSync(dir).filter(f => f.endsWith(".json")).length; } catch { return 0; } };
  const q = count(path.join(ai, "swarm", "queue"));
  const a = count(path.join(ai, "swarm", "active"));
  const d = count(path.join(ai, "swarm", "done"));
  if (q || a || d) console.log(`  swarm: ${q} queued, ${a} active, ${d} done`);

  // Swarm quota
  const quota = getSwarmQuotaLocal(target);
  if (quota.plan === "free") {
    console.log(`  swarm quota: ${D}locked (Free) — upgrade for ${quota.daily_limit} tasks/day${R}`);
  } else {
    console.log(`  swarm quota: ${quota.used_today}/${quota.daily_limit} tasks today (${quota.plan})`);
  }

  // Session roaming status
  const sessPlan = _detectPlanLocal(target);
  const sessLocked = PLAN_LEVELS[sessPlan] < PLAN_LEVELS["pro"];
  if (sessLocked) {
    console.log(`  session roaming: ${D}locked (Free) — upgrade to save/resume sessions${R}`);
  } else {
    console.log(`  session roaming: ${T}available (${sessPlan})${R}`);
  }

  try {
    const s = JSON.parse(fs.readFileSync(path.join(ai, "sessions", "active.json"), "utf8"));
    console.log(`  session: ${(s.task || {}).goal || "?"} (agent: ${s.current_agent || "?"})`);
  } catch {}

  // Anti-pattern warnings count
  try {
    const ds = findRepoScript(target, "anti_pattern_detector.py");
    if (ds) {
      const wr = spawnSync("python3", [ds, "count", "--target", target],
                           { stdio: ["ignore", "pipe", "ignore"], encoding: "utf8", timeout: 5000 });
      if (wr.status === 0 && wr.stdout) {
        const wc = JSON.parse(wr.stdout.trim());
        if (wc.count > 0) console.log(`  warnings: ${wc.count} active — run: 0dai experience warnings`);
      }
    }
  } catch {}

  // First-status tip (shows once after init)
  try { require("../onboarding").showFirstStatusTip(target); } catch {}

  // Drift warning (lightweight)
  try {
    const ds = findRepoScript(target, "drift_detector.py");
    if (ds) {
      const dr = spawnSync("python3", [ds, "report", "--target", target],
                           { stdio: ["ignore", "pipe", "ignore"], encoding: "utf8", timeout: 5000 });
      if (dr.stdout && (dr.stdout.includes("MODIFIED") || dr.stdout.includes("CONTRADICTS"))) {
        console.log(`  drift: config changes detected — run: 0dai doctor --drift`);
      }
    }
  } catch {}
}

module.exports = { cmdStatus };
