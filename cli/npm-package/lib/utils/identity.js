/**
 * Project identity and metadata detection.
 * Extracted from shared.js to reduce module size.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const os = require("os");
const { MANIFEST_FILES, PROBE_DIRS, SUPPORTED_CLIS } = require("./constants");

function deviceFingerprint() {
  const crypto = require("crypto");
  const parts = [
    os.hostname(),
    os.userInfo().username,
    os.platform(),
    os.arch(),
    os.cpus().length.toString(),
    os.totalmem().toString(),
  ];
  try {
    if (os.platform() === "linux") parts.push(fs.readFileSync("/etc/machine-id", "utf8").trim());
    else if (os.platform() === "darwin") {
      const { execSync } = require("child_process");
      parts.push(execSync("ioreg -rd1 -c IOPlatformExpertDevice | awk '/IOPlatformUUID/'", { encoding: "utf8" }).trim());
    }
  } catch {}
  return crypto.createHash("sha256").update(parts.join(":")).digest("hex").slice(0, 32);
}

function registerProject(projectPath, name, stack, CONFIG_DIR, PROJECTS_FILE) {
  try {
    fs.mkdirSync(CONFIG_DIR, { recursive: true });
    let projects = [];
    try { projects = JSON.parse(fs.readFileSync(PROJECTS_FILE, "utf8")).projects || []; } catch {}
    const abs = path.resolve(projectPath);
    const idx = projects.findIndex(p => p.path === abs);
    const entry = { path: abs, name: name || path.basename(abs), stack: stack || "?", last_seen: new Date().toISOString() };
    if (idx >= 0) projects[idx] = entry;
    else projects.unshift(entry);
    fs.writeFileSync(PROJECTS_FILE, JSON.stringify({ projects: projects.slice(0, 50) }, null, 2));
  } catch {}
}

function projectIdFor(target, projectName, remoteOrigin) {
  const crypto = require("crypto");
  const seed = JSON.stringify({ name: projectName, origin: remoteOrigin || path.resolve(target) });
  return "prj_" + crypto.createHash("sha256").update(seed).digest("hex").slice(0, 16);
}

function getGitRemoteOrigin(target) {
  try {
    const { execFileSync } = require("child_process");
    return execFileSync("git", ["config", "--get", "remote.origin.url"], {
      cwd: target, stdio: ["ignore", "pipe", "ignore"], encoding: "utf8", timeout: 5000,
    }).trim();
  } catch { return ""; }
}

function inferProjectName(target, manifestContents) {
  try {
    if (manifestContents["package.json"]) {
      const pkg = JSON.parse(manifestContents["package.json"]);
      if (pkg.name) return String(pkg.name);
    }
  } catch {}
  if (manifestContents["go.mod"]) {
    for (const line of manifestContents["go.mod"].split(/\r?\n/)) {
      if (line.startsWith("module ")) return line.trim().split(/\s+/).pop().split("/").pop();
    }
  }
  if (manifestContents["pyproject.toml"]) {
    for (const line of manifestContents["pyproject.toml"].split(/\r?\n/)) {
      if (line.trim().startsWith("name")) return line.split("=").pop().trim().replace(/^["']|["']$/g, "");
    }
  }
  return path.basename(path.resolve(target));
}

function detectStackHint(projectFiles, manifestContents) {
  if (manifestContents["next.config.js"] || manifestContents["next.config.mjs"] || manifestContents["next.config.ts"]) return "nextjs";
  if (manifestContents["package.json"]) {
    try {
      const pkg = JSON.parse(manifestContents["package.json"]);
      const deps = { ...(pkg.dependencies || {}), ...(pkg.devDependencies || {}) };
      if (deps.next) return "nextjs";
      if (deps.react || deps.vue || deps.svelte) return "frontend";
    } catch {}
  }
  if (manifestContents["go.mod"]) return "go-service";
  if (manifestContents["pyproject.toml"] || manifestContents["requirements.txt"]) return "python-service";
  if (projectFiles.some((name) => name.startsWith("apps/") || name.startsWith("packages/"))) return "monorepo";
  return "unknown";
}

function collectMetadata(target) {
  const projectFiles = [];
  const manifestContents = {};

  for (const d of PROBE_DIRS) {
    try { if (fs.statSync(path.join(target, d)).isDirectory()) projectFiles.push(d + "/"); } catch {}
  }

  for (const f of MANIFEST_FILES) {
    const p = path.join(target, f);
    try {
      const stat = fs.statSync(p);
      if (stat.isFile()) {
        projectFiles.push(f);
        const content = fs.readFileSync(p, "utf8");
        if (content.length < 100000) manifestContents[f] = content;
      }
    } catch {}
  }

  const clis = [];
  const { execSync } = require("child_process");
  for (const cli of SUPPORTED_CLIS) {
    try {
      execSync(`command -v ${cli.bin}`, { stdio: "ignore", shell: "/bin/sh", env: process.env });
      clis.push(cli.name);
    } catch {}
  }

  return { projectFiles, manifestContents, clis };
}

function buildProjectIdentity(target, metadata, detectedStack = "") {
  const projectName = inferProjectName(target, metadata.manifestContents);
  const remoteOrigin = getGitRemoteOrigin(target);
  return {
    project_name: projectName,
    stack: detectedStack || detectStackHint(metadata.projectFiles, metadata.manifestContents),
    project_id: projectIdFor(target, projectName, remoteOrigin),
    origin: remoteOrigin ? "git" : "local",
    remote_origin: remoteOrigin,
    binding_source: "npm-cli",
  };
}

module.exports = {
  MANIFEST_FILES, PROBE_DIRS,
  deviceFingerprint, registerProject, projectIdFor,
  getGitRemoteOrigin, inferProjectName, detectStackHint,
  collectMetadata, buildProjectIdentity,
};
