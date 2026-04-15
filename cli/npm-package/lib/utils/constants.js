/**
 * Shared constants extracted from shared.js.
 */
"use strict";

const SUPPORTED_CLIS = [
  {
    name: "claude", bin: "claude",
    pkg: "@anthropic-ai/claude-code", pkgType: "npm",
    install: "npm i -g @anthropic-ai/claude-code",
    altAuth: "Pro/Team subscription",
    agentFiles: [".claude/settings.json", ".claude/CLAUDE.md", ".mcp.json"],
  },
  {
    name: "codex", bin: "codex",
    pkg: "@openai/codex", pkgType: "npm",
    install: "npm i -g @openai/codex",
    altAuth: "ChatGPT Pro subscription",
    agentFiles: ["AGENTS.md", ".codex/config.toml"],
  },
  {
    name: "opencode", bin: "opencode",
    pkg: null, pkgType: "go",
    install: "go install github.com/nichochar/opencode@latest",
    altAuth: null,
    agentFiles: ["opencode.json"],
  },
  {
    name: "gemini", bin: "gemini",
    pkg: "@google/gemini-cli", pkgType: "npm",
    install: "npm i -g @google/gemini-cli",
    altAuth: null,
    agentFiles: null,
  },
  {
    name: "aider", bin: "aider",
    pkg: "aider-chat", pkgType: "pip",
    install: "pip install aider-chat",
    altAuth: null,
    agentFiles: null,
  },
  {
    name: "qoder", bin: "qodercli",
    pkg: "@qoder-ai/qodercli", pkgType: "npm",
    install: "npm i -g @qoder-ai/qodercli",
    altAuth: null,
    agentFiles: [".qoder/settings.json"],
  },
];

const MANIFEST_FILES = [
  "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb", "tsconfig.json",
  "next.config.js", "next.config.mjs", "next.config.ts",
  "vite.config.js", "vite.config.ts", "vite.config.mjs",
  "vue.config.js", "nuxt.config.js", "nuxt.config.ts",
  "svelte.config.js", "astro.config.mjs", "astro.config.ts",
  "remix.config.js", "angular.json",
  "go.mod", "go.sum", "pyproject.toml", "requirements.txt", "requirements-dev.txt", "setup.py",
  "poetry.lock", "Pipfile", "Pipfile.lock",
  "pubspec.yaml", "Cargo.toml", "Cargo.lock", "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts",
  "Gemfile", "composer.json",
  "Makefile", "docker-compose.yml", "docker-compose.yaml", "Dockerfile",
  "pnpm-workspace.yaml", "lerna.json", "turbo.json", "nx.json",
];

const PROBE_DIRS = [
  "src", "lib", "app", "apps", "packages", "services",
  "cmd", "internal", "web", "frontend", "backend",
  "tests", "test", "spec", "__tests__",
  "infra", "deploy", "docker", ".github",
  "android", "ios", "linux", "macos", "windows",
];

const SETTINGS_PRESERVE_FIELDS = ["model", "permissionMode", "effortLevel"];

module.exports = { SUPPORTED_CLIS, MANIFEST_FILES, PROBE_DIRS, SETTINGS_PRESERVE_FIELDS };
