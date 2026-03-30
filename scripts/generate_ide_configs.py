#!/usr/bin/env python3
"""Generate IDE configuration files for VS Code and JetBrains.

Creates .vscode/settings.json, .vscode/extensions.json,
and .idea/0dai.xml based on detected project stack.

Usage:
    python3 scripts/generate_ide_configs.py <target-dir>
"""
from __future__ import annotations

import json
import pathlib
import sys

STACK_EXTENSIONS: dict[str, list[str]] = {
    "python": ["ms-python.python", "ms-python.vscode-pylance", "charliermarsh.ruff"],
    "python-service": ["ms-python.python", "ms-python.vscode-pylance", "charliermarsh.ruff"],
    "fastapi": ["ms-python.python", "ms-python.vscode-pylance", "charliermarsh.ruff"],
    "data-ml": ["ms-python.python", "ms-toolsai.jupyter", "charliermarsh.ruff"],
    "node": ["dbaeumer.vscode-eslint", "esbenp.prettier-vscode"],
    "nextjs": ["dbaeumer.vscode-eslint", "esbenp.prettier-vscode", "bradlc.vscode-tailwindcss"],
    "react-native": ["dbaeumer.vscode-eslint", "esbenp.prettier-vscode", "msjsdiag.vscode-react-native"],
    "flutter": ["dart-code.dart-code", "dart-code.flutter"],
    "go-service": ["golang.go"],
    "fullstack-monorepo": ["dbaeumer.vscode-eslint", "esbenp.prettier-vscode", "ms-python.python"],
}

COMMON_EXTENSIONS = [
    "ms-azuretools.vscode-docker",
    "github.copilot",
    "eamodio.gitlens",
]

VSCODE_SETTINGS = {
    "editor.formatOnSave": True,
    "editor.rulers": [100],
    "files.trimTrailingWhitespace": True,
    "files.insertFinalNewline": True,
    "files.exclude": {
        "**/__pycache__": True,
        "**/node_modules": True,
        "**/.pytest_cache": True,
        "**/dist": True,
        "**/build": True,
        "**/.next": True,
    },
    "search.exclude": {
        "**/ai/experience/events": True,
        "**/ai/.backups": True,
    },
}


def detect_stack(target: pathlib.Path) -> str:
    discovery = target / "ai" / "manifest" / "discovery.json"
    if discovery.is_file():
        try:
            return json.loads(discovery.read_text(encoding="utf-8")).get("stack", "generic")
        except (json.JSONDecodeError, OSError):
            pass
    return "generic"


def generate_vscode(target: pathlib.Path, stack: str) -> None:
    vscode_dir = target / ".vscode"
    vscode_dir.mkdir(parents=True, exist_ok=True)

    # settings.json — merge with existing
    settings_path = vscode_dir / "settings.json"
    existing: dict = {}
    if settings_path.is_file():
        try:
            existing = json.loads(settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    merged = {**VSCODE_SETTINGS, **existing}
    settings_path.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"[0dai-repo] wrote .vscode/settings.json")

    # extensions.json — recommendations
    stack_exts = STACK_EXTENSIONS.get(stack, [])
    all_exts = sorted(set(stack_exts + COMMON_EXTENSIONS))

    ext_path = vscode_dir / "extensions.json"
    existing_recs: list[str] = []
    if ext_path.is_file():
        try:
            existing_recs = json.loads(ext_path.read_text(encoding="utf-8")).get("recommendations", [])
        except (json.JSONDecodeError, OSError):
            pass

    merged_recs = sorted(set(existing_recs + all_exts))
    ext_path.write_text(
        json.dumps({"recommendations": merged_recs}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[0dai-repo] wrote .vscode/extensions.json ({len(merged_recs)} recommendations)")


def generate_idea(target: pathlib.Path) -> None:
    idea_dir = target / ".idea"
    idea_dir.mkdir(parents=True, exist_ok=True)

    config_path = idea_dir / "0dai.xml"
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="RunManager">
    <configuration name="0dai validate" type="ShConfigurationType">
      <option name="SCRIPT_TEXT" value="bash -c './bin/0dai validate --target .'" />
      <option name="SCRIPT_WORKING_DIRECTORY" value="$PROJECT_DIR$" />
      <method v="2" />
    </configuration>
    <configuration name="0dai doctor" type="ShConfigurationType">
      <option name="SCRIPT_TEXT" value="bash -c './bin/0dai doctor --target .'" />
      <option name="SCRIPT_WORKING_DIRECTORY" value="$PROJECT_DIR$" />
      <method v="2" />
    </configuration>
    <configuration name="0dai sync" type="ShConfigurationType">
      <option name="SCRIPT_TEXT" value="bash -c './bin/0dai sync --target .'" />
      <option name="SCRIPT_WORKING_DIRECTORY" value="$PROJECT_DIR$" />
      <method v="2" />
    </configuration>
  </component>
</project>
"""
    config_path.write_text(xml, encoding="utf-8")
    print("[0dai-repo] wrote .idea/0dai.xml (run configurations)")


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: generate_ide_configs.py <target-dir>", file=sys.stderr)
        raise SystemExit(1)

    target = pathlib.Path(sys.argv[1])
    if not target.is_dir():
        print(f"target not found: {target}", file=sys.stderr)
        raise SystemExit(1)

    stack = detect_stack(target)
    generate_vscode(target, stack)
    generate_idea(target)
    print(f"[0dai-repo] IDE configs generated for stack: {stack}")


if __name__ == "__main__":
    main()
