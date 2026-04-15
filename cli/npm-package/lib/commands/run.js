"use strict";
const shared = require("../shared");
const { log, T, R, D, fs, path, apiCall } = shared;

async function cmdRun(goal, target, args = []) {
  if (!goal) {
    console.log(`Usage: 0dai run <goal> [--dry-run] [--agent claude|codex|gemini]`);
    console.log(`  Example: 0dai run "add dark mode to settings page"`);
    return;
  }

  const dryRun = args.includes("--dry-run");
  const agentIdx = args.indexOf("--agent");
  const agentOverride = agentIdx >= 0 ? args[agentIdx + 1] : null;

  // Read project context
  let stack = "generic", agents = ["claude"], commands = {};
  try {
    const disc = JSON.parse(fs.readFileSync(path.join(target, "ai", "manifest", "discovery.json"), "utf8"));
    stack = disc.stack || "generic";
    agents = disc.selected_agents || ["claude"];
  } catch {}

  if (!dryRun) process.stdout.write(`${T}[0dai]${R} decomposing goal...`);
  const result = await apiCall("/v1/run", { goal, context: { stack, agents, commands } });
  if (!dryRun) process.stdout.write("\r" + " ".repeat(40) + "\r");

  if (result.error) { log(`error: ${result.error}`); return; }

  const tasks = result.tasks || [];
  if (!tasks.length) { log("no tasks returned"); return; }

  console.log(`\n  ${T}Goal:${R} ${goal}`);
  console.log(`  Decomposed into ${tasks.length} task${tasks.length === 1 ? "" : "s"}:\n`);

  for (let i = 0; i < tasks.length; i++) {
    const t = tasks[i];
    const agent = agentOverride || t.assigned_to;
    console.log(`  ${T}${i + 1}.${R} ${t.title}`);
    console.log(`     ${D}→ ${agent}  [${t.model_tier}]${t.description ? "  " + t.description : ""}${R}`);
  }

  if (dryRun) {
    console.log(`\n  ${D}[dry-run] would create ${tasks.length} task(s) in swarm queue${R}\n`);
    return;
  }

  // Create queue entries
  const queueDir = path.join(target, "ai", "swarm", "queue");
  try { fs.mkdirSync(queueDir, { recursive: true }); } catch {}

  const created = [];
  for (const t of tasks) {
    const ts = Date.now();
    const rand = Math.random().toString(36).slice(2, 6);
    const id = `run-${ts}-${rand}`;
    const entry = {
      id,
      title: t.title,
      description: t.description || "",
      assigned_to: agentOverride || t.assigned_to,
      model_tier: t.model_tier,
      created_by: "run",
      created_at: new Date().toISOString(),
      context: { goal },
    };
    try {
      fs.writeFileSync(path.join(queueDir, `${id}.json`), JSON.stringify(entry, null, 2));
      created.push(id);
    } catch (e) { log(`warn: could not write task ${id}: ${e.message}`); }
  }

  console.log(`\n  ${T}✓${R} ${created.length} task${created.length === 1 ? "" : "s"} added to swarm queue`);
  console.log(`  ${D}Monitor: 0dai watch  |  Queue: 0dai swarm status${R}\n`);
}

module.exports = { cmdRun };
