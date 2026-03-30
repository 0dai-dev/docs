#!/usr/bin/env python3
"""Generate anonymized telemetry report from project experience data.

Creates ai/telemetry/reports/<timestamp>.json with aggregated metrics.
No source code, file paths, or credentials leave the project.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import sys


def detect_root() -> pathlib.Path:
    script_root = pathlib.Path(__file__).resolve().parent.parent
    cwd_root = pathlib.Path.cwd()
    if (cwd_root / "ai" / "experience").exists():
        return cwd_root
    return script_root


ROOT = detect_root()
EXPERIENCE = ROOT / "ai" / "experience"
TELEMETRY = ROOT / "ai" / "telemetry" / "reports"


def load_events() -> list[dict]:
    events: list[dict] = []
    for subdir in [EXPERIENCE / "events", EXPERIENCE / "outbox"]:
        if not subdir.is_dir():
            continue
        for path in sorted(subdir.glob("*.json")):
            try:
                events.append(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        for path in sorted(subdir.glob("*.jsonl")):
            try:
                for line in path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line:
                        events.append(json.loads(line))
            except (json.JSONDecodeError, OSError):
                continue
    return events


def count_accepted() -> dict[str, int]:
    counts: dict[str, int] = {}
    accepted = EXPERIENCE / "accepted"
    if not accepted.is_dir():
        return counts
    for category in ["rules", "skills", "playbooks", "anti-patterns"]:
        cat_dir = accepted / category
        if cat_dir.is_dir():
            counts[category] = sum(1 for f in cat_dir.glob("*.md") if f.is_file())
    return counts


def list_applied_bulletins() -> list[str]:
    bulletins_dir = ROOT / "ai" / "bulletins"
    if not bulletins_dir.is_dir():
        return []
    ids: list[str] = []
    for path in sorted(bulletins_dir.glob("*.yaml")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("id:"):
                ids.append(line.split(":", 1)[1].strip())
                break
    return ids


def detect_stack() -> str:
    discovery = ROOT / "ai" / "manifest" / "discovery.json"
    if discovery.is_file():
        try:
            return json.loads(discovery.read_text(encoding="utf-8")).get("stack", "unknown")
        except (json.JSONDecodeError, OSError):
            pass
    return "unknown"


def detect_repo_mode() -> str:
    cmap = ROOT / "ai" / "manifest" / "codebase-map.json"
    if cmap.is_file():
        try:
            return json.loads(cmap.read_text(encoding="utf-8")).get("repo_mode", "unknown")
        except (json.JSONDecodeError, OSError):
            pass
    return "unknown"


def read_version() -> str:
    vfile = ROOT / "ai" / "VERSION"
    if vfile.is_file():
        return vfile.read_text(encoding="utf-8").strip()
    return "unknown"


def generate_report() -> dict:
    events = load_events()
    accepted = count_accepted()
    bulletins = list_applied_bulletins()
    ttl_days = int(os.environ.get("ODAI_TELEMETRY_PERIOD_DAYS", "30"))

    # Aggregate metrics
    tool_usage: dict[str, int] = {}
    task_types: dict[str, int] = {}
    ci_passed = 0
    human_takeover = 0
    reverted = 0

    for event in events:
        tool = event.get("tool", "unknown")
        tool_usage[tool] = tool_usage.get(tool, 0) + 1
        tt = event.get("task_type", "unknown")
        task_types[tt] = task_types.get(tt, 0) + 1
        if event.get("ci_passed") is True:
            ci_passed += 1
        if event.get("human_takeover") is True:
            human_takeover += 1
        if event.get("reverted_within_7d") is True:
            reverted += 1

    total = max(len(events), 1)

    # Anonymize project name
    project_id = hashlib.sha256(ROOT.name.encode()).hexdigest()[:16]

    return {
        "schema": 2,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "project_id": project_id,
        "stack": detect_stack(),
        "repo_mode": detect_repo_mode(),
        "ai_version": read_version(),
        "period_days": ttl_days,
        "metrics": {
            "events_total": len(events),
            "ci_pass_rate": round(ci_passed / total, 2),
            "human_takeover_rate": round(human_takeover / total, 2),
            "revert_rate": round(reverted / total, 2),
        },
        "tool_usage": dict(sorted(tool_usage.items(), key=lambda x: -x[1])),
        "task_types": dict(sorted(task_types.items(), key=lambda x: -x[1])),
        "knowledge": {
            "rules_accepted": accepted.get("rules", 0),
            "skills_accepted": accepted.get("skills", 0),
            "playbooks_accepted": accepted.get("playbooks", 0),
            "anti_patterns_accepted": accepted.get("anti-patterns", 0),
        },
        "bulletins_applied": bulletins,
    }


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    report = generate_report()

    if dry_run:
        print(json.dumps(report, indent=2))
        print("\n[0dai-repo] dry-run: report not written")
        return

    TELEMETRY.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    out = TELEMETRY / f"{timestamp}.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[0dai-repo] wrote telemetry report to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
