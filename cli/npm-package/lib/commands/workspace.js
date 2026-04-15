"use strict";
const shared = require("../shared");
const { log, T, R, D, fs, path, spawnSync } = shared;
const os = require("os");

const CONFIG_NAME = "workspace.json";

function findConfig(target) {
  const local = path.join(target, ".0dai", CONFIG_NAME);
  if (fs.existsSync(local)) return { file: local, scope: "local" };
  const globalFile = path.join(os.homedir(), ".0dai", CONFIG_NAME);
  if (fs.existsSync(globalFile)) return { file: globalFile, scope: "global" };
  return null;
}

function loadConfig(target) {
  const found = findConfig(target);
  if (!found) return null;
  try { return JSON.parse(fs.readFileSync(found.file, "utf8")); } catch { return null; }
}

function saveConfig(target, ws, globalFlag) {
  const configFile = globalFlag
    ? path.join(os.homedir(), ".0dai", CONFIG_NAME)
    : path.join(target, ".0dai", CONFIG_NAME);
  fs.mkdirSync(path.dirname(configFile), { recursive: true, mode: 0o700 });
  fs.writeFileSync(configFile, JSON.stringify(ws, null, 2) + "\n", { mode: 0o600 });
  return configFile;
}

function tmux(args) {
  try {
    return spawnSync("tmux", args, { encoding: "utf8", timeout: 5000 });
  } catch { return { status: 1, stderr: "tmux not found" }; }
}

function sessionName(name) {
  return "0dai-" + name.replace(/[^a-z0-9-]/gi, "-").toLowerCase();
}

function listTmuxSessions() {
  const r = tmux(["list-sessions", "-F", "#{session_name}\t#{session_created}\t#{pane_pid}"]);
  if (r.status !== 0) return [];
  return r.stdout.trim().split("\n").filter(Boolean).map(line => {
    const [name, created, pid] = line.split("\t");
    return { name, created, pid };
  });
}

// --- Auto-detection ---

function detectSessions(target) {
  const sessions = [];

  // API server
  if (fs.existsSync(path.join(target, "scripts", "api_server.py"))) {
    sessions.push({
      name: "api",
      cmd: "python3 api_server.py --public --port 8440",
      dir: "scripts",
      auto_start: true,
    });
  }

  // Web dev (Next.js, etc.)
  const pkgPath = path.join(target, "web", "package.json");
  if (fs.existsSync(pkgPath)) {
    try {
      const pkg = JSON.parse(fs.readFileSync(pkgPath, "utf8"));
      if (pkg.scripts && pkg.scripts.dev) {
        sessions.push({ name: "web", cmd: "npm run dev", dir: "web", auto_start: true });
      }
    } catch {}
  }

  // Uptime monitor
  if (fs.existsSync(path.join(target, "scripts", "uptime_monitor.py"))) {
    sessions.push({
      name: "monitor",
      cmd: "python3 uptime_monitor.py --url http://localhost:8440",
      dir: "scripts",
      auto_start: false,
    });
  }

  // Procfile support
  const procfile = path.join(target, "Procfile");
  if (fs.existsSync(procfile)) {
    try {
      const lines = fs.readFileSync(procfile, "utf8").split("\n");
      for (const line of lines) {
        const m = line.match(/^(\w+):\s*(.+)$/);
        if (m) {
          const existing = sessions.find(s => s.name === m[1]);
          if (!existing) {
            sessions.push({ name: m[1], cmd: m[2], dir: ".", auto_start: true });
          }
        }
      }
    } catch {}
  }

  return sessions;
}

// --- Commands ---

function cmdWorkspaceInit(target, args) {
  const globalFlag = args.includes("--global");

  if (sessions.length === 0) {
    log("no services detected. Create workspace config manually with: 0dai workspace add");
    return;
  }

  const ws = {
    name: path.basename(target),
    root: target,
    sessions,
  };

  const configFile = saveConfig(target, ws, globalFlag);
  log(`workspace config created: ${T}${configFile}${R}`);
  log(`${sessions.length} session(s) detected: ${sessions.map(s => s.name).join(", ")}`);
  log(`run: ${T}0dai workspace up${R}`);
}

