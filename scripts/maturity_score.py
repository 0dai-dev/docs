#!/usr/bin/env python3
"""Maturity scorecard for 0dai AI layer.

Evaluates the completeness and health of the AI operating layer
in a target project, outputting a 0-100 score with grade.

Usage:
    0dai maturity --target /path/to/project
    python3 scripts/maturity_score.py /path/to/project
"""
from __future__ import annotations

import json
import pathlib
import sys


def score_project(root: pathlib.Path) -> dict:
    checks: list[dict] = []
    total_weight = 0

    def check(name: str, weight: int, passed: bool, detail: str = "") -> None:
        nonlocal total_weight
        total_weight += weight
        checks.append({
            "name": name,
            "weight": weight,
            "passed": passed,
            "detail": detail,
        })

    # --- Core manifests (30 points) ---
    check("ai/VERSION", 5, (root / "ai/VERSION").is_file())
    check("ai/manifest/project.yaml", 5, (root / "ai/manifest/project.yaml").is_file())
    check("ai/manifest/discovery.json", 5, (root / "ai/manifest/discovery.json").is_file())
    check("ai/manifest/commands.yaml", 5, (root / "ai/manifest/commands.yaml").is_file())
    check("ai/manifest/applied-lock.json", 5, (root / "ai/manifest/applied-lock.json").is_file())
    check("ai/manifest/codebase-map.json", 5, (root / "ai/manifest/codebase-map.json").is_file())

    # --- Native configs (15 points) ---
    check("AGENTS.md", 5, (root / "AGENTS.md").is_file())
    check(".claude/CLAUDE.md", 5, (root / ".claude/CLAUDE.md").is_file())
    check(".codex/config.toml", 5, (root / ".codex/config.toml").is_file())

    # --- Experience lifecycle (15 points) ---
    events_dir = root / "ai/experience/events"
    candidates_dir = root / "ai/experience/candidates"
    accepted_dir = root / "ai/experience/accepted"
    events_count = len(list(events_dir.glob("*.json"))) if events_dir.is_dir() else 0
    candidates_count = len(list(candidates_dir.glob("*.md"))) if candidates_dir.is_dir() else 0
    accepted_count = sum(1 for _ in accepted_dir.rglob("*.md")) if accepted_dir.is_dir() else 0

    check("experience/events", 5, events_count > 0, f"{events_count} events")
    check("experience/candidates", 5, candidates_count > 0, f"{candidates_count} candidates")
    check("experience/accepted", 5, accepted_count > 0, f"{accepted_count} accepted")

    # --- Personas (10 points) ---
    personas_dir = root / "ai/personas"
    personas_count = len(list(personas_dir.glob("*.yaml"))) if personas_dir.is_dir() else 0
    check("personas", 10, personas_count >= 2, f"{personas_count} personas")

    # --- Org policy (10 points) ---
    policy = root / "ai/manifest/org-policy.json"
    check("org-policy", 10, policy.is_file())

    # --- IDE configs (5 points) ---
    check("IDE configs", 5, (root / ".vscode/settings.json").is_file() or (root / ".idea/0dai.xml").is_file())

    # --- Bulletins (5 points) ---
    bulletins_dir = root / "ai/bulletins"
    bulletins_count = len(list(bulletins_dir.glob("*.yaml"))) if bulletins_dir.is_dir() else 0
    check("bulletins", 5, bulletins_count > 0, f"{bulletins_count} bulletins")

    # --- Federation (5 points) ---
    check("federation", 5, (root / "ai/federation.yaml").is_file())

    # --- Audit log (5 points) ---
    check("audit-log", 5, (root / "ai/manifest/audit.jsonl").is_file())

    # Calculate score
    earned = sum(c["weight"] for c in checks if c["passed"])
    score = round(earned / total_weight * 100) if total_weight > 0 else 0

    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 60:
        grade = "C"
    elif score >= 40:
        grade = "D"
    else:
        grade = "F"

    return {
        "score": score,
        "grade": grade,
        "earned": earned,
        "total": total_weight,
        "checks": checks,
        "badge_url": f"https://img.shields.io/badge/0dai_maturity-{score}%25_{grade}-{'brightgreen' if score >= 75 else 'yellow' if score >= 50 else 'red'}.svg",
    }


def main() -> None:
    if len(sys.argv) < 2:
        target = pathlib.Path(".")
    else:
        target = pathlib.Path(sys.argv[1])
        if not target.is_dir():
            # Check if it's --target format
            for i, arg in enumerate(sys.argv):
                if arg == "--target" and i + 1 < len(sys.argv):
                    target = pathlib.Path(sys.argv[i + 1])
                    break

    if "--json" in sys.argv:
        result = score_project(target)
        print(json.dumps(result, indent=2))
        return

    result = score_project(target)
    print(f"\n  0dai Maturity Scorecard")
    print(f"  ═══════════════════════")
    print(f"  Score: {result['score']}/100  Grade: {result['grade']}")
    print(f"  Earned: {result['earned']}/{result['total']} points\n")

    for c in result["checks"]:
        status = "✓" if c["passed"] else "✗"
        detail = f" ({c['detail']})" if c["detail"] else ""
        print(f"  {status} [{c['weight']:2d}] {c['name']}{detail}")

    print(f"\n  Badge: {result['badge_url']}")
    print(f"  maturity={result['score']} grade={result['grade']}")


if __name__ == "__main__":
    main()
