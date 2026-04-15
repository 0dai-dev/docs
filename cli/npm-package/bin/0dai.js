#!/usr/bin/env node
"use strict";

/**
 * 0dai CLI entry point — routing only.
 *
 * All command implementations live in lib/commands/*.js.
 * Shared config and utilities live in lib/shared.js.
 */

const shared = require("../lib/shared");
const { T, R, D, log, VERSION, fs, path, spawnSync, findRepoScript, checkVersion } = shared;

// --- Command imports ---
const { cmdAuthLogin, cmdAuthLogout, cmdRedeem, cmdAuthStatus, cmdActivateFree, cmdActivateStatus } = require("../lib/commands/auth");
const { cmdInit, cmdSync } = require("../lib/commands/init");
const { cmdDetect } = require("../lib/commands/detect");
const { cmdAudit } = require("../lib/commands/audit");
const { cmdDoctor } = require("../lib/commands/doctor");
const { cmdValidate } = require("../lib/commands/validate");
const { cmdUpdate } = require("../lib/commands/update");
const { cmdReflect } = require("../lib/commands/reflect");
const { cmdMetrics } = require("../lib/commands/metrics");
const { cmdStatus } = require("../lib/commands/status");
const { cmdPortfolio } = require("../lib/commands/portfolio");
const { cmdRun } = require("../lib/commands/run");
const { cmdWatch } = require("../lib/commands/watch");
const { cmdModels } = require("../lib/commands/models");
const { cmdSession } = require("../lib/commands/session");
const { cmdSwarm } = require("../lib/commands/swarm");
const { cmdFeedback, cmdFeedbackPush } = require("../lib/commands/feedback");
const { cmdGraph } = require("../lib/commands/graph");
const { cmdReport } = require("../lib/commands/report");
const { cmdExperience } = require("../lib/commands/experience");
const { cmdWorkspace } = require("../lib/commands/workspace");

