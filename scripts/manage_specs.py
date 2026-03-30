#!/usr/bin/env python3
"""0dai Spec-Driven Development — create, list, and validate structured specifications.

Specs live in ai/specs/ and give agents structured context before starting work.

Usage:
    python3 scripts/manage_specs.py --target <path> --list
    python3 scripts/manage_specs.py --target <path> --new <name> [--title <title>] [--agent <name>] [--priority <level>]
    python3 scripts/manage_specs.py --target <path> --info <id>
    python3 scripts/manage_specs.py --target <path> --validate
    python3 scripts/manage_specs.py --target <path> --json
    0dai spec --target <path> --list|--new|--info|--validate|--json
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from datetime import datetime, timezone


ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT_DIR / "templates" / "layer" / "ai" / "specs" / "TEMPLATE.md"

REQUIRED_SECTIONS = ["Context", "Goal", "Requirements", "Acceptance Criteria"]
VALID_STATUSES = {"draft", "ready", "in-progress", "done", "cancelled"}
VALID_PRIORITIES = {"critical", "high", "medium", "low"}


def _parse_spec(path: pathlib.Path) -> dict | None:
    """Parse a spec file into metadata + body."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    entry: dict = {"file": path.name, "path": str(path)}
    if not text.startswith("---"):
        return entry

    end = text.find("---", 3)
    if end < 0:
        return entry

    # Parse frontmatter
    for line in text[3:end].splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            # Handle list values like [tag1, tag2]
            if val.startswith("[") and val.endswith("]"):
                val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",") if v.strip()]
            elif val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            entry[key] = val

    body = text[end + 3:].strip()
    entry["body"] = body

    # Extract section headers
    sections = re.findall(r"^## (.+)$", body, re.MULTILINE)
    entry["sections"] = sections

    # Count acceptance criteria
    criteria_total = body.count("- [ ]") + body.count("- [x]") + body.count("- [X]")
    criteria_done = body.count("- [x]") + body.count("- [X]")
    entry["criteria_total"] = criteria_total
    entry["criteria_done"] = criteria_done

    return entry


def _get_specs_dir(target: pathlib.Path) -> pathlib.Path:
    return target / "ai" / "specs"


def _list_specs(target: pathlib.Path) -> list[dict]:
    specs_dir = _get_specs_dir(target)
    if not specs_dir.is_dir():
        return []

    specs = []
    for path in sorted(specs_dir.glob("*.md")):
        if path.name in ("README.md", "TEMPLATE.md"):
            continue
        parsed = _parse_spec(path)
        if parsed:
            specs.append(parsed)
    return specs


def cmd_list(target: pathlib.Path) -> None:
    """List all specs in the project."""
    specs = _list_specs(target)

    if not specs:
        print("No specs found. Create one with: 0dai spec --new <name> --target <path>")
        return

    print(f"{'ID':<18} {'Status':<14} {'Priority':<10} {'Criteria':<10} Title")
    print("-" * 85)
    for s in specs:
        spec_id = s.get("id", "?")
        status = s.get("status", "?")
        priority = s.get("priority", "?")
        criteria = f"{s.get('criteria_done', 0)}/{s.get('criteria_total', 0)}"
        title = s.get("title", s["file"])
        print(f"{spec_id:<18} {status:<14} {priority:<10} {criteria:<10} {title}")

    # Summary
    statuses = {}
    for s in specs:
        st = s.get("status", "unknown")
        statuses[st] = statuses.get(st, 0) + 1

    parts = [f"{v} {k}" for k, v in sorted(statuses.items())]
    print(f"\n{len(specs)} spec(s): {', '.join(parts)}")


def cmd_new(target: pathlib.Path, name: str, title: str, agent: str, priority: str) -> None:
    """Create a new spec from template."""
    specs_dir = _get_specs_dir(target)
    specs_dir.mkdir(parents=True, exist_ok=True)

    # Auto-generate ID
    existing_ids = []
    for s in _list_specs(target):
        sid = s.get("id", "")
        m = re.match(r"SPEC-(\d+)", sid)
        if m:
            existing_ids.append(int(m.group(1)))

    next_id = max(existing_ids, default=0) + 1
    spec_id = f"SPEC-{next_id:03d}"

    # Sanitize name for filename
    safe_name = re.sub(r"[^a-z0-9-]", "-", name.lower())
    safe_name = re.sub(r"-+", "-", safe_name).strip("-")
    filename = f"{spec_id}-{safe_name}.md"

    if not title:
        title = name.replace("-", " ").title()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    content = f"""---
id: {spec_id}
title: {title}
status: draft
priority: {priority}
author: ""
created: {today}
updated: {today}
tags: []
agent: {agent}
---

## Context

Why is this work needed? What problem does it solve?

## Goal

One sentence describing what success looks like.

## Requirements

1. Requirement one
2. Requirement two
3. Requirement three

## Acceptance Criteria

- [ ] Criterion one
- [ ] Criterion two
- [ ] Criterion three

## Out of Scope

- What is explicitly NOT included in this spec

## Technical Notes

Implementation hints, constraints, dependencies, or references.
"""

    path = specs_dir / filename
    path.write_text(content, encoding="utf-8")
    print(f"Created {spec_id}: ai/specs/{filename}")
    print(f"Edit the spec, then set status to 'ready' when it's complete.")