function cmdWorkspaceAdd(target, args) {
  const nameIdx = args.indexOf("add");
  const name = nameIdx >= 0 ? args[nameIdx + 1] : args[0];
  if (!name) { log("usage: 0dai workspace add <name> --cmd '...' [--dir scripts] [--auto]"); return; }

  const ws = loadConfig(target) || { name: path.basename(target), sessions: [] };
  const cmdIdx = args.indexOf("--cmd");
  const dirIdx = args.indexOf("--dir");
  const cmd = cmdIdx >= 0 && args[cmdIdx + 1] ? args[cmdIdx + 1] : name;
  const dir = dirIdx >= 0 && args[dirIdx + 1] ? args[dirIdx + 1] : ".";
  const auto = args.includes("--auto");

  const existing = ws.sessions.findIndex(s => s.name === name);
  const entry = { name, cmd, dir, auto_start: auto };
  if (existing >= 0) ws.sessions[existing] = entry;
  else ws.sessions.push(entry);

  const found = findConfig(target);
  const configFile = found ? found.file : saveConfig(target, ws, false);
  fs.writeFileSync(configFile, JSON.stringify(ws, null, 2) + "\n", { mode: 0o600 });
  log(`session "${T}${name}${R}" ${existing >= 0 ? "updated" : "added"}`);
}

function cmdWorkspaceRm(target, name) {
  if (!name) { log("usage: 0dai workspace rm <name>"); return; }
  const ws = loadConfig(target);
  if (!ws) { log("no workspace config"); return; }
  ws.sessions = ws.sessions.filter(s => s.name !== name);
  const found = findConfig(target);
  fs.writeFileSync(found.file, JSON.stringify(ws, null, 2) + "\n", { mode: 0o600 });
  log(`session "${T}${name}${R}" removed`);
}

function cmdWorkspaceUp(target, args) {
  const ws = loadConfig(target);
  if (!ws) { log("no workspace config. Run: 0dai workspace init"); return; }

  // Filter by name if specified
  const filterNames = args.filter(a => !a.startsWith("-"));
  const running = listTmuxSessions();

  log(`starting workspace "${T}${ws.name}${R}"`);

  for (const s of ws.sessions) {
    if (!s.auto_start) continue;
    if (filterNames.length && !filterNames.includes(s.name)) continue;

    const sname = sessionName(s.name);
    if (running.find(x => x.name === sname)) {
      log(`${D}${s.name} already running (pid ${running.find(x => x.name === sname).pid})${R}`);
      continue;
    }

    const dir = s.dir ? path.join(ws.root || target, s.dir) : (ws.root || target);
    const cmd = `cd ${dir} && ${s.cmd}`;
    const r = tmux(["new-session", "-d", "-s", sname, "bash", "-lc", cmd]);
    if (r.status === 0) log(`${T}✓${R} ${s.name} started`);
    else log(`${R}✗${R} ${s.name} failed: ${r.stderr?.trim() || r.error || "unknown"}`);
  }

  if (filterNames.length === 0) {
    log(`workspace ready. ${D}Status: 0dai workspace status${R}`);
  }
}

function cmdWorkspaceDown(target, args) {
  const ws = loadConfig(target);
  if (!ws) { log("no workspace config"); return; }

  const filterNames = args.filter(a => !a.startsWith("-"));
  log(`stopping workspace "${T}${ws.name}${R}"`);

  for (const s of ws.sessions) {
    if (filterNames.length && !filterNames.includes(s.name)) continue;
    const sname = sessionName(s.name);
    tmux(["kill-session", "-t", sname]);
    log(`${D}${s.name} stopped${R}`);
  }
}

