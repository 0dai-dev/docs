#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import pathlib


def detect_root() -> pathlib.Path:
    script_root = pathlib.Path(__file__).resolve().parent.parent
    cwd_root = pathlib.Path.cwd()
    if (cwd_root / "ai" / "experience").exists():
        return cwd_root
    return script_root


ROOT = detect_root()
EXPERIENCE_ROOT = ROOT / "ai" / "experience"
OUTBOX = EXPERIENCE_ROOT / "outbox"
EVENTS = EXPERIENCE_ROOT / "events"
REPORTS = EXPERIENCE_ROOT / "reports"


def load_json_events(directory: pathlib.Path) -> list[dict]:
    events: list[dict] = []
    if not directory.exists():
        return events
    for path in sorted(directory.glob("*.json")):
        try:
            events.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"warning: skipping malformed file {path}: {exc}")
    return events


def main() -> None:
    outbox_events = load_json_events(OUTBOX)
    archived_events = load_json_events(EVENTS)
    all_events = archived_events + outbox_events

    by_tool: dict[str, int] = {}
    by_task_type: dict[str, int] = {}
    candidate_types: dict[str, int] = {}
    ci_success = 0

    for event in all_events:
        by_tool[event.get("tool", "unknown")] = (
            by_tool.get(event.get("tool", "unknown"), 0) + 1
        )
        by_task_type[event.get("task_type", "unknown")] = (
            by_task_type.get(event.get("task_type", "unknown"), 0) + 1
        )
        candidate_types[event.get("candidate_type", "none")] = (
            candidate_types.get(event.get("candidate_type", "none"), 0) + 1
        )
        if event.get("ci_passed") is True:
            ci_success += 1

    report = {
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "repo": ROOT.name,
        "events_total": len(all_events),
        "outbox_events": len(outbox_events),
        "archived_events": len(archived_events),
        "ci_success_count": ci_success,
        "by_tool": by_tool,
        "by_task_type": by_task_type,
        "candidate_types": candidate_types,
    }

    REPORTS.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS / "0dai-experience-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {report_path}")


if __name__ == "__main__":
    main()
