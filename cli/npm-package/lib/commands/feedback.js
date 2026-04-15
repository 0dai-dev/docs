"use strict";
const shared = require("../shared");
const { log, T, R, D, fs, path, apiCall } = shared;

async function cmdFeedbackPush(target) {
  const fbDir = path.join(target, "ai", "feedback");
  const items = [];

  // Collect from report JSON files
  try {
    for (const f of fs.readdirSync(fbDir)) {
      if (f.endsWith("-report.json") || (f.endsWith(".json") && f.match(/^\d{8}/))) {
        try {
          const d = JSON.parse(fs.readFileSync(path.join(fbDir, f), "utf8"));
          if (d.project || d.verdict) items.push({ type: "report", data: d, file: f });
        } catch {}
      }
    }
  } catch {}

  // Collect from operational.jsonl (feedback log entries)
  const jsonlPath = path.join(fbDir, "operational.jsonl");
  try {
    if (fs.existsSync(jsonlPath)) {
      const lines = fs.readFileSync(jsonlPath, "utf8").trim().split("\n").filter(Boolean);
      for (const line of lines) {
        try { items.push({ type: "log", data: JSON.parse(line) }); } catch {}
      }
    }
  } catch {}

  if (!items.length) {
    log("no feedback found");
    console.log(`  ${D}Log feedback first: 0dai feedback log --type suggestion --detail '...'${R}`);
    return;
  }

  // Push all items
  const report = {
    project: path.basename(target),
    entries: items.map(i => i.data),
    count: items.length,
    submitted_at: new Date().toISOString(),
  };
  log(`pushing ${items.length} feedback item(s)...`);
  const result = await apiCall("/v1/feedback", { report });
  if (result.received) {
    log(`received${result.issue ? `: ${result.issue}` : ""}`);
    if (result.bonus) log(`${T}bonus:${R} ${result.bonus}`);
    // Archive pushed entries
    if (fs.existsSync(jsonlPath)) {
      const archivePath = path.join(fbDir, `pushed-${Date.now()}.jsonl`);
      fs.renameSync(jsonlPath, archivePath);
    }
  } else {
    log(`error: ${result.error || "unknown"}`);
  }
}

async function cmdFeedback(target, sub, args) {
  const fbDir = path.join(target, "ai", "feedback");

  if (sub === "push") {
    return cmdFeedbackPush(target);
  }
  if (sub === "log") {
    const type = args.find((_, i) => args[i - 1] === "--type") || "suggestion";
    const detail = args.find((_, i) => args[i - 1] === "--detail") || "";
    if (!detail) { console.log("Usage: 0dai feedback log --type bug|suggestion|friction|positive --detail '...'"); return; }
    fs.mkdirSync(fbDir, { recursive: true });
    const entry = JSON.stringify({ ts: new Date().toISOString(), type, detail, agent: "cli" });
    fs.appendFileSync(path.join(fbDir, "operational.jsonl"), entry + "\n");
    log(`logged: [${type}] ${detail.slice(0, 60)}`);
    return;
  }
  if (sub === "list") {
    try {
      const files = fs.readdirSync(fbDir).filter(f => f.endsWith("-report.json"));
      if (!files.length) { log("no reports"); return; }
      for (const f of files) {
        try {
          const d = JSON.parse(fs.readFileSync(path.join(fbDir, f), "utf8"));
          console.log(`  ${f}: ${d.verdict || "?"} (${d.project || "?"})`);
        } catch {}
      }
    } catch { log("no feedback directory"); }
    return;
  }
  console.log("Usage: 0dai feedback [push|log|list] [--type ...] [--detail '...']");
}

module.exports = { cmdFeedbackPush, cmdFeedback };
