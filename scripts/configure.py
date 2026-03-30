#!/usr/bin/env python3
"""Interactive configuration wizard for 0dai projects.

Generates or updates project configuration by asking structured questions
about stack, agents, MCP servers, org policy, and hooks.

Usage:
    0dai configure --target /path/to/project
    0dai configure --target /path --preset enterprise
    0dai configure --target /path --preset minimal
"""
from __future__ import annotations

import json
import pathlib
import sys


def detect_root() -> pathlib.Path:
    for i, arg in enumerate(sys.argv):
        if arg == "--target" and i + 1 < len(sys.argv):
            return pathlib.Path(sys.argv[i + 1])
    return pathlib.Path.cwd()


TARGET = detect_root()
PRESETS: dict[str, dict] = {
    "minimal": {
        "agents": ["claude"],
        "mcp_servers": [],
        "org_policy": None,
        "hooks_enabled": False,
        "telemetry_enabled": False,
    },
    "standard": {
        "agents": ["codex", "claude", "opencode", "gemini", "aider"],
        "mcp_servers": ["filesystem"],
        "org_policy": None,
        "hooks_enabled": True,
        "telemetry_enabled": True,
    },
    "enterprise": {
        "agents": ["codex", "claude", "opencode", "gemini", "aider"],
        "mcp_servers": ["filesystem", "github"],
        "org_policy": "enterprise-default",
        "hooks_enabled": True,
        "telemetry_enabled": True,
    },
}


def get_preset() -> str | None:
    for i, arg in enumerate(sys.argv):
        if arg == "--preset" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


def write_config(config: dict) -> None:
    config_dir = TARGET / "ai" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "project-config.json"
    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"[0dai-repo] wrote project config to {config_path.relative_to(TARGET)}")


def write_mcp_json(servers: list[str]) -> None:
    mcp_path = TARGET / ".mcp.json"
    mcp_config: dict = {"mcpServers": {}}

    if mcp_path.is_file():
        try:
            mcp_config = json.loads(mcp_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    server_defs = {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@anthropic-ai/mcp-server-filesystem", "."],
        },
        "github": {
            "command": "npx",
            "args": ["-y", "@anthropic-ai/mcp-server-github"],
            "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
        },
        "0dai": {
            "command": "python3",
            "args": ["-m", "scripts.mcp_server", "--target", "."],
        },
    }

    for server in servers:
        if server in server_defs and server not in mcp_config.get("mcpServers", {}):
            mcp_config.setdefault("mcpServers", {})[server] = server_defs[server]

    mcp_path.write_text(
        json.dumps(mcp_config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"[0dai-repo] updated .mcp.json with {len(servers)} server(s)")


def generate_config(preset_name: str, preset: dict) -> dict:
    return {
        "managed": True,
        "preset": preset_name,
        "agents": preset["agents"],
        "mcp_servers": preset["mcp_servers"],
        "org_policy": preset["org_policy"],
        "hooks_enabled": preset["hooks_enabled"],
        "telemetry_enabled": preset["telemetry_enabled"],
        "configured_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
    }


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    preset_name = get_preset()

    if preset_name and preset_name in PRESETS:
        preset = PRESETS[preset_name]
        config = generate_config(preset_name, preset)
        if dry_run:
            print(json.dumps(config, indent=2))
            print(f"\n[0dai-repo] dry-run: would apply preset '{preset_name}'")
            return

        write_config(config)
        write_mcp_json(preset["mcp_servers"])
        print(f"[0dai-repo] applied preset: {preset_name}")
        print(f"[0dai-repo] agents: {', '.join(preset['agents'])}")
        if preset["org_policy"]:
            print(f"[0dai-repo] org policy: {preset['org_policy']}")
        return

    if preset_name and preset_name not in PRESETS:
        print(f"[0dai-repo] unknown preset: {preset_name}")
        print(f"[0dai-repo] available presets: {', '.join(PRESETS.keys())}")
        raise SystemExit(1)

    # No preset — list available presets
    print("[0dai-repo] available configuration presets:\n")
    for name, preset in PRESETS.items():
        agents = ", ".join(preset["agents"])
        mcp = ", ".join(preset["mcp_servers"]) if preset["mcp_servers"] else "none"
        policy = preset["org_policy"] or "none"
        print(f"  {name}:")
        print(f"    agents: {agents}")
        print(f"    mcp: {mcp}")
        print(f"    org_policy: {policy}")
        print(f"    hooks: {preset['hooks_enabled']}")
        print()

    print("usage: 0dai configure --target <path> --preset <name>")
    print("       0dai configure --target <path> --preset <name> --dry-run")


if __name__ == "__main__":
    main()
