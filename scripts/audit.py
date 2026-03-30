#!/usr/bin/env python3
"""Audit logger for 0dai operations.

Appends structured JSONL entries to ai/manifest/audit.jsonl.
Each entry records: timestamp, action, actor, target, and details.

Usage (from bootstrap scripts):
    python3 scripts/audit.py --target /path --action sync --actor cli --details "stack=fastapi"
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import sys


def log_audit(target: pathlib.Path, action: str, actor: str = "cli", details: str = "") -> None:
    audit_path = target / "ai" / "manifest" / "audit.jsonl"
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": dt.datetime.now(dt.UTC).isoformat(),
        "action": action,
        "actor": actor,
        "user": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
        "ai_version": None,
        "details": details,
    }

    version_file = target / "ai" / "VERSION"
    if version_file.is_file():
        try:
            entry["ai_version"] = version_file.read_text(encoding="utf-8").strip()
        except OSError:
            pass

    with audit_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> None:
    target = pathlib.Path(".")
    action = "unknown"
    actor = "cli"
    details = ""

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--target" and i + 1 < len(sys.argv):
            target = pathlib.Path(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--action" and i + 1 < len(sys.argv):
            action = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--actor" and i + 1 < len(sys.argv):
            actor = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--details" and i + 1 < len(sys.argv):
            details = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    log_audit(target, action, actor, details)
    print(f"[0dai-repo] audit: {action}")


if __name__ == "__main__":
    main()
