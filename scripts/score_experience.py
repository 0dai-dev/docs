#!/usr/bin/env python3
"""0dai Experience Auto-Scorer — rank candidates by impact and frequency.

Reads ai/experience/candidates/ and ai/experience/events/ to compute
a promotion score for each candidate. Higher scores indicate stronger
evidence for promotion.

Usage:
    python3 scripts/score_experience.py --target <path>
    python3 scripts/score_experience.py --target <path> --json
    python3 scripts/score_experience.py --target <path> --auto-promote
    0dai score-experience --target <path>

Scoring dimensions:
    - Recurrence (0-10): how many times the pattern was observed
    - CI signal (0-5): pass rate of associated events
    - Stability (0-3): no reverts within 7 days
    - Scope clarity (0-2): specific file paths vs wildcard
    - Review quality (0-3): human review outcomes
    - Type weight (0-2): rules/anti-patterns weighted higher

Total possible: 25 points
    >= 18: recommend promote (auto-promotable)
    >= 10: review recommended
    < 10: defer (needs more evidence)
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import time


def _parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter from markdown."""
    result: dict = {}
    if not text.startswith("---"):
        return result
    end = text.find("---", 3)
    if end < 0:
        return result
    for line in text[3:end].splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if val.startswith("[") and val.endswith("]"):
                val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",") if v.strip()]
            elif val.lower() in ("true", "false"):
                val = val.lower() == "true"
            else:
                try:
                    val = int(val)
                except ValueError:
                    val = val.strip('"').strip("'")
            result[key] = val
    return result


