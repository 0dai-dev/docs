"use strict";
const shared = require("../shared");
const { T, R, D, fs, path } = shared;

function cmdReflect(target, args) {
  const ai = path.join(target, "ai");
  const W = process.stdout.isTTY ? "\x1b[33m" : "";
  const G = process.stdout.isTTY ? "\x1b[32m" : "";
  const R2 = process.stdout.isTTY ? "\x1b[0m" : "";
  const B = process.stdout.isTTY ? "\x1b[1m" : "";

  // Collect swarm done tasks
  const doneDir = path.join(ai, "swarm", "done");
  const queueDir = path.join(ai, "swarm", "queue");
  const activeDir = path.join(ai, "swarm", "active");
  const doneTasks = [], queueTasks = [];

  // -- how many days to look back (default 7)
  const daysArg = args.find((_, i) => args[i - 1] === "--days");
  const days = parseInt(daysArg || "7");
  const since = Date.now() - days * 24 * 60 * 60 * 1000;

  const readJsonDir = (dir) => {
    const out = [];
    try {
      for (const f of fs.readdirSync(dir).filter(f => f.endsWith(".json"))) {
        try { out.push(JSON.parse(fs.readFileSync(path.join(dir, f), "utf8"))); } catch {}
      }
    } catch {}
    return out;
  };

  const allDone = readJsonDir(doneDir).filter(t => {
    const ts = t.completed_at || t.created_at;
    return !ts || new Date(ts).getTime() >= since;
  });
  const allQueue = readJsonDir(queueDir);
  const allActive = readJsonDir(activeDir);

  // Aggregate by agent
  const byAgent = {};
  for (const t of allDone) {
    const a = t.assigned_to || t.agent || "unknown";
    if (!byAgent[a]) byAgent[a] = { done: 0, tasks: [] };
    byAgent[a].done++;
    byAgent[a].tasks.push(t.title || t.id || "?");
  }

  // Session data
  let sessionGoal = "?";
  try {
    const active = JSON.parse(fs.readFileSync(path.join(ai, "sessions", "active.json"), "utf8"));
    sessionGoal = (active.task || {}).goal || "?";
  } catch {}

  console.log(`\n  ${B}${T}0dai reflect${R2}${R} — last ${days} days\n`);

  // Goal
  if (sessionGoal !== "?") console.log(`  ${B}Goal${R2}      ${sessionGoal}`);

  // Delegation stats
  const totalDone = allDone.length;
  const totalPending = allQueue.length + allActive.length;
  const successRate = totalDone + totalPending > 0
    ? Math.round((totalDone / (totalDone + totalPending)) * 100)
    : null;

  console.log(`  ${B}Delivered${R2}  ${G}${totalDone}${R2} tasks completed`);
  if (totalPending) console.log(`  ${B}Remaining${R2}  ${W}${totalPending}${R2} tasks still pending`);
  if (successRate !== null) console.log(`  ${B}Rate${R2}       ${successRate >= 80 ? G : W}${successRate}%${R2} delegation success rate`);

  // By agent breakdown with per-agent completion rate
  const allPendingByAgent = {};
  for (const t of [...allQueue, ...allActive]) {
    const a = t.assigned_to || "unknown";
    allPendingByAgent[a] = (allPendingByAgent[a] || 0) + 1;
  }

  if (Object.keys(byAgent).length) {
    console.log(`\n  ${B}By agent:${R2}`);
    for (const [agent, data] of Object.entries(byAgent).sort((a, b) => b[1].done - a[1].done)) {
      const pending = allPendingByAgent[agent] || 0;
      const total = data.done + pending;
      const rate = total > 0 ? Math.round((data.done / total) * 100) : 100;
      const bar = "█".repeat(Math.min(data.done, 20));
      const rateStr = total > 1 ? ` (${rate >= 80 ? G : W}${rate}%${R2})` : "";
      console.log(`    ${(agent + " ").padEnd(14)} ${G}${bar}${R2} ${data.done}/${total}${rateStr}`);
    }
    // Agents with only pending tasks (never completed anything in window)
    for (const [agent, count] of Object.entries(allPendingByAgent)) {
      if (!byAgent[agent]) {
        console.log(`    ${(agent + " ").padEnd(14)} ${W}${"░".repeat(Math.min(count, 20))}${R2} 0/${count} ${W}(pending)${R2}`);
      }
    }
  }

  // Budget summary from budget.json
  const budgetFile = path.join(ai, "swarm", "budget.json");
  try {
    const budget = JSON.parse(fs.readFileSync(budgetFile, "utf8"));
    const today = new Date().toISOString().slice(0, 10);
    const sessionKey = process.env.ODAI_SESSION_ID ||
      new Date().toISOString().slice(0, 13).replace("T", "-"); // YYYY-MM-DD-HH
    const dailySpent = budget.daily?.[today] || 0;
    const totalSpent = budget.total_spent || 0;
    const sess = budget.sessions?.[sessionKey];

    // Tier distribution across all tasks
    const tierCount = { fast: 0, balanced: 0, deep: 0 };
    for (const t of Object.values(budget.tasks || {})) {
      if (t.tier && tierCount[t.tier] !== undefined) tierCount[t.tier]++;
    }
    const tieredTotal = tierCount.fast + tierCount.balanced + tierCount.deep;

    if (dailySpent > 0 || totalSpent > 0 || sess) {
      console.log(`\n  ${B}Budget:${R2}`);
      if (sess && sess.total_cost > 0) {
        const taskCount = (sess.tasks || []).length;
        const avgCost = taskCount > 0 ? (sess.total_cost / taskCount).toFixed(4) : "0";
        console.log(`    ${B}This session${R2}  $${sess.total_cost.toFixed(4)} · ${taskCount} tasks · avg $${avgCost}/task`);
        if (sess.tiers) {
          const tiers = Object.entries(sess.tiers).filter(([, n]) => n > 0).map(([t, n]) => `${n}×${t}`).join("  ");
          if (tiers) console.log(`    ${D}Tiers          ${tiers}${R2}`);
        }
      }
      if (dailySpent > 0) {
        const dailyLimit = parseFloat(process.env.ODAI_DAILY_BUDGET || "5");
        const pct = Math.round((dailySpent / dailyLimit) * 100);
        const bar = "█".repeat(Math.round(pct / 5)).padEnd(20, "░");
        const col = pct < 50 ? G : pct < 80 ? W : "\x1b[31m";
        console.log(`    ${B}Today${R2}         ${col}$${dailySpent.toFixed(4)}${R2} / $${dailyLimit.toFixed(2)} ${D}${bar} ${pct}%${R2}`);
      }
      if (totalSpent > 0) {
        console.log(`    ${B}All time${R2}      ${D}$${totalSpent.toFixed(4)}${R2}`);
      }
      if (tieredTotal > 0) {
        const fastPct = Math.round((tierCount.fast / tieredTotal) * 100);
        console.log(`    ${D}Model routing  ${tierCount.fast}×fast  ${tierCount.balanced}×balanced  ${tierCount.deep}×deep  (${fastPct}% cheap)${R2}`);
      }
    }
  } catch {}

  // Insights — learn from patterns
  if (totalDone >= 3) {
    const insights = [];
    // Best agent by completion rate
    const agentEntries = Object.entries(byAgent).map(([a, d]) => {
      const pending = allPendingByAgent[a] || 0;
      const total = d.done + pending;
      return { agent: a, done: d.done, total, rate: total > 0 ? d.done / total : 1 };
    });
    const best = agentEntries.sort((a, b) => b.rate - a.rate)[0];
    if (best && agentEntries.length > 1) {
      insights.push(`${best.agent} has the highest success rate (${Math.round(best.rate * 100)}%)`);
    }
    // Fastest agent by avg elapsed
    try {
      const budget = JSON.parse(fs.readFileSync(path.join(ai, "swarm", "budget.json"), "utf8"));
      const agentElapsed = {};
      const agentCounts = {};
      for (const t of Object.values(budget.tasks || {})) {
        if (t.elapsed > 0) {
          agentElapsed[t.agent] = (agentElapsed[t.agent] || 0) + t.elapsed;
          agentCounts[t.agent] = (agentCounts[t.agent] || 0) + 1;
        }
      }
      let fastest = null, fastestAvg = Infinity;
      for (const [a, total] of Object.entries(agentElapsed)) {
        const avg = total / agentCounts[a];
        if (avg < fastestAvg) { fastest = a; fastestAvg = avg; }
      }
      if (fastest && Object.keys(agentElapsed).length > 1) {
        insights.push(`${fastest} is fastest (avg ${Math.round(fastestAvg)}s per task)`);
      }
    } catch {}
    // Cost efficiency
    if (allDone.length > 0) {
      try {
        const budget = JSON.parse(fs.readFileSync(path.join(ai, "swarm", "budget.json"), "utf8"));
        if (budget.total_spent > 0) {
          const costPerTask = budget.total_spent / allDone.length;
          insights.push(`avg cost: $${costPerTask.toFixed(4)}/task`);
        }
      } catch {}
    }
    if (insights.length) {
      console.log(`\n  ${B}Insights:${R2}`);
      for (const i of insights) console.log(`    ${G}→${R2} ${i}`);
    }
  }

  // Remaining blockers
  if (allQueue.length) {
    console.log(`\n  ${B}Blockers / queue:${R2}`);
    for (const t of allQueue.slice(0, 8)) {
      const agent = t.assigned_to ? ` → ${t.assigned_to}` : "";
      console.log(`    ${W}•${R2} ${(t.title || t.id || "?").slice(0, 60)}${agent}`);
    }
    if (allQueue.length > 8) console.log(`    ${D}… and ${allQueue.length - 8} more${R2}`);
  }

  // No data
  if (!totalDone && !totalPending) {
    console.log(`  ${D}No swarm tasks found in the last ${days} days.${R2}`);
    console.log(`  ${D}Use '0dai swarm add --task "..." --to codex' to delegate tasks.${R2}`);
  }

  console.log();
}

module.exports = { cmdReflect };
