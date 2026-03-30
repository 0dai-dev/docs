#!/usr/bin/env python3
"""0dai Write-Ahead Log — undo/redo for ai/ layer MCP mutations.

Records file state before each MCP write operation, enabling rollback.
WAL stored in ai/manifest/wal.jsonl.

Usage:
    python3 scripts/wal.py --target <path> --list            # show recent entries
    python3 scripts/wal.py --target <path> --undo             # undo last mutation
    python3 scripts/wal.py --target <path> --undo <id>        # undo specific entry
    python3 scripts/wal.py --target <path> --json             # JSON output
    0dai wal --target <path>
"""
from __future__ import annotations

import json
import pathlib
import sys
import time


def _wal_path(target: pathlib.Path) -> pathlib.Path:
    return target / "ai" / "manifest" / "wal.jsonl"


def load_entries(target: pathlib.Path, limit: int = 20) -> list[dict]:
    """Load WAL entries, most recent first."""
    path = _wal_path(target)
    if not path.is_file():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    entries.reverse()
    return entries[:limit]


def record(target: pathlib.Path, action: str, file_path: str, before: str | None, after: str | None) -> dict:
    """Record a WAL entry before a mutation."""
    path = _wal_path(target)
    path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "id": f"wal-{int(time.time() * 1000)}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
        "action": action,
        "file": file_path,
        "before_hash": _hash(before) if before else None,
        "after_hash": _hash(after) if after else None,
        "before_size": len(before) if before else 0,
        "after_size": len(after) if after else 0,
        "undone": False,
    }

    # Store before content for undo (base64 to keep JSONL safe)
    import base64
    if before is not None:
        entry["before_b64"] = base64.b64encode(before.encode("utf-8")).decode("ascii")

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry


def undo(target: pathlib.Path, entry_id: str | None = None) -> dict:
    """Undo a WAL entry by restoring the before state."""
    import base64

    path = _wal_path(target)
    if not path.is_file():
        return {"error": "no WAL entries", "undone": False}

    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # Find target entry
    target_entry = None
    if entry_id:
        for e in reversed(entries):
            if e.get("id") == entry_id and not e.get("undone"):
                target_entry = e
                break
    else:
        for e in reversed(entries):
            if not e.get("undone"):
                target_entry = e
                break

    if not target_entry:
        return {"error": "no undoable entry found", "undone": False}

    # Restore before state
    file_path = target / target_entry["file"]
    before_b64 = target_entry.get("before_b64")

    if before_b64:
        content = base64.b64decode(before_b64).decode("utf-8")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
    elif target_entry.get("before_size", 0) == 0:
        # File didn't exist before — remove it
        if file_path.is_file():
            file_path.unlink()

    # Mark as undone
    target_entry["undone"] = True
    target_entry["undone_at"] = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())

    # Rewrite WAL
    path.write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n",
        encoding="utf-8",
    )

    return {
        "undone": True,
        "entry_id": target_entry["id"],
        "action": target_entry["action"],
        "file": target_entry["file"],
        "restored": "before state" if before_b64 else "file removed",
    }


def _hash(content: str) -> str:
    import hashlib
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def cmd_list(target: pathlib.Path) -> None:
    entries = load_entries(target)
    if not entries:
        print("No WAL entries.")
        return

    print(f"{'ID':<25} {'Time':<22} {'Action':<20} {'File':<35} {'Undo'}")
    print("-" * 110)
    for e in entries:
        ts = e.get("timestamp", "")[:19]
        undone = "yes" if e.get("undone") else "no"
        print(f"{e.get('id', ''):<25} {ts:<22} {e.get('action', ''):<20} {e.get('file', ''):<35} {undone}")

    print(f"\n{len(entries)} entry(ies). Use '0dai wal --target <path> --undo' to revert last mutation.")


def cmd_undo(target: pathlib.Path, entry_id: str | None = None) -> None:
    result = undo(target, entry_id)
    if result.get("undone"):
        print(f"Undone: {result['entry_id']} ({result['action']} on {result['file']})")
        print(f"Restored: {result['restored']}")
    else:
        print(f"Error: {result.get('error', 'unknown')}")


def cmd_json(target: pathlib.Path) -> None:
    entries = load_entries(target, limit=50)
    print(json.dumps({"entries": entries, "count": len(entries)}, indent=2, ensure_ascii=False))


def main() -> None:
    target = pathlib.Path(".")
    subcmd = "list"
    undo_id = None
    args = sys.argv[1:]

    i = 0
    while i < len(args):
        if args[i] == "--target" and i + 1 < len(args):
            target = pathlib.Path(args[i + 1]).resolve()
            i += 2
        elif args[i] == "--list":
            subcmd = "list"
            i += 1
        elif args[i] == "--undo":
            subcmd = "undo"
            if i + 1 < len(args) and not args[i + 1].startswith("-"):
                undo_id = args[i + 1]
                i += 2
            else:
                i += 1
        elif args[i] == "--json":
            subcmd = "json"
            i += 1
        else:
            i += 1

    if subcmd == "undo":
        cmd_undo(target, undo_id)
    elif subcmd == "json":
        cmd_json(target)
    else:
        cmd_list(target)


if __name__ == "__main__":
    main()
