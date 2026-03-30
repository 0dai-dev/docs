#!/usr/bin/env python3
"""0dai Agent Orchestration Config Generator.

Generates squad and swarm workspace definitions from ai/ layer personas,
playbooks, and command tiers. Compatible with claude-squad / claude-swarm patterns.

Usage:
    python3 scripts/generate_orchestration.py --target <path>
    python3 scripts/generate_orchestration.py --target <path> --list
    python3 scripts/generate_orchestration.py --target <path> --json
    0dai orchestrate --target <path>
"""
from __future__ import annotations

import json
import pathlib
import sys
import time


ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent


def _parse_yaml_flat(path: pathlib.Path) -> dict:
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

        if multiline_key and (line.startswith("  ") or line.startswith("\t")):
            multiline_lines.append(stripped)
            continue
        elif multiline_key:
            result[multiline_key] = "\n".join(multiline_lines).strip()
            multiline_key = None
            multiline_lines = []

        if current_key and stripped.startswith("- "):
            current_list.append(stripped[2:].strip().strip('"').strip("'"))
            continue

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


def _load_personas(target: pathlib.Path) -> list[dict]:
    """Load persona definitions from target or upstream."""
    dirs = [
        target / "ai" / "personas",
        ROOT_DIR / "templates" / "layer" / "ai" / "personas",
    ]
    for d in dirs:
        if d.is_dir():
            return [_parse_yaml_flat(p) for p in sorted(d.glob("*.yaml"))]
    return []


def _load_playbooks(target: pathlib.Path) -> list[dict]:
    """Load playbook definitions."""
    dirs = [
        target / "ai" / "playbooks",
        ROOT_DIR / "templates" / "layer" / "ai" / "playbooks",
    ]
    for d in dirs:
        if d.is_dir():
            playbooks = []
            for p in sorted(d.glob("*.md")):
                text = p.read_text(encoding="utf-8")
                title = p.stem.replace("_", " ").title()
                for line in text.splitlines():
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break
                playbooks.append({"name": p.stem, "title": title, "file": p.name})
            return playbooks
    return []


def generate_squad(target: pathlib.Path) -> dict:
    """Generate squad workspace definition.

    Squad pattern: lead agent + specialist agents + quality gate.
    One agent leads, delegates to specialists, gate agent reviews before merge.
    """
    personas = _load_personas(target)
    playbooks = _load_playbooks(target)

    # Map personas to squad roles
    roles = []
    lead = None
    gate = None

    for p in personas:
        name = p.get("name", "")
        role = {
            "agent": name,
            "display_name": p.get("display_name", name),
            "focus_paths": p.get("focus_paths", []),
            "command_tiers": p.get("allowed_command_tiers", ["safe"]),
        }

        if name == "architect":
            role["squad_role"] = "lead"
            role["description"] = "Leads design decisions, delegates implementation to specialists"
            lead = role
        elif name == "security":
            role["squad_role"] = "gate"
            role["description"] = "Final security review before any merge or deploy"
            gate = role
        else:
            role["squad_role"] = "specialist"
            role["description"] = p.get("description", "")
            roles.append(role)

    # Build squad definition
    squad = {
        "managed": True,
        "schema": 1,
        "type": "squad",
        "description": "Multi-agent squad with architect lead, specialists, and security gate",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
        "lead": lead or {
            "agent": "architect",
            "squad_role": "lead",
            "description": "Leads design decisions",
        },
        "specialists": roles,
        "gate": gate or {
            "agent": "security",
            "squad_role": "gate",
            "description": "Final security review",
        },
        "workflows": [
            {
                "name": pb["name"],
                "title": pb["title"],
                "phases": _workflow_phases(pb["name"]),
            }
            for pb in playbooks
        ],
        "handoff_rules": [
            {"from": "lead", "to": "specialist", "condition": "task assigned to domain"},
            {"from": "specialist", "to": "gate", "condition": "implementation complete"},
            {"from": "gate", "to": "lead", "condition": "review findings require design change"},
        ],
    }

    return squad


def generate_swarm(target: pathlib.Path) -> dict:
    """Generate swarm workspace definition.

    Swarm pattern: orchestrator + parallel specialists + reviewer.
    Orchestrator decomposes work, specialists execute in parallel, reviewer consolidates.
    """
    personas = _load_personas(target)
    playbooks = _load_playbooks(target)

    agents = []
    for p in personas:
        name = p.get("name", "")
        agents.append({
            "agent": name,
            "display_name": p.get("display_name", name),
            "parallel": name not in ("architect", "security"),
            "focus_paths": p.get("focus_paths", []),
            "command_tiers": p.get("allowed_command_tiers", ["safe"]),
        })

    swarm = {
        "managed": True,
        "schema": 1,
        "type": "swarm",
        "description": "Parallel agent swarm with orchestrator decomposition and review consolidation",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
        "orchestrator": {
            "agent": "architect",
            "role": "Decomposes tasks into parallel subtasks and assigns to specialists",
        },
        "agents": agents,
        "reviewer": {
            "agent": "security",
            "role": "Reviews consolidated output for security and consistency",
        },
        "execution": {
            "strategy": "fan-out-fan-in",
            "parallel_limit": 3,
            "timeout_minutes": 30,
        },
        "task_routing": [
            {"pattern": "test|coverage|regression", "agent": "qa"},
            {"pattern": "deploy|ci|docker|infra", "agent": "devops"},
            {"pattern": "auth|secret|cve|injection", "agent": "security"},
            {"pattern": "design|boundary|api|refactor", "agent": "architect"},
        ],
    }

    return swarm


