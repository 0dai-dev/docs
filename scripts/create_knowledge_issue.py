#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import tempfile


def detect_root() -> pathlib.Path:
    script_root = pathlib.Path(__file__).resolve().parent.parent
    cwd_root = pathlib.Path.cwd()
    if (cwd_root / "ai" / "experience").exists():
        return cwd_root
    return script_root


ROOT = detect_root()
REPORTS = ROOT / "ai" / "experience" / "reports"
INTAKE_PATH = REPORTS / "0dai-knowledge-intake-scored.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=os.environ.get("ODAI_KNOWLEDGE_REPO", ""))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not INTAKE_PATH.exists():
        raise SystemExit(f"missing intake summary: {INTAKE_PATH}")

    intake = json.loads(INTAKE_PATH.read_text(encoding="utf-8"))
    if not intake.get("recommend_open_issue") and not args.force:
        print("skip issue creation: threshold not met")
        return

    target_repo = args.repo
    if not target_repo:
        print("skip issue creation: no target repo configured")
        return

    title = f"0dai intake: {intake.get('repo', 'repo')}"
    body = "\n".join(
        [
            "## Summary",
            intake.get("summary", "0dai knowledge intake"),
            "",
            "## Metrics",
            f"- Events total: {intake.get('events_total', 0)}",
            f"- Candidate types: {json.dumps(intake.get('candidate_types', {}), ensure_ascii=False)}",
            f"- By tool: {json.dumps(intake.get('by_tool', {}), ensure_ascii=False)}",
            f"- By task type: {json.dumps(intake.get('by_task_type', {}), ensure_ascii=False)}",
            f"- Score: {intake.get('score', 0)}",
            f"- Confidence: {intake.get('confidence', 'low')}",
            f"- Duplicate key: {intake.get('duplicate_key', 'n/a')}",
            "",
            "## Recommendation",
            f"- Issue type: {intake.get('recommended_issue_type', 'ai_lesson')}",
        ]
    )

    if args.dry_run:
        print(f"dry-run issue create in {target_repo}: {title}")
        return

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
        tmp.write(body)
        tmp_path = tmp.name

    try:
        subprocess.run(
            [
                "gh",
                "issue",
                "create",
                "--repo",
                target_repo,
                "--title",
                title,
                "--label",
                "ai",
                "--label",
                "intake",
                "--label",
                f"confidence:{intake.get('confidence', 'low')}",
                "--body-file",
                tmp_path,
            ],
            check=True,
        )
    finally:
        pathlib.Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
