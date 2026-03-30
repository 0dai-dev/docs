#!/usr/bin/env python3
"""0dai Agent Teams Generator — generate .claude/agents/ from personas and agent sources.

Reads ai/agents-src/ (canonical agent definitions) and ai/personas/ (role-specific
behavior) to produce rich Agent Teams configurations for Claude Code.

Usage:
    python3 scripts/generate_agent_teams.py --target <path>
    python3 scripts/generate_agent_teams.py --target <path> --list
    python3 scripts/generate_agent_teams.py --target <path> --info <name>
    0dai agent-teams --target <path>
"""
from __future__ import annotations

import json
import pathlib
import sys


ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent


def _parse_yaml_simple(path: pathlib.Path) -> dict:
    """Minimal YAML parser for flat key-value + simple lists."""
    result: dict = {}
    current_key: str | None = None
    current_list: list[str] = []
    multiline_key: str | None = None
    multiline_lines: list[str] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            if multiline_key:
                multiline_lines.append("")
            continue

        # Multiline block (indented continuation)
        if multiline_key and (line.startswith("  ") or line.startswith("\t")):
            multiline_lines.append(stripped)
            continue
        elif multiline_key:
            result[multiline_key] = "\n".join(multiline_lines).strip()
            multiline_key = None
            multiline_lines = []

        # List item
        if current_key and stripped.startswith("- "):
            current_list.append(stripped[2:].strip().strip('"').strip("'"))
            continue

        # Close list
        if current_key and current_list:
            result[current_key] = current_list
            current_key = None
            current_list = []

        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "|":
                multiline_key = key
                multiline_lines = []
            elif val:
                try:
                    result[key] = int(val)
                except ValueError:
                    if val.lower() in ("true", "false"):
                        result[key] = val.lower() == "true"
                    else:
                        result[key] = val.strip('"').strip("'")
            else:
                current_key = key
                current_list = []

    if current_key and current_list:
        result[current_key] = current_list
    if multiline_key and multiline_lines:
        result[multiline_key] = "\n".join(multiline_lines).strip()

    return result


def get_personas(target: pathlib.Path) -> list[dict]:
    """Read persona definitions from target project or upstream templates."""
    personas = []
    # Check project-local personas first
    personas_dir = target / "ai" / "personas"
    if not personas_dir.is_dir():
        # Fallback to upstream templates
        personas_dir = ROOT_DIR / "templates" / "layer" / "ai" / "personas"

    if not personas_dir.is_dir():
        return personas

    for path in sorted(personas_dir.glob("*.yaml")):
        data = _parse_yaml_simple(path)
        data["_source"] = str(path.relative_to(ROOT_DIR) if str(path).startswith(str(ROOT_DIR)) else path)
        personas.append(data)

    return personas


def get_agent_sources() -> list[dict]:
    """Read canonical agent definitions from upstream."""
    agents = []
    agents_dir = ROOT_DIR / "templates" / "layer" / "ai" / "agents-src"
    if not agents_dir.is_dir():
        return agents

    for path in sorted(agents_dir.glob("*.yaml")):
        data = _parse_yaml_simple(path)
        agents.append(data)

    return agents


def get_agent_templates() -> list[dict]:
    """Read existing Claude agent team templates."""
    templates = []
    agents_dir = ROOT_DIR / "templates" / "layer" / "ai" / "templates" / "claude" / "agents"
    if not agents_dir.is_dir():
        return templates

    for path in sorted(agents_dir.glob("*.md.tmpl")):
        text = path.read_text(encoding="utf-8")
        entry: dict = {"file": path.name, "name": path.stem.replace(".md", "")}

        # Parse frontmatter
        if text.startswith("---"):
            end = text.find("---", 3)
            if end > 0:
                for line in text[3:end].splitlines():
                    if ":" in line:
                        k, _, v = line.partition(":")
                        entry[k.strip()] = v.strip()
                entry["body_preview"] = text[end + 3:].strip()[:200]

        templates.append(entry)

    return templates


