"use strict";
const shared = require("../shared");
const { T, R } = shared;

function cmdModels(filter) {
  // Scores from benchmark_models.py (3-task: read/count/review, 2026-04-06)
  const MODELS = [
    { name: "Claude Opus 4.6",   tier: "deep",     score: 95, cli: "claude",   flag: "--model opus" },
    { name: "GPT-5.4-mini",      tier: "fast",     score: 93, cli: "codex",    flag: "-m gpt-5.4-mini",      tested: true },
    { name: "MiniMax M2.7",      tier: "balanced", score: 93, cli: "opencode", flag: "-m opencode-go/minimax-m2.7",   tested: true },
    { name: "Claude Sonnet 4.6", tier: "balanced", score: 90, cli: "claude",   flag: "--model sonnet" },
    { name: "GPT-5.4",           tier: "balanced", score: 90, cli: "codex",    flag: "-m gpt-5.4",           tested: true },
    { name: "Kimi K2.5",         tier: "balanced", score: 88, cli: "opencode", flag: "-m opencode-go/kimi-k2.5",      tested: true },
    { name: "Qwen 3.6+ Free",    tier: "free",     score: 88, cli: "opencode", flag: "-m opencode/qwen3.6-plus-free", tested: true },
    { name: "Gemini 3.1 Pro",    tier: "balanced", score: 85, cli: "gemini",   flag: "-m gemini-3.1-pro" },
    { name: "GPT-5.3 Codex",     tier: "deep",     score: 83, cli: "codex",    flag: "-m gpt-5.3-codex",      tested: true },
    { name: "GPT-5.3 Spark",     tier: "fast",     score: 82, cli: "codex",    flag: "-m gpt-5.3-codex-spark" },
    { name: "Claude Haiku 4.5",  tier: "fast",     score: 78, cli: "claude",   flag: "--model haiku" },
    { name: "Gemini 3 Flash",    tier: "fast",     score: 77, cli: "gemini",   flag: "-m gemini-3-flash" },
    { name: "Mimo v2 Pro",       tier: "fast",     score: 74, cli: "opencode", flag: "-m opencode-go/mimo-v2-pro",    tested: true },
    { name: "GPT-5.4 (opencode)",tier: "fast",     score: 74, cli: "opencode", flag: "-m openai/gpt-5.4",            tested: true },
    { name: "GPT-5.2",           tier: "balanced", score: 87, cli: "codex",    flag: "-m gpt-5.2",           tested: true },
    { name: "MiniMax M2.5",      tier: "slow",     score: 57, cli: "opencode", flag: "-m opencode-go/minimax-m2.5",   tested: true },
  ];

  const { execFileSync } = require("child_process");
  const available = new Set();
  for (const cli of ["claude", "codex", "opencode", "gemini", "aider"]) {
    try { execFileSync("/bin/sh", ["-c", `command -v ${cli}`], { stdio: "ignore" }); available.add(cli); } catch {}
  }

  const isTTY = process.stdout.isTTY;
  const Y  = isTTY ? "\x1b[33m" : "";
  const G  = isTTY ? "\x1b[32m" : "";
  const DIM = isTTY ? "\x1b[2m" : "";

  let models = [...MODELS].sort((a, b) => b.score - a.score);
  if (filter === "--fast")      models = models.filter(m => m.tier === "fast");
  if (filter === "--balanced")  models = models.filter(m => m.tier === "balanced");
  if (filter === "--deep")      models = models.filter(m => m.tier === "deep");
  if (filter === "--available") models = models.filter(m => available.has(m.cli));

  const tc = (t) => t === "deep" ? T : t === "balanced" ? G : DIM;
  console.log(`\n  ${T}0dai${R} model ratings — ${models.length} models\n`);
  console.log(`  ${"SCORE".padEnd(6)} ${"MODEL".padEnd(22)} ${"TIER".padEnd(10)} ${"CLI".padEnd(10)} FLAG`);
  console.log(`  ${"-".repeat(64)}`);
  for (const m of models) {
    const dim = available.has(m.cli) ? "" : DIM;
    const mark = m.tested ? ` ${G}✓${R}` : "";
    console.log(`${dim}  ${Y}${String(m.score).padEnd(6)}${R} ${m.name.padEnd(22)} ${tc(m.tier)}${m.tier.padEnd(10)}${R} ${m.cli.padEnd(10)} ${DIM}${m.flag}${R}${mark}${dim ? R : ""}`);
  }
  console.log(`\n  ${DIM}✓ = swarm-benchmarked  |  dimmed = CLI not installed${R}`);
  console.log(`  ${DIM}Filter: --fast  --balanced  --deep  --available${R}`);
  console.log(`  ${DIM}Full table: https://0dai.dev/models${R}\n`);
}

async function cmdModelsRecommend(target, args) {
  const shared = require("../shared");
  const { log, T, R, D, findRepoScript, spawnSync, requirePlan } = shared;

  const gate = requirePlan("pro", "Model Recommend", target);
  if (gate) { log(gate.error); log(gate.hint); return; }

  const taskType = args.find((_, i) => args[i - 1] === "--task") || "";
  const goal = args.find((_, i) => args[i - 1] === "--goal") || "";
  const maxCost = parseFloat(args.find((_, i) => args[i - 1] === "--max-cost") || "0");
  const minQuality = parseFloat(args.find((_, i) => args[i - 1] === "--min-quality") || "0");
  const asJson = args.includes("--json");

  if (!taskType && !goal) {
    console.log("Usage: 0dai models recommend --task TYPE [--goal '...'] [--max-cost N] [--min-quality N] [--json]");
    console.log("  TYPE: feat, fix, refactor, test, docs");
    return;
  }

  const recScript = findRepoScript(target, "model_router.py");
  if (!recScript) { log("model router unavailable"); return; }

  const fwd = [recScript, "recommend", "--target", target];
  if (taskType) fwd.push("--task", taskType);
  if (goal) fwd.push("--goal", goal);
  if (maxCost > 0) fwd.push("--max-cost", String(maxCost));
  if (minQuality > 0) fwd.push("--min-quality", String(minQuality));
  if (asJson) fwd.push("--json");

  const result = spawnSync("python3", fwd, { stdio: "inherit" });
  if (typeof result.status === "number" && result.status !== 0) process.exit(result.status);
}

module.exports = { cmdModels, cmdModelsRecommend };