def _workflow_phases(playbook_name: str) -> list[dict]:
    """Map a playbook to orchestration phases."""
    phases_map = {
        "bugfix_flow": [
            {"phase": "reproduce", "agent": "qa", "action": "Reproduce the bug and identify root cause"},
            {"phase": "fix", "agent": "devops", "action": "Implement minimal fix"},
            {"phase": "test", "agent": "qa", "action": "Add regression test"},
            {"phase": "review", "agent": "security", "action": "Review fix for side effects"},
        ],
        "release_flow": [
            {"phase": "audit", "agent": "architect", "action": "Review decisions and version consistency"},
            {"phase": "validate", "agent": "qa", "action": "Run full test suite and quality gates"},
            {"phase": "security", "agent": "security", "action": "Security review of all changes"},
            {"phase": "deploy", "agent": "devops", "action": "Execute deployment playbook"},
        ],
        "onboarding": [
            {"phase": "orient", "agent": "architect", "action": "Read project structure and manifest"},
            {"phase": "inspect", "agent": "qa", "action": "Run tests and verify build"},
            {"phase": "configure", "agent": "devops", "action": "Set up development environment"},
        ],
    }
    return phases_map.get(playbook_name, [
        {"phase": "plan", "agent": "architect", "action": "Plan execution"},
        {"phase": "execute", "agent": "qa", "action": "Execute and verify"},
        {"phase": "review", "agent": "security", "action": "Final review"},
    ])


def write_orchestration(target: pathlib.Path) -> dict:
    """Generate and write orchestration configs."""
    orch_dir = target / "ai" / "orchestration"
    orch_dir.mkdir(parents=True, exist_ok=True)

    squad = generate_squad(target)
    swarm = generate_swarm(target)

    squad_path = orch_dir / "squad.yaml"
    swarm_path = orch_dir / "swarm.yaml"

    # Write as readable YAML-like format
    squad_path.write_text(_to_yaml(squad), encoding="utf-8")
    swarm_path.write_text(_to_yaml(swarm), encoding="utf-8")

    return {
        "squad": str(squad_path.relative_to(target)),
        "swarm": str(swarm_path.relative_to(target)),
        "agents": len(squad.get("specialists", [])) + 2,  # + lead + gate
        "workflows": len(squad.get("workflows", [])),
    }


def _to_yaml(data: dict, indent: int = 0) -> str:
    """Convert dict to readable YAML-like string."""
    lines: list[str] = []
    prefix = "  " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_to_yaml(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}:")
            for item in value:
                if isinstance(item, dict):
                    first = True
                    for k, v in item.items():
                        if first:
                            lines.append(f"{prefix}  - {k}: {_scalar(v)}")
                            first = False
                        else:
                            lines.append(f"{prefix}    {k}: {_scalar(v)}")
                else:
                    lines.append(f"{prefix}  - {_scalar(item)}")
        else:
            lines.append(f"{prefix}{key}: {_scalar(value)}")
    return "\n".join(lines)


def _scalar(v: object) -> str:
    """Format a scalar value for YAML output."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, list):
        return "[" + ", ".join(str(i) for i in v) + "]"
    return str(v)


def cmd_list(target: pathlib.Path) -> None:
    """Show orchestration roster."""
    personas = _load_personas(target)
    playbooks = _load_playbooks(target)

    print("Squad Roster:")
    print(f"  Lead: architect")
    for p in personas:
        name = p.get("name", "")
        if name not in ("architect", "security"):
            print(f"  Specialist: {name} — {p.get('description', '')[:60]}")
    print(f"  Gate: security")

    print(f"\nSwarm Agents: {len(personas)}")
    for p in personas:
        parallel = "parallel" if p.get("name") not in ("architect", "security") else "sequential"
        print(f"  {p.get('name', ''):<15} ({parallel})")

    print(f"\nWorkflows: {len(playbooks)}")
    for pb in playbooks:
        print(f"  {pb['name']:<20} {pb['title']}")


def cmd_json(target: pathlib.Path) -> None:
    """Output orchestration configs as JSON."""
    result = {
        "squad": generate_squad(target),
        "swarm": generate_swarm(target),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_generate(target: pathlib.Path) -> None:
    """Generate orchestration configs to ai/orchestration/."""
    result = write_orchestration(target)
    print(f"Generated orchestration configs:")
    print(f"  Squad: {result['squad']} ({result['agents']} agents, {result['workflows']} workflows)")
    print(f"  Swarm: {result['swarm']}")
    print(f"\nAgents can read these to coordinate multi-agent workflows.")


def main() -> None:
    target = pathlib.Path(".")
    subcmd = ""
    args = sys.argv[1:]

    i = 0
    while i < len(args):
        if args[i] == "--target" and i + 1 < len(args):
            target = pathlib.Path(args[i + 1]).resolve()
            i += 2
        elif args[i] == "--list":
            subcmd = "list"
            i += 1
        elif args[i] == "--json":
            subcmd = "json"
            i += 1
        else:
            i += 1

    if subcmd == "list":
        cmd_list(target)
    elif subcmd == "json":
        cmd_json(target)
    else:
        cmd_generate(target)


if __name__ == "__main__":
    main()
