"use strict";
const shared = require("../shared");
const { fs, path } = shared;

function cmdMetrics(target) {
  const ai = path.join(target, "ai");
  const G = "\x1b[32m", W = "\x1b[33m", R2 = "\x1b[0m", D = "\x1b[2m",
        B = "\x1b[34m", T = "\x1b[36m", M = "\x1b[35m";

  // --- Data sources ---
  let stats = {}, budget = {}, discovery = {};
  try { stats  = JSON.parse(fs.readFileSync(path.join(ai, "feedback", ".usage_stats.json"), "utf8")); } catch {}
  try { budget = JSON.parse(fs.readFileSync(path.join(ai, "swarm", "budget.json"), "utf8")); } catch {}
  try { discovery = JSON.parse(fs.readFileSync(path.join(ai, "manifest", "discovery.json"), "utf8")); } catch {}

  const projectName = discovery.project_name || path.basename(target);
  const stack = discovery.stack || "?";
  const totalSessions = stats.total_sessions || 0;
  const agentBreakdown = stats.agents || {};
  const layerInfo = stats.layer || {};
  const lastSession = stats.last_session ? new Date(stats.last_session) : null;
  const layerVersion = stats.version || "?";

  // Swarm tasks: count done files
  let tasksDone = 0, tasksQueue = 0;
  const doneDir = path.join(ai, "swarm", "done");
  const queueDir = path.join(ai, "swarm", "queue");
  try { tasksDone = fs.readdirSync(doneDir).filter(f => f.endsWith(".json")).length; } catch {}
  try { tasksQueue = fs.readdirSync(queueDir).filter(f => f.endsWith(".json")).length; } catch {}

  // Activity: count events from activity.jsonl
  let activityEvents = 0;
  try {
    const lines = fs.readFileSync(path.join(ai, "swarm", "activity.jsonl"), "utf8").trim().split("\n").filter(Boolean);
    activityEvents = lines.length;
  } catch {}

  // Feedback submissions
  let feedbackCount = layerInfo.feedback_reports || 0;

  // Budget totals
  const totalSpent = budget.total_spent || 0;
  const sessionsWithBudget = Object.keys(budget.sessions || {}).length;

  // --- Effectiveness score (0-100) ---
  let score = 0, scoreNotes = [];

  // Sessions depth: 1 = tried, 3 = habit forming, 7 = regular use
  const sessionScore = Math.min(Math.floor((totalSessions / 7) * 35), 35);
  score += sessionScore;
  if (totalSessions === 0)       scoreNotes.push("not started");
  else if (totalSessions === 1)  scoreNotes.push("first session");
  else if (totalSessions < 3)    scoreNotes.push("early");
  else if (totalSessions < 7)    scoreNotes.push("habit forming");
  else                           scoreNotes.push("regular use");

  // Delegation: did they delegate to swarm?
  const delegationScore = tasksDone > 0 ? Math.min(Math.floor((tasksDone / 5) * 30), 30) : 0;
  score += delegationScore;
  if (tasksDone > 0) scoreNotes.push(`${tasksDone} tasks delegated`);

  // Feedback: submitted = trust signal
  const feedbackScore = feedbackCount > 0 ? 20 : 0;
  score += feedbackScore;
  if (feedbackCount > 0) scoreNotes.push("feedback submitted");

  // Layer completeness: has playbooks and commands?
  const layerScore = (layerInfo.playbooks && layerInfo.commands) ? 15 : (layerInfo.commands ? 8 : 0);
  score += layerScore;

  const scoreColor = score >= 70 ? G : score >= 40 ? W : "\x1b[31m";
  const bar = "█".repeat(Math.round(score / 5)).padEnd(20, "░");

  // --- Output ---
  console.log(`\n  ${T}Metrics${R2}  ${D}${projectName} · ${stack} · ai v${layerVersion}${R2}\n`);

  // Effectiveness score
  console.log(`  ${B}Effectiveness${R2}`);
  console.log(`    ${scoreColor}${score}/100${R2}  ${D}${bar}${R2}`);
  if (scoreNotes.length) console.log(`    ${D}${scoreNotes.join("  ·  ")}${R2}`);

  // Adoption funnel
  console.log(`\n  ${B}Adoption funnel${R2}`);
  const funnelStep = (label, value, done, hint) => {
    const icon = done ? `${G}✓${R2}` : `${D}○${R2}`;
    const val = value !== null ? `  ${D}${value}${R2}` : "";
    const h = !done && hint ? `  ${D}← ${hint}${R2}` : "";
    console.log(`    ${icon}  ${label}${val}${h}`);
  };
  funnelStep("Initialized",       `ai/ v${layerVersion}`,    true);
  funnelStep("Returned (>1 session)",  `${totalSessions} total`,  totalSessions > 1, "run 0dai reflect after each session");
  funnelStep("Used swarm delegation",  tasksDone > 0 ? `${tasksDone} tasks done` : null, tasksDone > 0, "try: 0dai swarm add --task '...' --to codex");
  funnelStep("Submitted feedback",     feedbackCount > 0 ? `${feedbackCount} reports` : null, feedbackCount > 0, "0dai feedback log + push");

  // Session stats
  if (totalSessions > 0) {
    console.log(`\n  ${B}Sessions${R2}`);
    console.log(`    Total      ${totalSessions}`);
    if (lastSession) {
      const daysAgo = Math.floor((Date.now() - lastSession.getTime()) / 86400000);
      const when = daysAgo === 0 ? "today" : daysAgo === 1 ? "yesterday" : `${daysAgo}d ago`;
      console.log(`    Last       ${when}`);
    }
    const agentEntries = Object.entries(agentBreakdown).sort((a, b) => b[1] - a[1]);
    if (agentEntries.length) {
      console.log(`    Agents     ${agentEntries.map(([a, n]) => `${a}: ${n}`).join("  ")}`);
    }
    if (sessionsWithBudget > 0 && totalSpent > 0) {
      console.log(`    Cost       $${totalSpent.toFixed(4)} total  ${D}(${sessionsWithBudget} sessions tracked)${R2}`);
    }
  }

  // Delegation stats
  if (tasksDone > 0 || tasksQueue > 0) {
    console.log(`\n  ${B}Delegation${R2}`);
    if (tasksDone > 0) console.log(`    Done       ${G}${tasksDone}${R2}`);
    if (tasksQueue > 0) console.log(`    Queue      ${W}${tasksQueue}${R2}`);
    if (activityEvents > 0) console.log(`    Events     ${activityEvents}`);
  }

  // Layer health
  console.log(`\n  ${B}ai/ layer${R2}`);
  const checks = [
    ["commands.yaml",  layerInfo.commands],
    ["playbooks",      layerInfo.playbooks],
    ["personas",       layerInfo.personas],
    ["session roaming", layerInfo.session_active],
    ["swarm queue",    (layerInfo.swarm_queue || 0) > 0],
  ];
  for (const [label, ok] of checks) {
    const icon = ok ? `${G}✓${R2}` : `${D}—${R2}`;
    console.log(`    ${icon}  ${label}`);
  }

  // Next suggested action
  console.log(`\n  ${B}Next${R2}`);
  if (totalSessions === 0)   console.log(`    ${D}Start a Claude Code session — session_start hook will print project context${R2}`);
  else if (tasksDone === 0)  console.log(`    ${D}Try delegating a task: 0dai swarm add --task "write tests for auth module" --to codex${R2}`);
  else if (feedbackCount === 0) console.log(`    ${D}Submit feedback: 0dai feedback log --type positive --detail "what worked"${R2}`);
  else                       console.log(`    ${D}Score ${score}/100 — keep delegating and submitting feedback${R2}`);

  console.log();
}

module.exports = { cmdMetrics };
