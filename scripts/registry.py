#!/usr/bin/env python3
"""Community stack registry for 0dai.

Browse, search, and install community-contributed stack definitions.

Usage:
    0dai registry --list                              # list all stacks
    0dai registry --search python                     # search by tag/name
    0dai registry --install django --target /path      # install stack to project
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "templates" / "layer" / "ai" / "registry" / "index.json"


def load_registry() -> list[dict]:
    if not REGISTRY_PATH.is_file():
        return []
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        return data.get("stacks", [])
    except (json.JSONDecodeError, OSError):
        return []


def list_stacks(stacks: list[dict]) -> None:
    if not stacks:
        print("[0dai-repo] registry is empty")
        return
    print(f"[0dai-repo] community stacks ({len(stacks)} available):\n")
    for s in stacks:
        tags = ", ".join(s.get("tags", []))
        print(f"  {s['name']}")
        print(f"    {s.get('description', '')}")
        print(f"    tags: {tags}  priority: {s.get('priority', 50)}")
        print()


def search_stacks(stacks: list[dict], query: str) -> list[dict]:
    q = query.lower()
    return [
        s for s in stacks
        if q in s.get("name", "").lower()
        or q in s.get("description", "").lower()
        or any(q in t.lower() for t in s.get("tags", []))
    ]


def install_stack(stacks: list[dict], name: str, target: pathlib.Path) -> None:
    match = [s for s in stacks if s["name"] == name]
    if not match:
        print(f"[0dai-repo] stack not found in registry: {name}")
        available = ", ".join(s["name"] for s in stacks)
        print(f"[0dai-repo] available: {available}")
        raise SystemExit(1)

    stack = match[0]
    dest_dir = target / "ai" / "stacks"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / f"{name}.yaml"

    if dest_file.exists():
        print(f"[0dai-repo] stack already installed: {name}")
        return

    lines = [
        f"# installed from 0dai community registry",
        f"",
        f"name: {stack['name']}",
        f"priority: {stack.get('priority', 50)}",
    ]

    if stack.get("match_primary"):
        lines.append("match_primary:")
        for m in stack["match_primary"]:
            lines.append(f"  - {m}")

    if stack.get("match_any"):
        lines.append("match_any:")
        for m in stack["match_any"]:
            lines.append(f"  - {m}")

    lines.append(f"recommended_layout: {stack.get('recommended_layout', 'backend-api')}")
    lines.append("agents:")
    lines.append("  - codex")
    lines.append("  - claude")
    lines.append("  - opencode")

    dest_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[0dai-repo] installed community stack: {name} → {dest_file.relative_to(target)}")


def main() -> None:
    stacks = load_registry()
    target = pathlib.Path(".")
    action = "list"
    query = ""
    name = ""

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] in ("--list", "-l"):
            action = "list"
            i += 1
        elif sys.argv[i] in ("--search", "-s") and i + 1 < len(sys.argv):
            action = "search"
            query = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] in ("--install", "-i") and i + 1 < len(sys.argv):
            action = "install"
            name = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--target" and i + 1 < len(sys.argv):
            target = pathlib.Path(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    if action == "list":
        list_stacks(stacks)
    elif action == "search":
        results = search_stacks(stacks, query)
        if results:
            list_stacks(results)
        else:
            print(f"[0dai-repo] no stacks matching '{query}'")
    elif action == "install":
        install_stack(stacks, name, target)


if __name__ == "__main__":
    main()
