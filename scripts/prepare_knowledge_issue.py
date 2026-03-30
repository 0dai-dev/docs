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
REPORT_PATH = EXPERIENCE_ROOT / "reports" / "0dai-experience-report.json"
INTAKE_PATH = EXPERIENCE_ROOT / "reports" / "0dai-knowledge-intake.json"


def main() -> None:
    if not REPORT_PATH.exists():
        raise SystemExit(f"missing report: {REPORT_PATH}")

    try:
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"failed to parse {REPORT_PATH}: {exc}")
    intake = {
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "repo": report.get("repo", ROOT.name),
        "summary": f"0dai knowledge intake for {report.get('repo', ROOT.name)}",
        "events_total": report.get("events_total", 0),
        "candidate_types": report.get("candidate_types", {}),
        "by_tool": report.get("by_tool", {}),
        "by_task_type": report.get("by_task_type", {}),
        "recommend_open_issue": report.get("events_total", 0) >= 3,
        "recommended_issue_type": "ai_lesson"
        if report.get("candidate_types", {}).get("skill", 0)
        else "ai_regression",
    }
    INTAKE_PATH.parent.mkdir(parents=True, exist_ok=True)
    INTAKE_PATH.write_text(json.dumps(intake, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {INTAKE_PATH}")


if __name__ == "__main__":
    main()