function cmdWorkspaceStatus(target) {
  const ws = loadConfig(target);
  if (!ws) { log("no workspace config. Run: 0dai workspace init"); return; }

  const running = listTmuxSessions();
  const isTTY = process.stdout.isTTY;
  const G = isTTY ? "\x1b[32m" : "";
  const RD = isTTY ? "\x1b[31m" : "";
  const DIM = isTTY ? "\x1b[2m" : "";

  console.log(`\n  ${T}Workspace: ${ws.name}${R}\n`);
  console.log(`  ${"SESSION".padEnd(14)} ${"STATUS".padEnd(10)} ${"PID".padEnd(8)} DIR`);
  console.log(`  ${"-".repeat(60)}`);

  for (const s of ws.sessions) {
    const sname = sessionName(s.name);
    const match = running.find(x => x.name === sname);
    const status = match ? `${G}running${R}` : `${RD}stopped${R}`;
    const pid = match ? match.pid : "—";
    const dir = s.dir || ".";
    console.log(`  ${s.name.padEnd(14)} ${status.padEnd(10)} ${String(pid).padEnd(8)} ${DIM}${dir}${R}`);
  }
  console.log();
}

function cmdWorkspaceAttach(target, name) {
  if (!name) { log("usage: 0dai workspace attach <name>"); return; }
  const sname = sessionName(name);
  const running = listTmuxSessions();
  if (!running.find(x => x.name === sname)) {
    log(`session "${name}" not running. Run: 0dai workspace up`);
    return;
  }
  log(`attaching to ${T}${name}${R}`);
  try {
    const { execSync } = require("child_process");
    execSync(`tmux attach -t ${sname}`, { stdio: "inherit" });
  } catch (e) { log(`error: ${e.message}`); }
}

function cmdWorkspaceLogs(target, name, args) {
  if (!name) { log("usage: 0dai workspace logs <name> [-f]"); return; }
  const sname = sessionName(name);
  const running = listTmuxSessions();
  if (!running.find(x => x.name === sname)) { log(`session "${name}" not running`); return; }

  const follow = args.includes("-f") || args.includes("--follow");
  if (follow) {
    // Live follow mode
    log(`following ${T}${name}${R} logs (Ctrl+C to exit)`);
    try {
      const { execSync } = require("child_process");
      execSync(`tmux capture-pane -t ${sname} -p -e`, { stdio: "inherit" });
    } catch (e) { log(`error: ${e.message}`); }
  } else {
    const r = tmux(["capture-pane", "-t", sname, "-p"]);
    if (r.stdout) {
      const lines = r.stdout.trim().split("\n").slice(-50);
      console.log(lines.join("\n"));
    }
  }
}

function cmdWorkspace(target, sub, args) {
  switch (sub) {
    case "init": cmdWorkspaceInit(target, args); break;
    case "up": cmdWorkspaceUp(target, args); break;
    case "down": cmdWorkspaceDown(target, args); break;
    case "status": cmdWorkspaceStatus(target); break;
    case "attach": cmdWorkspaceAttach(target, args[0]); break;
    case "logs": cmdWorkspaceLogs(target, args[0], args); break;
    case "add": cmdWorkspaceAdd(target, args); break;
    case "rm": cmdWorkspaceRm(target, args[0]); break;
    default:
      console.log(`\n  ${T}0dai workspace${R} — tmux session manager\n`);
      console.log("Commands:");
      console.log("  workspace init [--global]   Create config (auto-detect services)");
      console.log("  workspace up [name...]       Start auto_start sessions (filter by name)");
      console.log("  workspace down [name...]     Stop sessions (filter by name)");
      console.log("  workspace status             Show session status table");
      console.log("  workspace attach <name>      Attach to a running session");
      console.log("  workspace logs <name> [-f]   Show session output (-f = follow)");
      console.log("  workspace add <name> --cmd '...' [--dir X] [--auto]");
      console.log("  workspace rm <name>          Remove session from config");
      console.log();
  }
}

module.exports = { cmdWorkspace };
