#!/usr/bin/env python3
"""0dai Changelog Automation — generate CHANGELOG entries from git log.

Reads git history between tags (or from a given ref) and produces
a structured changelog entry grouped by commit type.

Usage:
    python3 scripts/generate_changelog.py                          # since last tag
    python3 scripts/generate_changelog.py --from v0.3.3 --to HEAD  # specific range
    python3 scripts/generate_changelog.py --version 0.4.0          # set version header
    python3 scripts/generate_changelog.py --apply                  # prepend to CHANGELOG.md
    python3 scripts/generate_changelog.py --json                   # JSON output
    0dai changelog [--from <ref>] [--to <ref>] [--version <ver>] [--apply] [--json]
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
CHANGELOG_PATH = ROOT_DIR / "CHANGELOG.md"

# Conventional commit prefixes → display categories
CATEGORIES = {
    "feat": "Features",
    "add": "Features",
    "fix": "Fixes",
    "refactor": "Refactoring",
    "docs": "Documentation",
    "test": "Tests",
    "ci": "CI/CD",
    "chore": "Chores",
    "perf": "Performance",
    "style": "Style",
    "build": "Build",
}


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT_DIR)] + list(args),
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def _get_latest_tag() -> str | None:
    tags = _git("tag", "-l", "--sort=-version:refname")
    if tags:
        return tags.splitlines()[0]
    return None


def _get_commits(from_ref: str, to_ref: str) -> list[dict]:
    """Get commits between two refs."""
    # Format: hash|subject|author|date
    log = _git(
        "log", f"{from_ref}..{to_ref}",
        "--pretty=format:%h|%s|%an|%ai",
        "--no-merges",
    )
    if not log:
        return []

    commits = []
    for line in log.splitlines():
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        hash_, subject, author, date = parts

        # Skip Co-Authored-By commits that are just metadata
        if subject.startswith("Co-Authored-By"):
            continue

        # Parse conventional commit prefix
        category = "other"
        message = subject
        m = re.match(r"^(\w+?)[\(:]", subject)
        if m:
            prefix = m.group(1).lower()
            if prefix in CATEGORIES:
                category = prefix
                # Strip prefix from message
                message = re.sub(r"^\w+[\(:].*?[\):]?\s*", "", subject).strip()
                if not message:
                    message = subject

        # Also detect by common patterns
        if category == "other":
            lower = subject.lower()
            if lower.startswith("add "):
                category = "feat"
                message = subject
            elif lower.startswith("fix "):
                category = "fix"
                message = subject
            elif lower.startswith("remove ") or lower.startswith("delete "):
                category = "chore"
                message = subject
            elif lower.startswith("update "):
                category = "chore"
                message = subject
            elif lower.startswith("prepare "):
                category = "chore"
                message = subject

        commits.append({
            "hash": hash_,
            "subject": subject,
            "message": message,
            "author": author,
            "date": date,
            "category": category,
        })

    return commits


def _group_commits(commits: list[dict]) -> dict[str, list[dict]]:
    """Group commits by category."""
    groups: dict[str, list[dict]] = {}
    for c in commits:
        cat = CATEGORIES.get(c["category"], "Other")
        groups.setdefault(cat, []).append(c)
    return groups


def _format_markdown(version: str, groups: dict[str, list[dict]], date: str) -> str:
    """Format grouped commits as markdown."""
    lines = [f"## v{version} - {date}", ""]

    # Preferred category order
    order = ["Features", "Fixes", "Refactoring", "Documentation", "Tests", "CI/CD", "Performance", "Chores", "Other"]

    for cat in order:
        if cat not in groups:
            continue
        commits = groups[cat]
        for c in commits:
            lines.append(f"- {c['message']}")

    lines.append("")
    return "\n".join(lines)


def cmd_generate(from_ref: str, to_ref: str, version: str, apply: bool) -> None:
    """Generate changelog entry."""
    commits = _get_commits(from_ref, to_ref)

    if not commits:
        print(f"No commits found between {from_ref} and {to_ref}.")
        return

    groups = _group_commits(commits)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = _format_markdown(version, groups, today)

    print(entry)
    print(f"---\n{len(commits)} commit(s) from {from_ref} to {to_ref}")

    if apply:
        if not CHANGELOG_PATH.is_file():
            print("CHANGELOG.md not found.", file=sys.stderr)
            sys.exit(1)

        existing = CHANGELOG_PATH.read_text(encoding="utf-8")
        # Insert after the first line (# Changelog header)
        header_end = existing.find("\n") + 1
        new_content = existing[:header_end] + "\n" + entry + existing[header_end:]
        CHANGELOG_PATH.write_text(new_content, encoding="utf-8")
        print(f"\nPrepended to {CHANGELOG_PATH}")


def cmd_json(from_ref: str, to_ref: str, version: str) -> None:
    """Output as JSON."""
    commits = _get_commits(from_ref, to_ref)
    groups = _group_commits(commits)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    result = {
        "version": version,
        "date": today,
        "from_ref": from_ref,
        "to_ref": to_ref,
        "total_commits": len(commits),
        "categories": {cat: len(items) for cat, items in groups.items()},
        "commits": commits,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main() -> None:
    from_ref = ""
    to_ref = "HEAD"
    version = ""
    apply = False
    output_json = False
    args = sys.argv[1:]

    i = 0
    while i < len(args):
        if args[i] == "--from" and i + 1 < len(args):
            from_ref = args[i + 1]
            i += 2
        elif args[i] == "--to" and i + 1 < len(args):
            to_ref = args[i + 1]
            i += 2
        elif args[i] == "--version" and i + 1 < len(args):
            version = args[i + 1]
            i += 2
        elif args[i] == "--apply":
            apply = True
            i += 1
        elif args[i] == "--json":
            output_json = True
            i += 1
        else:
            i += 1

    # Defaults
    if not from_ref:
        tag = _get_latest_tag()
        if tag:
            from_ref = tag
        else:
            # No tags — use initial commit
            from_ref = _git("rev-list", "--max-parents=0", "HEAD")

    if not version:
        # Read from VERSION file
        version_file = ROOT_DIR / "VERSION"
        if version_file.is_file():
            version = version_file.read_text(encoding="utf-8").strip()
        else:
            version = "unreleased"

    if output_json:
        cmd_json(from_ref, to_ref, version)
    else:
        cmd_generate(from_ref, to_ref, version, apply)


if __name__ == "__main__":
    main()
