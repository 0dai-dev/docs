#!/usr/bin/env python3
"""0dai Prompt Versioning — track and diff system prompt changes over time.

Maintains a history of prompt file snapshots in ai/prompts/.history.json.
Each snapshot records file hash, version, and timestamp for change tracking.

Usage:
    python3 scripts/prompt_versioning.py --target <path>                # snapshot current state
    python3 scripts/prompt_versioning.py --target <path> --status       # show changed/unchanged
    python3 scripts/prompt_versioning.py --target <path> --history      # show version history
    python3 scripts/prompt_versioning.py --target <path> --diff <file>  # show diff for a file
    python3 scripts/prompt_versioning.py --target <path> --json         # JSON output
    0dai prompt-history --target <path>
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import time


def _hash_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _parse_frontmatter(text: str) -> dict:
    result: dict = {}
    if not text.startswith("---"):
        return result
    end = text.find("---", 3)
    if end < 0:
        return result
    for line in text[3:end].splitlines():
        line = line.strip()
        if ":" in line:
            k, _, v = line.partition(":")
            result[k.strip()] = v.strip()
    return result


def _collect_prompts(target: pathlib.Path) -> list[dict]:
    """Collect all prompt files from the project."""
    prompts = []
    prompt_dirs = [
        target / "ai" / "prompts",
        target / ".claude" / "agents",
        target / ".gemini" / "agents",
        target / ".aider" / "agents",
    ]

    for base in prompt_dirs:
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            meta = _parse_frontmatter(text)
            rel = str(path.relative_to(target))
            prompts.append({
                "path": rel,
                "hash": _hash_file(path),
                "version": meta.get("version", "unknown"),
                "name": meta.get("name", meta.get("role", meta.get("task", path.stem))),
                "managed": meta.get("managed", "false") == "true",
                "size": len(text),
            })

    return prompts


def _load_history(target: pathlib.Path) -> dict:
    history_path = target / "ai" / "prompts" / ".history.json"
    if not history_path.is_file():
        return {"schema": 1, "snapshots": []}
    try:
        return json.loads(history_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"schema": 1, "snapshots": []}


def _save_history(target: pathlib.Path, history: dict) -> None:
    history_path = target / "ai" / "prompts" / ".history.json"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(
        json.dumps(history, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def snapshot(target: pathlib.Path) -> dict:
    """Take a snapshot of current prompt state."""
    prompts = _collect_prompts(target)
    history = _load_history(target)

    now = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    entry = {
        "timestamp": now,
        "files": {p["path"]: {"hash": p["hash"], "version": p["version"]} for p in prompts},
        "total_files": len(prompts),
    }

    # Compute changes from previous snapshot
    prev = history["snapshots"][-1] if history["snapshots"] else None
    if prev:
        prev_files = prev.get("files", {})
        added = [p for p in entry["files"] if p not in prev_files]
        removed = [p for p in prev_files if p not in entry["files"]]
        changed = [
            p for p in entry["files"]
            if p in prev_files and entry["files"][p]["hash"] != prev_files[p]["hash"]
        ]
        entry["changes"] = {
            "added": added,
            "removed": removed,
            "modified": changed,
            "unchanged": len(entry["files"]) - len(added) - len(changed),
        }
    else:
        entry["changes"] = {
            "added": list(entry["files"].keys()),
            "removed": [],
            "modified": [],
            "unchanged": 0,
        }

    history["snapshots"].append(entry)

    # Keep last 50 snapshots
    if len(history["snapshots"]) > 50:
        history["snapshots"] = history["snapshots"][-50:]

    _save_history(target, history)

    return {
        "snapshot": now,
        "total_files": len(prompts),
        "changes": entry["changes"],
    }


def status(target: pathlib.Path) -> dict:
    """Compare current state against last snapshot."""
    prompts = _collect_prompts(target)
    history = _load_history(target)
    current = {p["path"]: p for p in prompts}

    if not history["snapshots"]:
        return {
            "status": "no_history",
            "message": "No snapshots yet. Run '0dai prompt-history --target <path>' to take first snapshot.",
            "current_files": len(prompts),
        }

    prev = history["snapshots"][-1]
    prev_files = prev.get("files", {})

    added = [p for p in current if p not in prev_files]
    removed = [p for p in prev_files if p not in current]
    modified = [
        p for p in current
        if p in prev_files and current[p]["hash"] != prev_files[p]["hash"]
    ]
    unchanged = [
        p for p in current
        if p in prev_files and current[p]["hash"] == prev_files[p]["hash"]
    ]

    return {
        "status": "clean" if not added and not removed and not modified else "changed",
        "last_snapshot": prev.get("timestamp", "unknown"),
        "added": added,
        "removed": removed,
        "modified": modified,
        "unchanged": len(unchanged),
        "total_current": len(current),
    }


def get_history(target: pathlib.Path) -> dict:
    """Get full snapshot history."""
    history = _load_history(target)
    entries = []
    for snap in reversed(history["snapshots"][-20:]):
        changes = snap.get("changes", {})
        entries.append({
            "timestamp": snap.get("timestamp", ""),
            "total_files": snap.get("total_files", 0),
            "added": len(changes.get("added", [])),
            "modified": len(changes.get("modified", [])),
            "removed": len(changes.get("removed", [])),
        })
    return {"history": entries, "total_snapshots": len(history["snapshots"])}


def cmd_snapshot(target: pathlib.Path) -> None:
    result = snapshot(target)
    ch = result["changes"]
    print(f"Snapshot taken: {result['snapshot']}")
    print(f"  Files: {result['total_files']}")
    print(f"  Added: {len(ch['added'])}, Modified: {len(ch['modified'])}, Removed: {len(ch['removed'])}, Unchanged: {ch['unchanged']}")
    if ch["modified"]:
        for f in ch["modified"]:
            print(f"    ~ {f}")
    if ch["added"]:
        for f in ch["added"]:
            print(f"    + {f}")


def cmd_status(target: pathlib.Path) -> None:
    result = status(target)
    if result["status"] == "no_history":
        print(result["message"])
        return
    print(f"Last snapshot: {result['last_snapshot']}")
    print(f"Status: {result['status']}")
    if result["added"]:
        for f in result["added"]:
            print(f"  + {f}")
    if result["modified"]:
        for f in result["modified"]:
            print(f"  ~ {f}")
    if result["removed"]:
        for f in result["removed"]:
            print(f"  - {f}")
    if result["status"] == "clean":
        print(f"  {result['unchanged']} file(s) unchanged")


def cmd_history(target: pathlib.Path) -> None:
    result = get_history(target)
    if not result["history"]:
        print("No snapshots yet.")
        return
    print(f"{'Timestamp':<28} {'Files':<8} {'Add':<6} {'Mod':<6} {'Rem':<6}")
    print("-" * 60)
    for h in result["history"]:
        print(f"{h['timestamp']:<28} {h['total_files']:<8} {h['added']:<6} {h['modified']:<6} {h['removed']:<6}")
    print(f"\n{result['total_snapshots']} snapshot(s) total")


def cmd_json(target: pathlib.Path) -> None:
    result = {
        "status": status(target),
        "history": get_history(target),
        "current_prompts": _collect_prompts(target),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main() -> None:
    target = pathlib.Path(".")
    subcmd = "snapshot"
    args = sys.argv[1:]

    i = 0
    while i < len(args):
        if args[i] == "--target" and i + 1 < len(args):
            target = pathlib.Path(args[i + 1]).resolve()
            i += 2
        elif args[i] == "--status":
            subcmd = "status"
            i += 1
        elif args[i] == "--history":
            subcmd = "history"
            i += 1
        elif args[i] == "--json":
            subcmd = "json"
            i += 1
        else:
            i += 1

    if subcmd == "status":
        cmd_status(target)
    elif subcmd == "history":
        cmd_history(target)
    elif subcmd == "json":
        cmd_json(target)
    else:
        cmd_snapshot(target)


if __name__ == "__main__":
    main()
