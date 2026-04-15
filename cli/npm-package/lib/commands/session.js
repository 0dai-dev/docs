"use strict";
const shared = require("../shared");
const { log, fs, path, requirePlan } = shared;

function cmdSession(target, sub, args) {
  const sessFile = path.join(target, "ai", "sessions", "active.json");
  const sessDir = path.dirname(sessFile);

  if (sub === "save") {
    const gate = requirePlan("pro", "Session Roaming", target);
    if (gate) {
      log(gate.error);
      log(gate.hint);
      return;
    }
    fs.mkdirSync(sessDir, { recursive: true });
    const goal = args.find((_, i) => args[i - 1] === "--goal") || "";
    const summary = args.find((_, i) => args[i - 1] === "--summary") || "";
    const session = {
      id: `sess-${Date.now()}`,
      started: new Date().toISOString(),
      current_agent: "cli",
      task: { goal: goal || summary || "active session", status: "in_progress" },
      handoff_notes: summary,
      context: { files_touched: [] },
    };
    if (fs.existsSync(sessFile)) {
      const existing = JSON.parse(fs.readFileSync(sessFile, "utf8"));
      existing.handoff_notes = summary || existing.handoff_notes;
      if (goal) existing.task.goal = goal;
      existing.updated = new Date().toISOString();
      fs.writeFileSync(sessFile, JSON.stringify(existing, null, 2));
      log("session updated");
    } else {
      fs.writeFileSync(sessFile, JSON.stringify(session, null, 2));
      log(`session started: ${session.id}`);
    }
    return;
  }
  if (sub === "status") {
    if (!fs.existsSync(sessFile)) { log("no active session"); return; }
    const s = JSON.parse(fs.readFileSync(sessFile, "utf8"));
    log(`session: ${(s.task || {}).goal || "?"}`);
    console.log(`  agent: ${s.current_agent || "?"}`);
    if (s.handoff_notes) console.log(`  handoff: ${s.handoff_notes}`);
    return;
  }
  if (sub === "complete") {
    if (!fs.existsSync(sessFile)) { log("no active session"); return; }
    const archiveDir = path.join(target, "ai", "sessions", "archive");
    fs.mkdirSync(archiveDir, { recursive: true });
    const s = JSON.parse(fs.readFileSync(sessFile, "utf8"));
    fs.writeFileSync(path.join(archiveDir, `${s.id || "session"}.json`), JSON.stringify(s, null, 2));
    fs.unlinkSync(sessFile);
    log(`session ${s.id} archived`);
    return;
  }
  console.log("Usage: 0dai session [save|status|complete] [--goal '...'] [--summary '...']");
}

module.exports = { cmdSession };
