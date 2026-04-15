"use strict";
const shared = require("../shared");
const { T, fs, path } = shared;

function cmdWatch(target, args) {
  const isTTY = process.stdout.isTTY;
  const B2 = isTTY ? "\x1b[1m" : "";
  const DIM = isTTY ? "\x1b[2m" : "";
  const G = isTTY ? "\x1b[32m" : "";
  const Y = isTTY ? "\x1b[33m" : "";
  const C = isTTY ? "\x1b[36m" : "";
  const M = isTTY ? "\x1b[35m" : "";
  const R2 = isTTY ? "\x1b[0m" : "";

  const swarmDir = path.join(target, "ai", "swarm");
  const interval = parseInt(args.find((_, i) => args[i - 1] === "--interval") || "3", 10) * 1000;

  function readDir(dir) {
    try {
      return fs.readdirSync(dir)
        .filter(f => f.endsWith(".json"))
        .map(f => { try { return JSON.parse(fs.readFileSync(path.join(dir, f), "utf8")); } catch { return null; } })
        .filter(Boolean);
    } catch { return []; }
  }

  function ago(ts) {
    if (!ts) return "—";
    const s = Math.floor((Date.now() - new Date(ts).getTime()) / 1000);
    if (s < 60) return `${s}s`;
    if (s < 3600) return `${Math.floor(s / 60)}m`;
    return `${Math.floor(s / 3600)}h`;
  }

  function tierColor(tier) {
    if (tier === "deep") return M;
    if (tier === "fast") return C;
    return G;
  }

  function statusColor(status) {
    if (status === "done") return G;
    if (status === "active" || status === "running") return Y;
    if (status === "failed") return "\x1b[31m";
    return DIM;
  }

  function render() {
    const queue  = readDir(path.join(swarmDir, "queue"));
    const active = readDir(path.join(swarmDir, "active"));
    const done   = readDir(path.join(swarmDir, "done")).sort(
      (a, b) => new Date(b.completed_at || b.created_at) - new Date(a.completed_at || a.created_at)
    ).slice(0, 8);

    const lines = [];
    const w = process.stdout.columns || 100;
    const sep = DIM + "─".repeat(Math.min(w, 96)) + R2;

    lines.push(`\n  ${B2}${T}0dai watch${R2}  ${DIM}${new Date().toLocaleTimeString()}  (q to quit)${R2}`);
    lines.push(sep);

    const header = `  ${"STATUS".padEnd(9)} ${"AGENT".padEnd(10)} ${"TIER".padEnd(9)} ${"AGE".padEnd(6)}  TITLE`;
    lines.push(DIM + header + R2);
    lines.push(sep);

    const printTask = (t, statusOverride) => {
      const status = statusOverride || t.status || "queued";
      const sc = statusColor(status);
      const tc = tierColor(t.model_tier);
      const title = (t.title || "—").slice(0, Math.max(20, w - 42));
      const age = ago(t.created_at);
      lines.push(
        `  ${sc}${status.padEnd(9)}${R2} ` +
        `${DIM}${(t.assigned_to || "—").padEnd(10)}${R2} ` +
        `${tc}${(t.model_tier || "—").padEnd(9)}${R2} ` +
        `${DIM}${age.padEnd(6)}${R2}  ${title}`
      );
    };

    if (active.length) {
      active.forEach(t => printTask(t, "active"));
    }
    if (queue.length) {
      queue.forEach(t => printTask(t, "queued"));
    }
    if (!active.length && !queue.length) {
      lines.push(`  ${DIM}No tasks in queue or active.${R2}`);
    }

    lines.push(sep);
    if (done.length) {
      lines.push(`  ${DIM}Recently done:${R2}`);
      done.forEach(t => printTask(t, "done"));
    }

    lines.push(`\n  ${DIM}queue: ${queue.length}  active: ${active.length}  done (total): ${readDir(path.join(swarmDir, "done")).length}${R2}\n`);

    if (isTTY) process.stdout.write("\x1b[2J\x1b[H");
    console.log(lines.join("\n"));
  }

  render();
  const timer = setInterval(render, interval);

  // Exit on 'q' or Ctrl+C
  if (isTTY && process.stdin.setRawMode) {
    process.stdin.setRawMode(true);
    process.stdin.resume();
    process.stdin.once("data", (key) => {
      clearInterval(timer);
      process.stdin.setRawMode(false);
      process.exit(0);
    });
  }
  process.on("SIGINT", () => { clearInterval(timer); process.exit(0); });
}

module.exports = { cmdWatch };
