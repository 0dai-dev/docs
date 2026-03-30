#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "$0")" && pwd)/common.sh"

parse_kv_args "$@"
require_target

python3 - "$TARGET_DIR" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
errors = []
notes = []

def require(rel: str) -> pathlib.Path | None:
    path = root / rel
    if not path.exists():
        errors.append(f"missing required path: {rel}")
        return None
    return path

version = require("ai/VERSION")
require("ai/VERSION_SCHEMA")
project_manifest = require("ai/manifest/project.yaml")
discovery_file = require("ai/manifest/discovery.json")
require("ai/manifest/applied-lock.json")
require("ai/manifest/init-report.md")
meta_manifest = require("ai/meta/project.manifest.yaml")
environment_manifest = require("ai/manifest/environment.yaml")
commands_manifest = require("ai/manifest/commands.yaml")

agents = []
if discovery_file is not None:
    try:
        discovery = json.loads(discovery_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON: ai/manifest/discovery.json ({exc})")
        discovery = {}
    agents = discovery.get("selected_agents", [])
    stack = discovery.get("stack")
    package_manager = discovery.get("package_manager")
    notes.append(f"stack={stack}")
    notes.append(f"package_manager={package_manager}")

required_for_agent = {
    "codex": ["AGENTS.md", ".codex/config.toml"],
    "claude": [".claude/settings.json", ".claude/CLAUDE.md", ".mcp.json"],
    "opencode": ["opencode.json", ".opencode/agents"],
}

for agent in agents:
    for rel in required_for_agent.get(agent, []):
        require(rel)

if project_manifest is not None:
    text = project_manifest.read_text(encoding="utf-8")
    for needle in ["managed: true", "project:", "commands:", "paths:", "ai:"]:
        if needle not in text:
            errors.append(f"project manifest missing marker: {needle}")

if meta_manifest is not None and discovery_file is not None:
    meta_text = meta_manifest.read_text(encoding="utf-8")
    if agents:
        if "claude" in agents and ".claude/CLAUDE.md" not in meta_text:
            errors.append("meta manifest missing .claude/CLAUDE.md")
        if "opencode" in agents and ".opencode/agents" not in meta_text:
            errors.append("meta manifest missing .opencode/agents")
        if "codex" in agents and ".codex/config.toml" not in meta_text:
            errors.append("meta manifest missing .codex/config.toml")

if environment_manifest is not None:
    env_text = environment_manifest.read_text(encoding="utf-8")
    for needle in ["kind:", "execution:", "workspace:", "available_clis:", "capabilities:", "constraints:"]:
        if needle not in env_text:
            errors.append(f"environment manifest missing marker: {needle}")

if commands_manifest is not None:
    commands_text = commands_manifest.read_text(encoding="utf-8")
    for needle in ["commands:", "install:", "build:", "test:", "lint:", "format:", "tier:", "policy:"]:
        if needle not in commands_text:
            errors.append(f"commands manifest missing marker: {needle}")

if version is not None:
    notes.append(f"ai_version={version.read_text(encoding='utf-8').strip()}")

if errors:
    print("validate=failed")
    for note in notes:
        print(f"note={note}")
    for error in errors:
        print(f"error={error}")
    sys.exit(1)

print("validate=ok")
for note in notes:
    print(f"note={note}")
print(f"selected_agents={','.join(agents) if agents else 'none'}")
PY