def cmd_info(target: pathlib.Path, spec_id: str) -> None:
    """Show detailed info about a spec."""
    specs = _list_specs(target)
    found = None
    for s in specs:
        if s.get("id") == spec_id or s["file"].startswith(spec_id):
            found = s
            break

    if not found:
        print(f"Spec '{spec_id}' not found.", file=sys.stderr)
        sys.exit(1)

    print(f"ID:       {found.get('id', '?')}")
    print(f"Title:    {found.get('title', '?')}")
    print(f"Status:   {found.get('status', '?')}")
    print(f"Priority: {found.get('priority', '?')}")
    print(f"Author:   {found.get('author', '?')}")
    print(f"Agent:    {found.get('agent', '?')}")
    print(f"Created:  {found.get('created', '?')}")
    print(f"Updated:  {found.get('updated', '?')}")
    tags = found.get("tags", [])
    if isinstance(tags, list):
        print(f"Tags:     {', '.join(tags)}")
    print(f"Sections: {', '.join(found.get('sections', []))}")
    print(f"Criteria: {found.get('criteria_done', 0)}/{found.get('criteria_total', 0)} complete")
    print(f"File:     {found['file']}")

    if found.get("body"):
        print(f"\n{found['body']}")


def cmd_validate(target: pathlib.Path) -> None:
    """Validate all specs for structural completeness."""
    specs = _list_specs(target)

    if not specs:
        print("No specs to validate.")
        return

    errors = 0
    warnings = 0

    for s in specs:
        issues: list[str] = []

        # Check required frontmatter
        if not s.get("id"):
            issues.append("ERROR: missing 'id' in frontmatter")
            errors += 1
        if not s.get("title"):
            issues.append("ERROR: missing 'title' in frontmatter")
            errors += 1
        if s.get("status") and s["status"] not in VALID_STATUSES:
            issues.append(f"ERROR: invalid status '{s['status']}' (valid: {', '.join(sorted(VALID_STATUSES))})")
            errors += 1
        if s.get("priority") and s["priority"] not in VALID_PRIORITIES:
            issues.append(f"WARNING: non-standard priority '{s['priority']}'")
            warnings += 1

        # Check required sections
        sections = s.get("sections", [])
        for req in REQUIRED_SECTIONS:
            if req not in sections:
                issues.append(f"WARNING: missing section '## {req}'")
                warnings += 1

        # Check acceptance criteria exist
        if s.get("criteria_total", 0) == 0 and s.get("status") in ("ready", "in-progress"):
            issues.append("WARNING: no acceptance criteria for a ready/in-progress spec")
            warnings += 1

        if issues:
            print(f"\n{s.get('id', s['file'])}:")
            for issue in issues:
                print(f"  {issue}")

    if errors == 0 and warnings == 0:
        print(f"All {len(specs)} spec(s) valid.")
    else:
        print(f"\n{len(specs)} spec(s) checked: {errors} error(s), {warnings} warning(s)")
        if errors > 0:
            sys.exit(1)


def cmd_json(target: pathlib.Path) -> None:
    """Output specs as JSON."""
    specs = _list_specs(target)
    result = {
        "specs": [
            {
                "id": s.get("id"),
                "title": s.get("title"),
                "status": s.get("status"),
                "priority": s.get("priority"),
                "agent": s.get("agent"),
                "tags": s.get("tags", []),
                "criteria_total": s.get("criteria_total", 0),
                "criteria_done": s.get("criteria_done", 0),
                "sections": s.get("sections", []),
                "file": s.get("file"),
            }
            for s in specs
        ],
        "counts": {
            "total": len(specs),
            "draft": sum(1 for s in specs if s.get("status") == "draft"),
            "ready": sum(1 for s in specs if s.get("status") == "ready"),
            "in_progress": sum(1 for s in specs if s.get("status") == "in-progress"),
            "done": sum(1 for s in specs if s.get("status") == "done"),
        },
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main() -> None:
    target = pathlib.Path(".")
    subcmd = ""
    name = ""
    title = ""
    agent = ""
    priority = "medium"
    args = sys.argv[1:]

    i = 0
    while i < len(args):
        if args[i] == "--target" and i + 1 < len(args):
            target = pathlib.Path(args[i + 1]).resolve()
            i += 2
        elif args[i] == "--list":
            subcmd = "list"
            i += 1
        elif args[i] == "--new" and i + 1 < len(args):
            subcmd = "new"
            name = args[i + 1]
            i += 2
        elif args[i] == "--info" and i + 1 < len(args):
            subcmd = "info"
            name = args[i + 1]
            i += 2
        elif args[i] == "--validate":
            subcmd = "validate"
            i += 1
        elif args[i] == "--json":
            subcmd = "json"
            i += 1
        elif args[i] == "--title" and i + 1 < len(args):
            title = args[i + 1]
            i += 2
        elif args[i] == "--agent" and i + 1 < len(args):
            agent = args[i + 1]
            i += 2
        elif args[i] == "--priority" and i + 1 < len(args):
            priority = args[i + 1]
            i += 2
        else:
            i += 1

    if subcmd == "list":
        cmd_list(target)
    elif subcmd == "new":
        if not name:
            print("Usage: 0dai spec --new <name> --target <path>", file=sys.stderr)
            sys.exit(1)
        cmd_new(target, name, title, agent, priority)
    elif subcmd == "info":
        cmd_info(target, name)
    elif subcmd == "validate":
        cmd_validate(target)
    elif subcmd == "json":
        cmd_json(target)
    else:
        # Default: show summary
        specs = _list_specs(target)
        if specs:
            cmd_list(target)
        else:
            print("Spec-driven development: structured specifications for agents.")
            print("  --new <name>    Create a new spec")
            print("  --list          List all specs")
            print("  --info <id>     Show spec details")
            print("  --validate      Check specs for completeness")
            print("  --json          Output as JSON")


if __name__ == "__main__":
    main()
