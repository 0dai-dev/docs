#!/usr/bin/env python3
"""0dai Pre-Release Auditor — automated release readiness gate.

Combines roadmap guardian, template validation, smoke test, and git state
checks into a single pass/fail report. Run before tagging a release.

Usage:
    python3 scripts/release_auditor.py              # full audit
    python3 scripts/release_auditor.py --json        # JSON output
    python3 scripts/release_auditor.py --fix         # show fix suggestions
    0dai audit                                       # via CLI
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"
SKIP = "SKIP"


def _read(rel: str) -> str | None:
    path = ROOT / rel
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return None


def _run(cmd: list[str], cwd: str | None = None) -> tuple[int, str]:
    result = subprocess.run(
        cmd, capture_output=True, text=True,
        cwd=cwd or str(ROOT),
    )
    return result.returncode, (result.stdout + result.stderr).strip()


# --- Check Groups ---

def check_version() -> list[tuple[str, str, str]]:
    """Version file, CHANGELOG, release notes consistency."""
    results = []
    version_text = _read("VERSION")
    if not version_text:
        results.append((FAIL, "version-file", "VERSION file missing"))
        return results

    version = version_text.strip()
    results.append((PASS, "version-file", f"VERSION = {version}"))

    changelog = _read("CHANGELOG.md") or ""
    if f"## v{version}" in changelog:
        results.append((PASS, "version-changelog", f"CHANGELOG has v{version} entry"))
    else:
        results.append((FAIL, "version-changelog", f"CHANGELOG missing v{version} entry"))

    rn = ROOT / f"release-notes/v{version}.md"
    if rn.is_file():
        results.append((PASS, "version-release-notes", f"release-notes/v{version}.md exists"))
    else:
        results.append((FAIL, "version-release-notes", f"release-notes/v{version}.md missing"))

    # Check bootstrap/common.sh version matches
    common = _read("bootstrap/common.sh") or ""
    if f'CURRENT_AI_VERSION="{version}"' in common:
        results.append((PASS, "version-bootstrap", "bootstrap/common.sh version matches"))
    else:
        results.append((FAIL, "version-bootstrap", f"bootstrap/common.sh CURRENT_AI_VERSION != {version}"))

    # Check SDK version
    sdk_init = _read("sdk/zerodayai/__init__.py") or ""
    if f'__version__ = "{version}"' in sdk_init:
        results.append((PASS, "version-sdk", "SDK __version__ matches"))
    else:
        results.append((WARN, "version-sdk", f"SDK __version__ != {version}"))

    return results


def check_git_state() -> list[tuple[str, str, str]]:
    """Working tree clean, no uncommitted changes."""
    results = []

    code, output = _run(["git", "status", "--porcelain"])
    if code != 0:
        results.append((SKIP, "git-status", "Not a git repository"))
        return results

    # Filter out untracked files that are expected
    dirty_lines = [
        l for l in output.splitlines()
        if l.strip() and not l.startswith("??")
    ]

    if not dirty_lines:
        results.append((PASS, "git-clean", "Working tree clean (no uncommitted changes)"))
    else:
        results.append((WARN, "git-uncommitted", f"{len(dirty_lines)} uncommitted change(s)"))

    # Check if we're on main
    code, branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if branch == "main":
        results.append((PASS, "git-branch", "On main branch"))
    else:
        results.append((WARN, "git-branch", f"On branch '{branch}', not main"))

    return results


def check_templates() -> list[tuple[str, str, str]]:
    """Run validate_templates.py."""
    results = []
    script = ROOT / "scripts" / "validate_templates.py"
    if not script.is_file():
        results.append((SKIP, "templates", "validate_templates.py not found"))
        return results

    code, output = _run(["python3", str(script)])
    if code == 0:
        results.append((PASS, "templates-valid", "Template validation passed"))
    else:
        results.append((FAIL, "templates-valid", f"Template validation failed: {output[:200]}"))

    return results


def check_guardian() -> list[tuple[str, str, str]]:
    """Run roadmap guardian checks."""
    results = []
    script = ROOT / "scripts" / "roadmap_guardian.py"
    if not script.is_file():
        results.append((SKIP, "guardian", "roadmap_guardian.py not found"))
        return results

    code, output = _run(["python3", str(script)])
    if code == 0:
        results.append((PASS, "guardian-pass", "Roadmap guardian passed"))
    else:
        # Extract failures from output
        fail_lines = [l for l in output.splitlines() if "FAIL" in l]
        if fail_lines:
            for fl in fail_lines[:5]:
                results.append((FAIL, "guardian-check", fl.strip()))
        else:
            results.append((FAIL, "guardian-pass", f"Roadmap guardian failed"))

    return results


def check_migrations() -> list[tuple[str, str, str]]:
    """Verify migration chain exists for current version."""
    results = []
    version = (_read("VERSION") or "").strip()
    if not version:
        return results

    migrations_dir = ROOT / "bootstrap" / "migrations"
    if not migrations_dir.is_dir():
        results.append((WARN, "migrations-dir", "No migrations directory"))
        return results

    # Check direct migration from 0.1.1 exists
    direct = migrations_dir / f"0.1.1_to_{version}.sh"
    if direct.is_file():
        results.append((PASS, "migration-direct", f"Direct migration 0.1.1 → {version} exists"))
    else:
        results.append((WARN, "migration-direct", f"No direct migration 0.1.1 → {version}"))

    return results


def check_smoke_runnable() -> list[tuple[str, str, str]]:
    """Check that smoke test script exists and is executable."""
    results = []
    smoke = ROOT / "tests" / "smoke_test.sh"
    if not smoke.is_file():
        results.append((FAIL, "smoke-exists", "tests/smoke_test.sh missing"))
        return results

    results.append((PASS, "smoke-exists", "smoke_test.sh exists"))

    # Check version reference
    smoke_text = smoke.read_text(encoding="utf-8")
    version = (_read("VERSION") or "").strip()
    if version and version in smoke_text:
        results.append((PASS, "smoke-version", f"smoke_test.sh references v{version}"))
    elif version:
        results.append((FAIL, "smoke-version", f"smoke_test.sh does not reference v{version}"))

    return results


def check_changelog_quality() -> list[tuple[str, str, str]]:
    """Check that CHANGELOG entry has substance."""
    results = []
    version = (_read("VERSION") or "").strip()
    changelog = _read("CHANGELOG.md") or ""

    # Find the section for current version
    pattern = f"## v{version}"
    idx = changelog.find(pattern)
    if idx < 0:
        return results

    # Find next section
    next_section = changelog.find("\n## v", idx + 1)
    if next_section < 0:
        section = changelog[idx:]
    else:
        section = changelog[idx:next_section]

    lines = [l for l in section.splitlines() if l.startswith("- ")]
    if len(lines) >= 1:
        results.append((PASS, "changelog-entries", f"{len(lines)} changelog entries for v{version}"))
    else:
        results.append((WARN, "changelog-entries", f"No bullet entries in v{version} changelog"))

    return results


# --- Main ---

def run_audit() -> list[tuple[str, str, str]]:
    all_results = []
    all_results.extend(check_version())
    all_results.extend(check_git_state())
    all_results.extend(check_templates())
    all_results.extend(check_guardian())
    all_results.extend(check_migrations())
    all_results.extend(check_smoke_runnable())
    all_results.extend(check_changelog_quality())
    return all_results


def print_report(results: list[tuple[str, str, str]], show_fix: bool = False) -> None:
    version = (_read("VERSION") or "unknown").strip()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    fails = [r for r in results if r[0] == FAIL]
    warns = [r for r in results if r[0] == WARN]
    passes = [r for r in results if r[0] == PASS]
    skips = [r for r in results if r[0] == SKIP]

    print(f"## Pre-Release Audit  v{version}  ({now})\n")
    print(f"checks={len(results)}  pass={len(passes)}  warn={len(warns)}  fail={len(fails)}  skip={len(skips)}\n")

    if fails:
        print("### FAILURES (must fix before release)")
        for _, check_id, msg in fails:
            print(f"  FAIL  {check_id}: {msg}")
        print()

    if warns:
        print("### WARNINGS (review recommended)")
        for _, check_id, msg in warns:
            print(f"  WARN  {check_id}: {msg}")
        print()

    if skips:
        print("### SKIPPED")
        for _, check_id, msg in skips:
            print(f"  SKIP  {check_id}: {msg}")
        print()

    if fails:
        print(f"audit=FAIL  ({len(fails)} blocking issue(s))")
        if show_fix:
            print("\n### Fix Suggestions")
            for _, check_id, msg in fails:
                if "CHANGELOG" in check_id:
                    print(f"  → Run: 0dai changelog --version {version} --apply")
                elif "release-notes" in check_id:
                    print(f"  → Create: release-notes/v{version}.md")
                elif "bootstrap" in check_id:
                    print(f"  → Update CURRENT_AI_VERSION in bootstrap/common.sh")
                elif "templates" in check_id:
                    print(f"  → Run: python3 scripts/validate_templates.py  (fix reported issues)")
                elif "guardian" in check_id:
                    print(f"  → Run: python3 scripts/roadmap_guardian.py  (fix reported issues)")
                elif "smoke" in check_id:
                    print(f"  → Update version references in tests/smoke_test.sh")
    else:
        print(f"audit=PASS  (ready for release)")


def print_json(results: list[tuple[str, str, str]]) -> None:
    version = (_read("VERSION") or "unknown").strip()
    output = {
        "version": version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_checks": len(results),
        "pass": sum(1 for r in results if r[0] == PASS),
        "warn": sum(1 for r in results if r[0] == WARN),
        "fail": sum(1 for r in results if r[0] == FAIL),
        "skip": sum(1 for r in results if r[0] == SKIP),
        "ready": all(r[0] != FAIL for r in results),
        "checks": [
            {"status": r[0], "id": r[1], "message": r[2]}
            for r in results
        ],
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def main() -> None:
    show_json = "--json" in sys.argv
    show_fix = "--fix" in sys.argv

    results = run_audit()

    if show_json:
        print_json(results)
    else:
        print_report(results, show_fix)

    has_fail = any(r[0] == FAIL for r in results)
    sys.exit(1 if has_fail else 0)


if __name__ == "__main__":
    main()