def get_installed_agents(target: pathlib.Path) -> list[dict]:
    """Read agents installed in the target project's .claude/agents/."""
    agents = []
    agents_dir = target / ".claude" / "agents"
    if not agents_dir.is_dir():
        return agents

    for path in sorted(agents_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        entry: dict = {"file": path.name, "name": path.stem, "managed": "managed: true" in text}

        if text.startswith("---"):
            end = text.find("---", 3)
            if end > 0:
                for line in text[3:end].splitlines():
                    if ":" in line:
                        k, _, v = line.partition(":")
                        entry[k.strip()] = v.strip()

        agents.append(entry)

    return agents


def cmd_list(target: pathlib.Path) -> None:
    """List available and installed agent team members."""
    templates = get_agent_templates()
    installed = get_installed_agents(target)
    installed_names = {a["name"] for a in installed}

    print(f"{'Name':<15} {'Status':<12} Description")
    print("-" * 70)
    for t in templates:
        status = "installed" if t["name"] in installed_names else "available"
        print(f"{t['name']:<15} {status:<12} {t.get('description', '')}")

    print(f"\n{len(templates)} agent(s) defined, {len(installed)} installed in {target}/.claude/agents/")


def cmd_info(name: str) -> None:
    """Show detailed info about an agent team member."""
    agents_dir = ROOT_DIR / "templates" / "layer" / "ai" / "templates" / "claude" / "agents"
    path = agents_dir / f"{name}.md.tmpl"

    if not path.is_file():
        print(f"Agent '{name}' not found.", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8")
    # Strip frontmatter delimiters for display
    print(text.replace(".tmpl", ""))


def cmd_generate(target: pathlib.Path) -> None:
    """Show agent teams status — actual installation happens via init/sync."""
    installed = get_installed_agents(target)
    templates = get_agent_templates()

    if installed:
        print(f"Agent Teams installed at {target}/.claude/agents/:")
        for a in installed:
            managed = " (managed)" if a.get("managed") else " (custom)"
            print(f"  {a['name']}{managed} — {a.get('description', '')}")
    else:
        print(f"No Agent Teams installed yet at {target}/.claude/agents/")

    print(f"\n{len(templates)} agents available in upstream templates.")
    print("Run '0dai sync --target <path>' to install/update agent teams.")


def cmd_json(target: pathlib.Path) -> None:
    """Output agent teams status as JSON."""
    templates = get_agent_templates()
    installed = get_installed_agents(target)
    personas = get_personas(target)

    result = {
        "available_agents": [
            {"name": t["name"], "description": t.get("description", "")}
            for t in templates
        ],
        "installed_agents": [
            {"name": a["name"], "description": a.get("description", ""), "managed": a.get("managed", False)}
            for a in installed
        ],
        "personas": [
            {"name": p.get("name", ""), "display_name": p.get("display_name", ""), "description": p.get("description", "")}
            for p in personas
        ],
        "counts": {
            "available": len(templates),
            "installed": len(installed),
            "personas": len(personas),
        },
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main() -> None:
    target = pathlib.Path(".")
    subcmd = ""
    info_name = ""
    args = sys.argv[1:]

    i = 0
    while i < len(args):
        if args[i] == "--target" and i + 1 < len(args):
            target = pathlib.Path(args[i + 1]).resolve()
            i += 2
        elif args[i] == "--list":
            subcmd = "list"
            i += 1
        elif args[i] == "--info" and i + 1 < len(args):
            subcmd = "info"
            info_name = args[i + 1]
            i += 2
        elif args[i] == "--json":
            subcmd = "json"
            i += 1
        else:
            i += 1

    if subcmd == "list":
        cmd_list(target)
    elif subcmd == "info":
        cmd_info(info_name)
    elif subcmd == "json":
        cmd_json(target)
    else:
        cmd_generate(target)


if __name__ == "__main__":
    main()
