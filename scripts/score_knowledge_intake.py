#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib


def detect_root() -> pathlib.Path:
    script_root = pathlib.Path(__file__).resolve().parent.parent
    cwd_root = pathlib.Path.cwd()
    if (cwd_root / "ai" / "experience").exists():
        return cwd_root
    return script_root


ROOT = detect_root()
REPORTS = ROOT / "ai" / "experience" / "reports"
INTAKE_PATH = REPORTS / "0dai-knowledge-intake.json"
SCORED_PATH = REPORTS / "0dai-knowledge-intake-scored.json"


def main() -> None:
    if not INTAKE_PATH.exists():
        raise SystemExit(f"missing intake summary: {INTAKE_PATH}")

    try:
        intake = json.loads(INTAKE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"failed to parse {INTAKE_PATH}: {exc}")
    events_total = intake.get("events_total", 0)
    candidate_types = intake.get("candidate_types", {})
    skill_hits = candidate_types.get("skill", 0)
    rule_hits = candidate_types.get("rule", 0)

    score = 0
    score += min(events_total, 10)
    score += skill_hits * 2
    score += rule_hits * 3

    confidence = "low"
    if score >= 8:
        confidence = "high"
    elif score >= 4:
        confidence = "medium"

    duplicate_key = f"{intake.get('repo', ROOT.name)}:{intake.get('recommended_issue_type', 'ai_lesson')}"
    intake["score"] = score
    intake["confidence"] = confidence
    intake["duplicate_key"] = duplicate_key
    intake["recommend_open_issue"] = (
        intake.get("recommend_open_issue", False) and confidence != "low"
    )

    SCORED_PATH.write_text(json.dumps(intake, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {SCORED_PATH}")


if __name__ == "__main__":
    main()
