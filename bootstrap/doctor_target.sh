#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "$0")" && pwd)/common.sh"

parse_kv_args "$@"
require_target

python3 - "$TARGET_DIR" <<'PY'
import json
import pathlib
import re
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


def read_yaml_value(text: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else "unknown"


def read_command_entries(text: str):
    entries = []
    current = None
    for line in text.splitlines():
        if re.match(r"^  [a-zA-Z0-9_-]+:$", line):
            current = line.strip().rstrip(":")
            if current != "policy":
                entries.append({"name": current, "command": "", "tier": "unknown"})
        elif current and line.strip().startswith("command:") and current != "policy":
            entries[-1]["command"] = line.split(":", 1)[1].strip().strip('"')
        elif current and line.strip().startswith("tier:") and current != "policy":
            entries[-1]["tier"] = line.split(":", 1)[1].strip()
    return [entry for entry in entries if entry["name"] != "commands"]


def command_status(entry, environment_kind: str, execution: str):
    tier = entry["tier"]
    if not entry["command"]:
        return "missing", "command not configured"
    if tier == "safe":
        return "allowed", "safe tier"
    if tier == "workspace":
        return "allowed", "workspace tier"
    if tier == "ops":
        if environment_kind in {"ci", "cloud-cli"}:
            return "blocked", "ops tier requires explicit approval outside ci/cloud-cli automation"
        if execution == "headless":
            return "blocked", "ops tier blocked in headless execution without explicit approval"
        return "blocked", "ops tier requires explicit approval"
    return "unknown", "unknown tier"


version = require("ai/VERSION")
project_manifest = require("ai/manifest/project.yaml")
environment_manifest = require("ai/manifest/environment.yaml")
commands_manifest = require("ai/manifest/commands.yaml")
require("ai/manifest/applied-lock.json")
discovery_file = require("ai/manifest/discovery.json")

agents = []
if discovery_file is not None:
    discovery = json.loads(discovery_file.read_text(encoding="utf-8"))
    agents = discovery.get("selected_agents", [])
    notes.append(f"stack={discovery.get('stack', 'unknown')}")

required_for_agent = {
    "codex": ["AGENTS.md", ".codex/config.toml"],
    "claude": [".claude/settings.json", ".claude/CLAUDE.md", ".mcp.json"],
    "opencode": ["opencode.json", ".opencode/agents"],
}

for agent in agents:
    for rel in required_for_agent.get(agent, []):
        require(rel)

if errors:
    print("doctor=failed")
    for error in errors:
        print(f"error={error}")
    sys.exit(1)

env_text = environment_manifest.read_text(encoding="utf-8")
environment_kind = read_yaml_value(env_text, "kind")
execution = read_yaml_value(env_text, "execution")
available_clis = []
capture = False
for line in env_text.splitlines():
    if line.startswith("available_clis:"):
      capture = True
      continue
    if capture and line.startswith("capabilities:"):
      break
    if capture and line.strip().startswith("- "):
      available_clis.append(line.strip()[2:])

commands_text = commands_manifest.read_text(encoding="utf-8")
entries = read_command_entries(commands_text)

print("doctor=ok")
print(f"environment={environment_kind}")
print(f"execution={execution}")
print(f"available_clis={','.join(available_clis) if available_clis else 'none'}")
if version is not None:
    print(f"ai_version={version.read_text(encoding='utf-8').strip()}")
for note in notes:
    print(f"note={note}")

for entry in entries:
    status, reason = command_status(entry, environment_kind, execution)
    print(f"command={entry['name']}")
    print(f"tier={entry['tier']}")
    print(f"status={status}")
    print(f"reason={reason}")
PY