async function main() {
  const args = process.argv.slice(2);
  let target = process.cwd();
  const ti = args.indexOf("--target");
  if (ti >= 0 && args[ti + 1]) { target = path.resolve(args[ti + 1]); args.splice(ti, 2); }

  const cmd = args[0] || "help";
  const sub = args[1] || "";

  // Non-blocking version check (runs in background, once per day)
  checkVersion();

  // Track first run for time-to-init telemetry
  try { require("../lib/onboarding").trackFirstRun(target); } catch {}

  // First-run wizard prompt for commands that need ai/
  if (["status", "doctor", "sync", "swarm", "detect", "validate", "reflect", "metrics", "experience", "graph", "session", "report"].includes(cmd)) {
    try {
      const { maybeWizard } = require("../lib/wizard");
      const handled = await maybeWizard(target, cmd);
      if (handled) return;
    } catch {}
  }

  switch (cmd) {
    case "quickstart": {
      const ob = require("../lib/onboarding");
      await ob.cmdQuickstart(target, { cmdDoctor, cmdStatus, cmdInit: (t, a) => cmdInit(t, a || []), log, ensureAuthenticated: shared.makeEnsureAuthenticated(cmdAuthLogin) });
      break;
    }
    case "run": await cmdRun(args[1] || "", target, args.slice(2)); break;
    case "watch": cmdWatch(target, args.slice(1)); break;
    case "audit": cmdAudit(target); break;
    case "security": {
      const subSec = args[1] || "";
      if (subSec === "install-hook") {
        const hooksDir = path.join(target, ".git", "hooks");
        if (!fs.existsSync(hooksDir)) { log("not a git repo"); break; }
        const hookPath = path.join(hooksDir, "pre-commit");
        const hookSource = path.join(__dirname, "..", "..", "..", "scripts", "hooks", "pre-commit.sh");
        if (fs.existsSync(hookSource)) {
          fs.copyFileSync(hookSource, hookPath);
          fs.chmodSync(hookPath, 0o755);
          log("pre-commit hook installed: " + hookPath);
        } else {
          // Inline install: copy from repo scripts if available
          const repoHook = findRepoScript(target, "hooks/pre-commit.sh");
          if (repoHook) {
            fs.copyFileSync(repoHook, hookPath);
            fs.chmodSync(hookPath, 0o755);
            log("pre-commit hook installed: " + hookPath);
          } else {
            log("hook source not found — run: 0dai security install-hook from repo root");
          }
        }
        break;
      }
      const secScript = findRepoScript(target, "scan_secrets.py");
      if (!secScript) { log("secret scanner unavailable"); break; }
      const fwd = [secScript, "--target", target];
      if (args.includes("--json")) fwd.push("--json");
      if (args.includes("--fix")) fwd.push("--fix");
      const sr = spawnSync("python3", fwd, { stdio: "inherit" });
      if (typeof sr.status === "number") process.exit(sr.status);
      break;
    }
    case "init": await cmdInit(target, args); break;
    case "sync": await cmdSync(target, args); break;
    case "detect": await cmdDetect(target); break;
    case "doctor":
      cmdDoctor(target);
      if (args.includes("--drift")) {
        const ds = findRepoScript(target, "drift_detector.py");
        if (ds) spawnSync("python3", [ds, "report", "--target", target], { stdio: "inherit" });
      }
      break;
    case "drift": {
      const ds = findRepoScript(target, "drift_detector.py");
      if (!ds) { log("drift detector unavailable"); break; }
      if (sub === "accept" && args[2]) {
        spawnSync("python3", [ds, "accept", args[2], "--target", target], { stdio: "inherit" });
      } else if (sub === "show" && args[2]) {
        spawnSync("python3", [ds, "show", args[2], "--target", target], { stdio: "inherit" });
      } else {
        spawnSync("python3", [ds, "report", "--target", target], { stdio: "inherit" });
      }
      break;
    }
    case "validate": cmdValidate(target); break;
    case "reflect": cmdReflect(target, args); break;
    case "update": cmdUpdate(args); break;
    case "metrics": cmdMetrics(target); break;
    case "portfolio": cmdPortfolio(); break;
    case "status": cmdStatus(target); break;
    case "auth":
      if (sub === "login") await cmdAuthLogin();
      else if (sub === "logout") cmdAuthLogout();
      else if (sub === "status") await cmdAuthStatus();
      else console.log("Usage: 0dai auth [login|logout|status]");
      break;
    case "activate":
      if (sub === "free" || !sub) await cmdActivateFree();
      else if (sub === "status") await cmdActivateStatus();
      else console.log("Usage: 0dai activate [free|status]");
      break;
    case "session": cmdSession(target, sub, args); break;
    case "swarm": cmdSwarm(target, sub, args); break;
    case "workspace": cmdWorkspace(target, sub, args.slice(2)); break;
    case "feedback": await cmdFeedback(target, sub, args); break;
    case "report": cmdReport(target, sub, args); break;
    case "experience": cmdExperience(target, sub, args); break;
    case "graph": await cmdGraph(target, sub, args); break;
    case "models": cmdModels(sub || args[1]); break;
    case "delegate": case "delegation": {
      const deScript = findRepoScript(target, "delegation_engine.py");
      if (!deScript) { log("delegation engine unavailable"); break; }
      const deCmd = cmd === "delegate" ? "delegate" : (sub || "show");
      const fwd = [deScript, deCmd, "--target", target];
      if (deCmd === "delegate") {
        // Find goal: first non-flag arg after delegate, or --goal value
        let goal = "";
        for (let i = 0; i < args.length; i++) {
          if (args[i] === "--goal" && args[i + 1]) { goal = args[i + 1]; i++; }
          else if (!args[i].startsWith("-") && !goal) goal = args[i];
        }
        if (sub && !sub.startsWith("-")) goal = goal || sub;
        if (goal) fwd.push(goal);
        for (let i = 0; i < args.length; i++) {
          if (args[i] === "--agent" && args[i + 1]) { fwd.push("--agent", args[i + 1]); i++; }
          else if (args[i] === "--model" && args[i + 1]) { fwd.push("--model", args[i + 1]); i++; }
          else if (args[i] === "--task-type" && args[i + 1]) { fwd.push("--task-type", args[i + 1]); i++; }
        }
        if (args.includes("--dry-run")) fwd.push("--dry-run");
      }
      if (args.includes("--json")) fwd.push("--json");
      const result = spawnSync("python3", fwd, { stdio: "inherit", timeout: 15000 });
      if (typeof result.status === "number" && result.status !== 0) process.exit(result.status);
      break;
    }
    case "redeem": await cmdRedeem(sub || args[1]); break;
    case "terminal": case "term":
      try {
        const SessionManager = require("../lib/session-manager");
        const sm = new SessionManager();
        if (sub === "launch" || !sub || sub.startsWith("--")) {
          const toolIdx = args.indexOf("--tool");
          const tool = toolIdx >= 0 && args[toolIdx + 1] ? args[toolIdx + 1] : "codex";
          const TOOL_CMDS = {
            codex:    { bin: "codex", args: [] },
            claude:   { bin: "claude", args: [] },
            gemini:   { bin: "gemini", args: [] },
            opencode: { bin: "opencode", args: [] },
            aider:    { bin: "aider", args: [] },
          };
          const toolConfig = TOOL_CMDS[tool];
          if (!toolConfig) {
            log(`unknown tool: ${tool}. Available: ${Object.keys(TOOL_CMDS).join(", ")}`);
            break;
          }
          const dashIdx = args.indexOf("--");
          const prompt = dashIdx >= 0 ? args.slice(dashIdx + 1).join(" ") : "";
          const spawnArgs = [...toolConfig.args];
          if (prompt) spawnArgs.push(prompt);
          const id = sm.spawn(toolConfig.bin, spawnArgs, target);
          log(`session ${id.slice(0, 8)} started (${tool})`);
          console.log(`  ${D}Ctrl+C to exit, session keeps running in background${R}`);
          console.log(`  ${D}Re-attach: 0dai terminal attach ${id.slice(0, 8)}${R}`);
          sm.attach(id);
        } else if (sub === "list") {
          const sessions = sm.list();
          if (!sessions.length) { log("no active sessions"); break; }
          for (const s of sessions) {
            const elapsed = Math.round((Date.now() - new Date(s.createdAt).getTime()) / 1000);
            console.log(`  ${s.id.slice(0, 8)} [${s.tool}] ${s.status} ${elapsed}s ${s.attached ? "(attached)" : ""}`);
          }
        } else if (sub === "attach") {
          const prefix = args[1] || "";
          if (!prefix) { log("usage: 0dai terminal attach <session-id-prefix>"); break; }
          const sessions = sm.list();
          const match = sessions.find(s => s.id.startsWith(prefix));
          if (!match) { log(`no running session matching '${prefix}'`); break; }
          log(`re-attaching to ${match.id.slice(0, 8)} (${match.tool})`);
          sm.attach(match.id);
        } else if (sub === "kill") {
          const prefix = args[1] || "";
          if (!prefix) { log("usage: 0dai terminal kill <session-id-prefix>"); break; }
          const all = Array.from(sm.sessions || []);
          let found = false;
          for (const [id] of all) {
            if (id.startsWith(prefix)) { sm.kill(id); log(`killed ${id.slice(0, 8)}`); found = true; }
          }
          if (!found) log(`no session matching '${prefix}'`);
        } else {
          console.log("Usage: 0dai terminal [launch|list|attach|kill] [--tool codex|claude|gemini|opencode|aider]");
          console.log("       0dai terminal --tool opencode -- 'fix the auth bug'");
        }
      } catch (e) {
        if (e.code === "MODULE_NOT_FOUND") log("install node-pty first: npm i -g node-pty");
        else log(`error: ${e.message}`);
      }
      break;
    case "--version": console.log(`${T}0dai${R} ${VERSION}`); break;
    case "help": case "--help": case "-h":
      console.log(`\n  ${T}0dai${R} v${VERSION} — One config for 5 AI agent CLIs\n`);
      console.log("Commands:");
      console.log("  run <goal>     AI-decompose goal → swarm tasks (auto-routed) [--dry-run]");
      console.log("  watch          Live task monitor: queue, active, recently done [--interval N]");
      console.log("  audit          Scan ai/ and agent configs for leaked secrets");
      console.log("  init           Initialize ai/ layer (via API) [--dry-run] [--minimal]");
      console.log("  sync           Update ai/ layer (via API) [--dry-run] [--quiet] [--force]");
      console.log("  detect         Show detected stack");
      console.log("  doctor         Check health + credentials checklist");
      console.log("  update         Update all installed agent CLIs to latest [--dry-run]");
      console.log("  validate       Validate ai/ layer completeness");
      console.log("  reflect        Session reflection: delivered, delegation rate, blockers");
      console.log("  metrics        Effectiveness score: adoption funnel, sessions, delegation");
      console.log("  portfolio      All tracked projects: score, sessions, agents, last activity");
      console.log("  status         Show maturity, swarm, session");
      console.log("  session save   Save session for roaming");
      console.log("  swarm status       Task queue & delegation");
      console.log("  swarm webhook add  Register webhook (fires on task done/failed)");
      console.log("  swarm webhook list Show registered webhooks");
      console.log("  swarm webhook test Send test ping to a webhook URL");
      console.log("  workspace init     Create tmux workspace config (auto-detect services)");
      console.log("  workspace up       Start all workspace sessions");
      console.log("  workspace status   Show session status table");
      console.log("  feedback push  Send feedback to 0dai");
      console.log("  report preview Preview privacy-safe project report");
      console.log("  report push    Send report to 0dai (with offline queue)");
      console.log("  report status  Show last report, queue, and auto-report status");
      console.log("  experience list  Show recent structured experience events");
      console.log("  experience stats Show success and cost stats by agent/model/type");
      console.log("  graph push     Upload local graph to server (Pro: edges, Free: nodes)");
      console.log("  graph pull     Download server graph and merge locally");
      console.log("  graph status   Show local graph stats and sync state");
      console.log("  models         Show model ratings (--fast/--balanced/--deep/--available)");
      console.log("  delegate       Auto-route task to best agent/model (0dai delegate 'goal')");
      console.log("  delegation show  Show current delegation policy");
      console.log("  terminal       Launch interactive agent session");
      console.log("  auth login     Authenticate (device code flow)");
      console.log("  auth logout    Remove credentials");
      console.log("  auth status    Show account and usage");
      console.log("  activate free  Claim free activation license");
      console.log("  activate status Show activation and bound-project status");
      console.log("  redeem <CODE>  Redeem a plan upgrade code");
      console.log("  --version\n");
      console.log("https://0dai.dev");
      break;
    default:
      log(`unknown command: ${cmd}. Run '0dai --help'`);
      process.exit(1);
  }
}

main().catch((e) => { log(`${e.message}`); process.exit(1); });
