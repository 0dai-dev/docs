#!/usr/bin/env python3
"""Roadmap Guardian: consistency checker for 0dai project state.

Verifies that VERSION, CHANGELOG, README, detectors, layouts, and docs
stay in sync as the project evolves. Designed to run before releases
and after major merges.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def check_version_consistency() -> list[tuple[str, str, str]]:
    results: list[tuple[str, str, str]] = []
    version = read_text("VERSION").strip()
    changelog = read_text("CHANGELOG.md")
    rn_path = ROOT / f"release-notes/v{version}.md"

    if f"## v{version}" in changelog:
        results.append((PASS, "version-changelog", f"CHANGELOG has v{version} entry"))
    else:
        results.append((FAIL, "version-changelog", f"CHANGELOG missing v{version} entry"))

    if rn_path.is_file():
        results.append((PASS, "version-release-notes", f"release-notes/v{version}.md exists"))
    else:
        results.append((FAIL, "version-release-notes", f"release-notes/v{version}.md missing"))

    return results


def check_stack_alignment() -> list[tuple[str, str, str]]:
    results: list[tuple[str, str, str]] = []

    # Collect actual layouts
    layout_dirs = sorted(
        d.name
        for d in (ROOT / "project_layouts").iterdir()
        if d.is_dir() and (d / "scaffold.sh").exists()
    )

    # Collect actual detector names
    detector_names = set()
    for f in (ROOT / "templates/layer/ai/patterns/detectors").glob("*.yaml"):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith("name:"):
                detector_names.add(line.split(":", 1)[1].strip())

    # Check README Included Stacks
    readme = read_text("README.md")
    for layout in layout_dirs:
        if f"`{layout}`" in readme:
            results.append((PASS, f"readme-stack-{layout}", f"{layout} listed in README"))
        else:
            results.append((FAIL, f"readme-stack-{layout}", f"{layout} missing from README Included Stacks"))

    # Check validate_templates.py expected detectors
    vt = read_text("scripts/validate_templates.py")
    for name in detector_names:
        escaped = f'"{name}"'
        if escaped in vt:
            results.append((PASS, f"validator-detector-{name}", f"detector {name} in validate_templates.py"))
        else:
            results.append((FAIL, f"validator-detector-{name}", f"detector {name} missing from validate_templates.py"))

    # Check validate_templates.py validate_layouts
    for layout in layout_dirs:
        escaped = f'"{layout}"'
        if escaped in vt:
            results.append((PASS, f"validator-layout-{layout}", f"layout {layout} in validate_templates.py"))
        else:
            results.append((FAIL, f"validator-layout-{layout}", f"layout {layout} missing from validate_templates.py"))

    # Check layout_for_stack coverage
    common = read_text("bootstrap/common.sh")
    for layout in layout_dirs:
        if layout in common:
            results.append((PASS, f"layout-for-stack-{layout}", f"{layout} in layout_for_stack()"))
        else:
            results.append((WARN, f"layout-for-stack-{layout}", f"{layout} not explicitly in layout_for_stack()"))

    return results


def check_docs_sync() -> list[tuple[str, str, str]]:
    results: list[tuple[str, str, str]] = []
    readme = read_text("README.md")

    # Check bin/ entries in README
    for script in sorted((ROOT / "bin").iterdir()):
        if script.name in readme:
            results.append((PASS, f"readme-bin-{script.name}", f"bin/{script.name} in README"))
        else:
            results.append((WARN, f"readme-bin-{script.name}", f"bin/{script.name} not in README tree"))

    # Check bootstrap/ scripts in README
    for script in sorted((ROOT / "bootstrap").glob("*.sh")):
        if script.name in readme:
            results.append((PASS, f"readme-bootstrap-{script.name}", f"bootstrap/{script.name} in README"))
        else:
            results.append((WARN, f"readme-bootstrap-{script.name}", f"bootstrap/{script.name} not in README tree"))

    return results


def check_smoke_coverage() -> list[tuple[str, str, str]]:
    results: list[tuple[str, str, str]] = []
    smoke = read_text("tests/smoke_test.sh")
    layout_dirs = sorted(
        d.name
        for d in (ROOT / "project_layouts").iterdir()
        if d.is_dir() and (d / "scaffold.sh").exists()
    )

    for layout in layout_dirs:
        if layout in smoke:
            results.append((PASS, f"smoke-{layout}", f"smoke test covers {layout}"))
        else:
            results.append((WARN, f"smoke-{layout}", f"smoke test may not cover {layout}"))

    return results


def main() -> None:
    all_results: list[tuple[str, str, str]] = []
    all_results.extend(check_version_consistency())
    all_results.extend(check_stack_alignment())
    all_results.extend(check_docs_sync())
    all_results.extend(check_smoke_coverage())

    version = read_text("VERSION").strip()
    fails = [r for r in all_results if r[0] == FAIL]
    warns = [r for r in all_results if r[0] == WARN]
    passes = [r for r in all_results if r[0] == PASS]

    print(f"## Roadmap Guardian Report  v{version}\n")
    print(f"checks={len(all_results)} pass={len(passes)} warn={len(warns)} fail={len(fails)}\n")

    if fails:
        print("### Failures")
        for status, check_id, message in fails:
            print(f"  FAIL  {check_id}: {message}")
        print()

    if warns:
        print("### Warnings")
        for status, check_id, message in warns:
            print(f"  WARN  {check_id}: {message}")
        print()

    if fails:
        print("guardian=fail")
        raise SystemExit(1)
    else:
        print("guardian=pass")


if __name__ == "__main__":
    main()
