"use strict";
const shared = require("../shared");
const { log, T, R, D, fs, path, PROJECTS_FILE } = shared;

function cmdPortfolio() {
  let projects = [];
  try { projects = JSON.parse(fs.readFileSync(PROJECTS_FILE, "utf8")).projects || []; } catch {}

  if (!projects.length) {
    log(`no projects registered yet`);
    console.log(`  Run ${D}0dai init${R} in a project to start tracking it.`);
    return;
  }

  const rows = [];
  let totalSessions = 0, totalScore = 0, scored = 0;

  for (const p of projects) {
    if (!fs.existsSync(p.path)) continue;

    let sessions = 0, lastSession = null, agentMap = {};
    try {
      const stats = JSON.parse(fs.readFileSync(path.join(p.path, "ai", "feedback", ".usage_stats.json"), "utf8"));
      sessions = stats.total_sessions || 0;
      lastSession = stats.last_session || null;
      agentMap = stats.agents || {};
    } catch {}

    let name = p.name, stack = p.stack;
    try {
      const disc = JSON.parse(fs.readFileSync(path.join(p.path, "ai", "manifest", "discovery.json"), "utf8"));
      name = disc.project_name || name;
      stack = disc.stack || stack;
    } catch {}

    // Effectiveness score (mirrors metrics command)
    let score = 0;
    if (sessions > 0) {
      score += Math.min(sessions * 5, 35);
      let done = 0;
      try { done = fs.readdirSync(path.join(p.path, "ai", "swarm", "done")).filter(f => f.endsWith(".json")).length; } catch {}
      if (done > 0) score += Math.min(done * 6, 30);
      try {
        const hasFb = fs.readdirSync(path.join(p.path, "ai", "feedback")).some(f => f.endsWith("-report.json"));
        if (hasFb) score += 20;
      } catch {}
      const layerFiles = ["ai/manifest/discovery.json", "ai/manifest/commands.yaml", "ai/playbooks/quick-start.md"];
      score += Math.round(layerFiles.filter(f => fs.existsSync(path.join(p.path, f))).length / layerFiles.length * 15);
    }

    totalSessions += sessions;
    if (sessions > 0) { totalScore += score; scored++; }

    const agentList = Object.keys(agentMap).join("·") || "—";

    let ago = "never";
    if (lastSession) {
      const h = Math.floor((Date.now() - new Date(lastSession).getTime()) / 3600000);
      const d = Math.floor(h / 24);
      if (h < 1) ago = "<1h ago";
      else if (h < 24) ago = `${h}h ago`;
      else if (d < 7) ago = `${d}d ago`;
      else ago = `${Math.floor(d / 7)}w ago`;
    }

    rows.push({ name, stack, score: sessions > 0 ? score : null, sessions, agents: agentList, ago });
  }

  if (!rows.length) {
    log("no projects found (paths may have moved)");
    return;
  }

  const nameW = Math.min(Math.max(...rows.map(r => r.name.length), 4), 28);
  const stackW = Math.min(Math.max(...rows.map(r => r.stack.length), 5), 16);

  console.log(`\n  ${T}Portfolio${R} — ${rows.length} project${rows.length === 1 ? "" : "s"}\n`);
  for (const r of rows) {
    const nm = r.name.slice(0, nameW).padEnd(nameW);
    const st = r.stack.slice(0, stackW).padEnd(stackW);
    const sc = r.score !== null ? `score ${String(r.score).padStart(3)}` : "         ";
    const se = `${String(r.sessions).padStart(2)} session${r.sessions === 1 ? " " : "s"}`;
    console.log(`  ${T}${nm}${R}  ${D}${st}${R}  ${sc}  ${se}  ${r.agents.padEnd(14)}  ${D}${r.ago}${R}`);
  }

  if (totalSessions > 0) {
    const avg = scored > 0 ? Math.round(totalScore / scored) : 0;
    const stacks = [...new Set(rows.map(r => r.stack))].length;
    console.log(`\n  ${D}${"─".repeat(70)}`);
    console.log(`  Total: ${totalSessions} sessions  ${stacks} stack${stacks === 1 ? "" : "s"}  avg effectiveness: ${avg}${R}\n`);
  } else {
    console.log(`\n  ${D}Tip: run '0dai init' in your projects to start tracking sessions.${R}\n`);
  }
}

module.exports = { cmdPortfolio };
