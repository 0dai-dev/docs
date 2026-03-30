#!/usr/bin/env python3
"""0dai Stack Compatibility Tester — verify init-new for all stacks.

Scaffolds each project layout in a temp directory and validates that
expected structure matches structure.md documentation.

Usage:
    python3 scripts/test_stack_compat.py                # test all stacks
    python3 scripts/test_stack_compat.py --stack fastapi # test one stack
    python3 scripts/test_stack_compat.py --json          # JSON output
    0dai stack-test [--stack <name>] [--json]
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
LAYOUTS_DIR = ROOT / "project_layouts"

# Common AI layer files that must exist after init-new
REQUIRED_AI_FILES = [
    "ai/VERSION",
    "ai/manifest/project.yaml",
    "ai/manifest/commands.yaml",
    "ai/manifest/discovery.json",
    "ai/manifest/applied-lock.json",
]

REQUIRED_NATIVE_FILES = [
    ".claude/settings.json",
    ".claude/CLAUDE.md",
    "AGENTS.md",
]


def _run(cmd: list[str], cwd: str) -> tuple[int, str]:
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=cwd,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def _parse_structure_paths(structure_md: str) -> list[str]:
    """Extract directory/file paths from structure.md code block with nesting."""
    paths = []
    in_block = False
    indent_stack: list[tuple[int, str]] = []  # (indent_level, path_segment)

    for line in structure_md.splitlines():
        if line.strip().startswith("```"):
            in_block = not in_block
            indent_stack = []
            continue
        if not in_block:
            continue

        stripped = line.rstrip().rstrip("/")
        if not stripped.strip() or stripped.strip() == "repo" or stripped.strip().startswith("#"):
            continue

        # Calculate indent level
        indent = len(stripped) - len(stripped.lstrip())
        segment = stripped.strip().rstrip("/")

        # Skip ai/ — tested separately
        if segment == "ai":
            indent_stack = [(indent, segment)]
            continue

        # Pop stack back to parent level
        while indent_stack and indent_stack[-1][0] >= indent:
            indent_stack.pop()

        # Skip children of ai/
        if indent_stack and indent_stack[0][1] == "ai":
            continue

        indent_stack.append((indent, segment))

        # Build full path from stack
        full_path = "/".join(s for _, s in indent_stack)
        if full_path and full_path != "repo":
            paths.append(full_path)

    return paths


def test_stack(stack: str) -> dict:
    """Test a single stack: scaffold + validate."""
    result: dict = {
        "stack": stack,
        "status": "pass",
        "checks": [],
        "errors": [],
    }

    layout_dir = LAYOUTS_DIR / stack
    if not layout_dir.is_dir():
        result["status"] = "fail"
        result["errors"].append(f"Layout directory not found: {layout_dir}")
        return result

    # Check scaffold.sh exists
    scaffold = layout_dir / "scaffold.sh"
    if not scaffold.is_file():
        result["status"] = "fail"
        result["errors"].append(f"Missing scaffold.sh")
        return result
    result["checks"].append("scaffold.sh exists")

    # Check structure.md exists
    structure_md = layout_dir / "structure.md"
    if structure_md.is_file():
        result["checks"].append("structure.md exists")
        expected_paths = _parse_structure_paths(structure_md.read_text(encoding="utf-8"))
    else:
        result["checks"].append("structure.md missing (warn)")
        expected_paths = []

    # Run init-new in temp directory
    tmpdir = tempfile.mkdtemp(prefix=f"0dai-compat-{stack}-")
    try:
        target = pathlib.Path(tmpdir) / "project"
        code, output = _run(
            [str(ROOT / "bin" / "0dai"), "init-new", "--stack", stack, "--target", str(target)],
            cwd=str(ROOT),
        )

        if code != 0:
            result["status"] = "fail"
            result["errors"].append(f"init-new failed (exit {code}): {output[:300]}")
            return result
        result["checks"].append("init-new succeeded")

        # Verify AI layer
        for rel in REQUIRED_AI_FILES:
            if (target / rel).exists():
                result["checks"].append(f"{rel} exists")
            else:
                result["status"] = "fail"
                result["errors"].append(f"Missing AI file: {rel}")

        # Verify native configs
        for rel in REQUIRED_NATIVE_FILES:
            if (target / rel).exists():
                result["checks"].append(f"{rel} exists")
            else:
                result["status"] = "fail"
                result["errors"].append(f"Missing native config: {rel}")

        # Verify structure.md paths
        for expected in expected_paths:
            full = target / expected
            if full.exists():
                result["checks"].append(f"{expected} exists")
            elif full.with_suffix("").exists() or any(target.glob(f"{expected}*")):
                result["checks"].append(f"{expected} exists (fuzzy)")
            else:
                # Some paths are optional (e.g., specific files vs dirs)
                result["errors"].append(f"Expected path missing: {expected}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    # If we have structure errors but no AI/native errors, downgrade to warn
    if result["status"] == "pass" and result["errors"]:
        result["status"] = "warn"

    return result


def main() -> None:
    target_stack = ""
    show_json = "--json" in sys.argv

    for i, arg in enumerate(sys.argv):
        if arg == "--stack" and i + 1 < len(sys.argv):
            target_stack = sys.argv[i + 1]

    stacks = [target_stack] if target_stack else sorted(
        d.name for d in LAYOUTS_DIR.iterdir() if d.is_dir()
    )

    results = []
    for stack in stacks:
        if not show_json:
            print(f"Testing {stack}...", end=" ", flush=True)
        r = test_stack(stack)
        results.append(r)
        if not show_json:
            print(f"{r['status'].upper()} ({len(r['checks'])} checks, {len(r['errors'])} issues)")

    if show_json:
        output = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stacks_tested": len(results),
            "passed": sum(1 for r in results if r["status"] == "pass"),
            "warned": sum(1 for r in results if r["status"] == "warn"),
            "failed": sum(1 for r in results if r["status"] == "fail"),
            "results": results,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        passed = sum(1 for r in results if r["status"] == "pass")
        warned = sum(1 for r in results if r["status"] == "warn")
        failed = sum(1 for r in results if r["status"] == "fail")
        print(f"\n{len(results)} stacks tested: {passed} pass, {warned} warn, {failed} fail")

        if failed:
            print("\nFailures:")
            for r in results:
                if r["status"] == "fail":
                    print(f"  {r['stack']}: {'; '.join(r['errors'][:3])}")

    has_fail = any(r["status"] == "fail" for r in results)
    sys.exit(1 if has_fail else 0)


if __name__ == "__main__":
    main()