def load_candidates(target: pathlib.Path) -> list[dict]:
    """Load all candidate files with parsed frontmatter."""
    candidates_dir = target / "ai" / "experience" / "candidates"
    if not candidates_dir.is_dir():
        return []

    candidates = []
    for path in sorted(candidates_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta = _parse_frontmatter(text)
        meta["_path"] = str(path)
        meta["_file"] = path.name
        meta["_body"] = text
        candidates.append(meta)

    return candidates


def load_events(target: pathlib.Path) -> list[dict]:
    """Load all archived events for cross-referencing."""
    events: list[dict] = []
    for subdir in ["events", "outbox"]:
        events_dir = target / "ai" / "experience" / subdir
        if not events_dir.is_dir():
            continue
        for path in sorted(events_dir.glob("*.json")):
            try:
                events.append(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
    return events


def score_candidate(candidate: dict, events: list[dict]) -> dict:
    """Score a single candidate across multiple dimensions."""
    scores: dict[str, int] = {}

    # 1. Recurrence (0-10): based on number of source events
    sources = candidate.get("sources", [])
    if isinstance(sources, str):
        sources = [s.strip() for s in sources.split(",")]
    occurrences = len(sources)
    scores["recurrence"] = min(occurrences * 2, 10)

    # 2. CI signal (0-5): pass rate of matching events
    source_ids = set(sources)
    matching_events = [e for e in events if e.get("id") in source_ids]
    if not matching_events:
        # Try matching by summary
        summary = candidate.get("id", "").replace("candidate.", "").replace("-", " ")
        matching_events = [e for e in events if summary and summary in e.get("summary", "").lower().replace("-", " ")]

    ci_applicable = [e for e in matching_events if "ci_passed" in e]
    if ci_applicable:
        ci_pass_rate = sum(1 for e in ci_applicable if e.get("ci_passed")) / len(ci_applicable)
        scores["ci_signal"] = round(ci_pass_rate * 5)
    else:
        scores["ci_signal"] = 2  # neutral if no CI data

    # 3. Stability (0-3): no reverts
    reverted = any(e.get("reverted_within_7d") for e in matching_events)
    human_takeover = any(e.get("human_takeover") for e in matching_events)
    scores["stability"] = 3 if not reverted and not human_takeover else (1 if not reverted else 0)

    # 4. Scope clarity (0-2): specific paths vs wildcards
    scope_paths = candidate.get("scope", {})
    if isinstance(scope_paths, dict):
        scope_paths = scope_paths.get("paths", [])
    if isinstance(scope_paths, str):
        try:
            scope_paths = json.loads(scope_paths)
        except (json.JSONDecodeError, ValueError):
            scope_paths = [scope_paths]

    has_specific = any(p and p != "**/*" for p in scope_paths) if scope_paths else False
    scores["scope_clarity"] = 2 if has_specific else 0

    # 5. Review quality (0-3): human review outcomes
    reviewed = [e for e in matching_events if e.get("review_outcome") in ("approved", "changes_requested", "commented")]
    approved = [e for e in reviewed if e.get("review_outcome") == "approved"]
    if approved:
        scores["review_quality"] = 3
    elif reviewed:
        scores["review_quality"] = 1
    else:
        scores["review_quality"] = 0

    # 6. Type weight (0-2): rules and anti-patterns are higher value
    ctype = candidate.get("type", "skill")
    type_weights = {"rule": 2, "anti-pattern": 2, "skill": 1, "playbook": 1}
    scores["type_weight"] = type_weights.get(ctype, 0)

    # Total
    total = sum(scores.values())

    # Recommendation
    if total >= 18:
        recommendation = "promote"
    elif total >= 10:
        recommendation = "review"
    else:
        recommendation = "defer"

    return {
        "candidate_id": candidate.get("id", "unknown"),
        "type": ctype,
        "confidence": candidate.get("confidence", "medium"),
        "occurrences": occurrences,
        "scores": scores,
        "total_score": total,
        "max_score": 25,
        "recommendation": recommendation,
    }


def score_all(target: pathlib.Path) -> dict:
    """Score all candidates and return summary."""
    candidates = load_candidates(target)
    events = load_events(target)

    results = []
    for c in candidates:
        scored = score_candidate(c, events)
        scored["file"] = c.get("_file", "")
        results.append(scored)

    results.sort(key=lambda x: -x["total_score"])

    summary = {
        "total_candidates": len(results),
        "promote": len([r for r in results if r["recommendation"] == "promote"]),
        "review": len([r for r in results if r["recommendation"] == "review"]),
        "defer": len([r for r in results if r["recommendation"] == "defer"]),
    }

    return {"candidates": results, "summary": summary}


def auto_promote(target: pathlib.Path) -> dict:
    """Auto-promote candidates with score >= 18."""
    result = score_all(target)
    promoted = []

    candidates_dir = target / "ai" / "experience" / "candidates"
    accepted_dir = target / "ai" / "experience" / "accepted"

    for scored in result["candidates"]:
        if scored["recommendation"] != "promote":
            continue

        src_path = candidates_dir / scored["file"]
        if not src_path.is_file():
            continue

        text = src_path.read_text(encoding="utf-8")
        ctype = scored["type"]
        subdir_map = {
            "rule": "rules", "skill": "skills",
            "playbook": "playbooks", "anti-pattern": "anti-patterns",
        }
        dest_subdir = subdir_map.get(ctype, "skills")
        dest_dir = accepted_dir / dest_subdir
        dest_dir.mkdir(parents=True, exist_ok=True)

        new_name = scored["file"].replace("candidate.", "accepted.", 1)
        dest_path = dest_dir / new_name

        new_text = text.replace("status: candidate", "status: accepted")
        new_text = re.sub(
            r"id: candidate\.",
            "id: lesson.",
            new_text,
        )
        # Add auto-score metadata
        new_text = new_text.replace(
            "---\n\n# Candidate",
            f"auto_score: {scored['total_score']}\nauto_promoted: {time.strftime('%Y-%m-%d')}\n---\n\n# Accepted",
        )

        dest_path.write_text(new_text, encoding="utf-8")
        src_path.unlink()
        promoted.append({
            "id": scored["candidate_id"],
            "score": scored["total_score"],
            "dest": str(dest_path.relative_to(target)),
        })

    return {"promoted": promoted, "count": len(promoted)}


def cmd_display(target: pathlib.Path) -> None:
    """Display scored candidates as table."""
    result = score_all(target)

    if not result["candidates"]:
        print("No candidates to score.")
        return

    print(f"{'ID':<45} {'Type':<12} {'Score':<8} {'Rec':<10} Details")
    print("-" * 100)
    for c in result["candidates"]:
        s = c["scores"]
        details = f"R:{s['recurrence']} CI:{s['ci_signal']} S:{s['stability']} SC:{s['scope_clarity']} RQ:{s['review_quality']} TW:{s['type_weight']}"
        print(f"{c['candidate_id']:<45} {c['type']:<12} {c['total_score']:>2}/25   {c['recommendation']:<10} {details}")

    sm = result["summary"]
    print(f"\n{sm['total_candidates']} candidate(s): {sm['promote']} promote, {sm['review']} review, {sm['defer']} defer")


def cmd_json(target: pathlib.Path) -> None:
    """Output scored candidates as JSON."""
    result = score_all(target)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main() -> None:
    target = pathlib.Path(".")
    subcmd = "display"
    args = sys.argv[1:]

    i = 0
    while i < len(args):
        if args[i] == "--target" and i + 1 < len(args):
            target = pathlib.Path(args[i + 1]).resolve()
            i += 2
        elif args[i] == "--json":
            subcmd = "json"
            i += 1
        elif args[i] == "--auto-promote":
            subcmd = "auto-promote"
            i += 1
        else:
            i += 1

    if subcmd == "json":
        cmd_json(target)
    elif subcmd == "auto-promote":
        result = auto_promote(target)
        if result["count"]:
            for p in result["promoted"]:
                print(f"[0dai] auto-promoted {p['id']} (score {p['score']}) → {p['dest']}")
            print(f"\n{result['count']} candidate(s) auto-promoted.")
        else:
            print("No candidates met the auto-promotion threshold (score >= 18).")
    else:
        cmd_display(target)


if __name__ == "__main__":
    main()
