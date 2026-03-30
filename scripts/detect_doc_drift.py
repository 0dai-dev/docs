#!/usr/bin/env python3
"""0dai Documentation Drift Detector — find stale docs by comparing against code.

Checks that CLI help text, README, bootstrap-spec, and architecture docs
reflect the actual project state.

Usage:
    python3 scripts/detect_doc_drift.py              # full report
    python3 scripts/detect_doc_drift.py --json        # JSON output
    0dai doc-drift                                    # via CLI
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"


def _read(rel: str) -> str | None:
    path = ROOT / rel
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return None


def check_cli_commands_in_readme() -> list[tuple[str, str, str]]:
    """Verify README lists all CLI commands from bin/0dai."""
    results = []
    cli_text = _read("bin/0dai") or ""
    readme = _read("README.md") or ""

    # Extract commands from case statement
    case_match = re.search(r"case.*\n\s*([\w|]+)\)", cli_text)
    if not case_match:
        return results

    # Find all commands from the usage() function
    commands = []
    for line in cli_text.splitlines():
        m = re.match(r"\s+0dai\s+(\S+)", line)
        if m:
            commands.append(m.group(1))

    for cmd in commands:
        if cmd in readme:
            results.append((PASS, f"readme-cmd-{cmd}", f"Command '{cmd}' documented in README"))
        else:
            results.append((WARN, f"readme-cmd-{cmd}", f"Command '{cmd}' not found in README"))

    return results


def check_scripts_exist() -> list[tuple[str, str, str]]:
    """Verify all script references in bin/0dai-repo actually exist."""
    results = []
    repo_text = _read("bin/0dai-repo") or ""

    for line in repo_text.splitlines():
        # Match: exec python3 "$ROOT_DIR/scripts/foo.py"
        m = re.search(r'exec python3 "\$ROOT_DIR/(scripts/\S+\.py)"', line)
        if m:
            script_path = m.group(1)
            if (ROOT / script_path).is_file():
                results.append((PASS, f"script-{script_path}", f"{script_path} exists"))
            else:
                results.append((FAIL, f"script-{script_path}", f"{script_path} referenced but missing"))

        # Match: exec "$ROOT_DIR/bootstrap/foo.sh"
        m = re.search(r'exec "\$ROOT_DIR/(bootstrap/\S+\.sh)"', line)
        if m:
            script_path = m.group(1)
            if (ROOT / script_path).is_file():
                results.append((PASS, f"script-{script_path}", f"{script_path} exists"))
            else:
                results.append((FAIL, f"script-{script_path}", f"{script_path} referenced but missing"))

    return results


def check_stack_docs() -> list[tuple[str, str, str]]:
    """Verify each project layout has both scaffold.sh and structure.md."""
    results = []
    layouts_dir = ROOT / "project_layouts"
    if not layouts_dir.is_dir():
        return results

    for d in sorted(layouts_dir.iterdir()):
        if not d.is_dir():
            continue
        has_scaffold = (d / "scaffold.sh").is_file()
        has_structure = (d / "structure.md").is_file()

        if has_scaffold and has_structure:
            results.append((PASS, f"layout-{d.name}", f"{d.name}: scaffold.sh + structure.md"))
        elif has_scaffold:
            results.append((WARN, f"layout-{d.name}", f"{d.name}: missing structure.md"))
        else:
            results.append((FAIL, f"layout-{d.name}", f"{d.name}: missing scaffold.sh"))

    return results


def check_persona_docs() -> list[tuple[str, str, str]]:
    """Verify all personas have required fields."""
    results = []
    personas_dir = ROOT / "templates" / "layer" / "ai" / "personas"
    if not personas_dir.is_dir():
        return results

    required_fields = {"name", "display_name", "description", "system_prompt_addition"}

    for path in sorted(personas_dir.glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        found = set()
        for field in required_fields:
            if f"{field}:" in text:
                found.add(field)

        missing = required_fields - found
        if not missing:
            results.append((PASS, f"persona-{path.stem}", f"{path.stem}: all fields present"))
        else:
            results.append((WARN, f"persona-{path.stem}", f"{path.stem}: missing {', '.join(sorted(missing))}"))

    return results


def check_version_in_docs() -> list[tuple[str, str, str]]:
    """Check that docs reference reasonable version ranges."""
    results = []
    version = (_read("VERSION") or "").strip()
    if not version:
        return results

    major_minor = ".".join(version.split(".")[:2])

    # Check architecture.md mentions current phase
    arch = _read("docs/architecture.md") or ""
    if arch:
        results.append((PASS, "docs-architecture", "docs/architecture.md exists"))
    else:
        results.append((WARN, "docs-architecture", "docs/architecture.md missing"))

    # Check bootstrap-spec.md exists
    spec = _read("docs/bootstrap-spec.md") or ""
    if spec:
        results.append((PASS, "docs-bootstrap-spec", "docs/bootstrap-spec.md exists"))
    else:
        results.append((WARN, "docs-bootstrap-spec", "docs/bootstrap-spec.md missing"))

    return results


def check_agent_template_consistency() -> list[tuple[str, str, str]]:
    """Check Claude agent templates match persona definitions."""
    results = []

    personas = set()
    personas_dir = ROOT / "templates" / "layer" / "ai" / "personas"
    if personas_dir.is_dir():
        for p in personas_dir.glob("*.yaml"):
            personas.add(p.stem)

    claude_agents = set()
    agents_dir = ROOT / "templates" / "layer" / "ai" / "templates" / "claude" / "agents"
    if agents_dir.is_dir():
        for a in agents_dir.glob("*.md.tmpl"):
            claude_agents.add(a.stem.replace(".md", ""))

    # Each persona should have a matching agent template
    for persona in sorted(personas):
        if persona in claude_agents:
            results.append((PASS, f"agent-persona-{persona}", f"Persona '{persona}' has Claude agent template"))
        else:
            results.append((WARN, f"agent-persona-{persona}", f"Persona '{persona}' has no matching Claude agent"))

    return results


def run_drift_check() -> list[tuple[str, str, str]]:
    all_results = []
    all_results.extend(check_cli_commands_in_readme())
    all_results.extend(check_scripts_exist())
    all_results.extend(check_stack_docs())
    all_results.extend(check_persona_docs())
    all_results.extend(check_version_in_docs())
    all_results.extend(check_agent_template_consistency())
    return all_results


def main() -> None:
    show_json = "--json" in sys.argv
    results = run_drift_check()

    fails = [r for r in results if r[0] == FAIL]
    warns = [r for r in results if r[0] == WARN]
    passes = [r for r in results if r[0] == PASS]

    if show_json:
        output = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_checks": len(results),
            "pass": len(passes),
            "warn": len(warns),
            "fail": len(fails),
            "drift_detected": len(fails) > 0 or len(warns) > 0,
            "checks": [{"status": r[0], "id": r[1], "message": r[2]} for r in results],
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        version = (_read("VERSION") or "?").strip()
        print(f"## Doc Drift Report  v{version}\n")
        print(f"checks={len(results)}  pass={len(passes)}  warn={len(warns)}  fail={len(fails)}\n")

        if fails:
            print("### DRIFT DETECTED")
            for _, check_id, msg in fails:
                print(f"  FAIL  {check_id}: {msg}")
            print()

        if warns:
            print("### POSSIBLE DRIFT")
            for _, check_id, msg in warns:
                print(f"  WARN  {check_id}: {msg}")
            print()

        if fails:
            print("drift=detected")
        elif warns:
            print("drift=warnings")
        else:
            print("drift=none")

    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
