"use strict";
const shared = require("../shared");
const { T, R, D, fs, path } = shared;

function cmdAudit(target) {
  const W = process.stdout.isTTY ? "\x1b[33m" : "";   // yellow
  const RE = process.stdout.isTTY ? "\x1b[31m" : "";  // red
  const G = process.stdout.isTTY ? "\x1b[32m" : "";   // green

  // Secret patterns: [label, regex, severity]
  const PATTERNS = [
    ["Anthropic API key",  /sk-ant-api[0-9A-Za-z_-]{20,}/g,         "critical"],
    ["OpenAI API key",     /sk-[A-Za-z0-9]{20,}/g,                   "critical"],
    ["GitHub PAT (ghp)",   /ghp_[A-Za-z0-9]{36}/g,                   "critical"],
    ["GitHub PAT (gho)",   /gho_[A-Za-z0-9]{36}/g,                   "critical"],
    ["GitHub fine-grained",/github_pat_[A-Za-z0-9_]{59}/g,           "critical"],
    ["AWS access key",     /AKIA[0-9A-Z]{16}/g,                       "critical"],
    ["AWS secret key",     /aws_secret_access_key\s*[=:]\s*\S{20,}/gi,"critical"],
    ["Google API key",     /AIza[0-9A-Za-z_-]{35}/g,                  "high"],
    ["Bearer token",       /Bearer\s+[A-Za-z0-9_-]{32,}/g,           "high"],
    ["Private key block",  /-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY/g, "critical"],
    ["Generic secret var", /(?:secret|password|passwd|pwd)\s*[=:]\s*["']?[A-Za-z0-9+/=_-]{12,}["']?/gi, "medium"],
  ];

  // Files to scan
  const SCAN_FILES = [
    "CLAUDE.md", "AGENTS.md", "GEMINI.md", ".cursorrules",
    ".codex/config.md", ".codex/instructions.md",
    "opencode.json", ".mcp.json",
  ];

  // Walk a directory recursively, return all file paths
  function walk(dir, maxDepth = 6, _depth = 0) {
    if (_depth > maxDepth) return [];
    let results = [];
    try {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        if (entry.name.startsWith(".git") || entry.name === "node_modules") continue;
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) results = results.concat(walk(full, maxDepth, _depth + 1));
        else results.push(full);
      }
    } catch { /* skip unreadable */ }
    return results;
  }

  const findings = []; // {file, line, label, severity, excerpt}

  function scanContent(filePath, content) {
    const lines = content.split("\n");
    for (const [label, regex, severity] of PATTERNS) {
      regex.lastIndex = 0;
      for (let i = 0; i < lines.length; i++) {
        let m;
        regex.lastIndex = 0;
        while ((m = regex.exec(lines[i])) !== null) {
          const val = m[0];
          // Redact: show first 6 + ... + last 4 chars
          const excerpt = val.length > 14 ? val.slice(0, 6) + "..." + val.slice(-4) : val.slice(0, 4) + "...";
          findings.push({ file: filePath, line: i + 1, label, severity, excerpt });
        }
      }
    }
  }

  // Collect files to scan
  const toScan = new Set();

  for (const rel of SCAN_FILES) {
    const p = path.join(target, rel);
    if (fs.existsSync(p)) toScan.add(p);
  }

  const aiDir = path.join(target, "ai");
  if (fs.existsSync(aiDir)) {
    for (const f of walk(aiDir)) {
      if (/\.(md|json|yaml|yml|txt|toml)$/.test(f)) toScan.add(f);
    }
  }

  // Warn about .env files (don't scan content, just flag existence)
  const envFiles = [".env", ".env.local", ".env.production", ".env.development"];
  const foundEnv = envFiles.filter(e => fs.existsSync(path.join(target, e)));

  console.log(`\n  ${T}0dai audit${R} — scanning for leaked secrets\n`);
  console.log(`  ${D}target: ${target}${R}`);
  console.log(`  ${D}files:  ${toScan.size} scanned${R}\n`);

  for (const filePath of toScan) {
    try {
      const content = fs.readFileSync(filePath, "utf8");
      scanContent(filePath, content);
    } catch { /* skip */ }
  }

  if (foundEnv.length > 0) {
    console.log(`  ${W}WARN${R}  .env files detected — ensure they are in .gitignore`);
    for (const e of foundEnv) console.log(`         ${D}${e}${R}`);
    console.log();
  }

  if (findings.length === 0) {
    console.log(`  ${G}✓ No secrets found${R} in scanned files\n`);
    return;
  }

  const critical = findings.filter(f => f.severity === "critical");
  const high = findings.filter(f => f.severity === "high");
  const medium = findings.filter(f => f.severity === "medium");

  const colorFor = (s) => s === "critical" ? RE : s === "high" ? W : D;

  for (const f of findings) {
    const c = colorFor(f.severity);
    const rel = path.relative(target, f.file);
    console.log(`  ${c}${f.severity.toUpperCase().padEnd(8)}${R} ${rel}:${f.line}`);
    console.log(`           ${D}${f.label}: ${f.excerpt}${R}`);
  }

  console.log();
  if (critical.length > 0) console.log(`  ${RE}${critical.length} critical${R} · ${W}${high.length} high${R} · ${D}${medium.length} medium${R}\n`);
  else console.log(`  ${W}${high.length} high${R} · ${D}${medium.length} medium${R}\n`);

  console.log(`  ${D}Tip: add secrets to .gitignore or use env vars, not plaintext files${R}\n`);

  if (critical.length > 0) process.exit(1);
}

module.exports = { cmdAudit };
