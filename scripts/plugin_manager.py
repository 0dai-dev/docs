#!/usr/bin/env python3
"""0dai Plugin System — extend 0dai with custom commands, checks, and generators.

Plugins live in ai/plugins/<name>/ with a plugin.json manifest.
Each plugin can provide: commands, checks, generators, hooks.

Usage:
    0dai plugin --target <path> list                        # list installed plugins
    0dai plugin --target <path> run <name> [args]           # run a plugin command
    0dai plugin --target <path> init <name>                 # scaffold new plugin
    0dai plugin --target <path> validate                    # validate all plugins
    0dai plugin --target <path> --json                      # JSON output
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time


PLUGIN_SCHEMA = {
    "name": "my-plugin",
    "version": "0.1.0",
    "description": "What this plugin does",
    "author": "",
    "type": "command",
    "entry": "run.sh",
    "triggers": [],
    "permissions": ["safe"],
}


def _plugins_dir(target: pathlib.Path) -> pathlib.Path:
    return target / "ai" / "plugins"


def _load_plugin(plugin_dir: pathlib.Path) -> dict | None:
    manifest = plugin_dir / "plugin.json"
    if not manifest.is_file():
        return None
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["_path"] = str(plugin_dir)
        data["_dir"] = plugin_dir.name
        return data
    except (json.JSONDecodeError, OSError):
        return None


def list_plugins(target: pathlib.Path) -> list[dict]:
    pdir = _plugins_dir(target)
    if not pdir.is_dir():
        return []
    plugins = []
    for d in sorted(pdir.iterdir()):
        if d.is_dir():
            p = _load_plugin(d)
            if p:
                plugins.append(p)
    return plugins


def cmd_list(target: pathlib.Path) -> None:
    plugins = list_plugins(target)
    if not plugins:
        print("[0dai] no plugins installed")
        print("  Create one: 0dai plugin --target . init my-plugin")
        return
    print(f"{'Name':<20} {'Version':<10} {'Type':<12} Description")
    print("-" * 70)
    for p in plugins:
        print(f"{p.get('name','?'):<20} {p.get('version','?'):<10} {p.get('type','?'):<12} {p.get('description','')[:30]}")
    print(f"\n{len(plugins)} plugin(s)")


def cmd_init(target: pathlib.Path, name: str) -> None:
    pdir = _plugins_dir(target) / name
    if pdir.exists():
        print(f"[0dai] plugin '{name}' already exists")
        return

    pdir.mkdir(parents=True, exist_ok=True)

    manifest = {**PLUGIN_SCHEMA, "name": name, "description": f"{name} plugin"}
    (pdir / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    (pdir / "run.sh").write_text(f"""#!/usr/bin/env bash
# {name} plugin for 0dai
# Type: command
# Run with: 0dai plugin --target . run {name}

set -euo pipefail
TARGET_DIR="${{1:-.}}"

echo "[{name}] running on $TARGET_DIR"
echo "[{name}] implement your logic here"
""", encoding="utf-8")
    os.chmod(pdir / "run.sh", 0o755)

    (pdir / "README.md").write_text(f"""# {name}

0dai plugin.

## Usage

```bash
0dai plugin --target . run {name}
```

## Configuration

Edit `plugin.json` to customize:
- `type`: command, check, generator, hook
- `entry`: script to execute (sh, py)
- `triggers`: events that auto-run this plugin (init, sync, pre-deploy)
- `permissions`: command tiers allowed (safe, workspace, ops)
""", encoding="utf-8")

    print(f"[0dai] plugin '{name}' created at ai/plugins/{name}/")
    print(f"  Manifest: plugin.json")
    print(f"  Entry: run.sh")
    print(f"  Edit run.sh to add your logic")


def cmd_run(target: pathlib.Path, name: str, extra_args: list[str]) -> None:
    pdir = _plugins_dir(target) / name
    plugin = _load_plugin(pdir)
    if not plugin:
        print(f"[0dai] plugin '{name}' not found")
        sys.exit(1)

    entry = pdir / plugin.get("entry", "run.sh")
    if not entry.is_file():
        print(f"[0dai] entry point not found: {entry}")
        sys.exit(1)

    # Determine interpreter
    entry_str = str(entry)
    if entry_str.endswith(".py"):
        cmd = ["python3", entry_str, str(target)] + extra_args
    elif entry_str.endswith(".sh"):
        cmd = ["bash", entry_str, str(target)] + extra_args
    else:
        cmd = [entry_str, str(target)] + extra_args

    try:
        result = subprocess.run(cmd, cwd=str(target), timeout=120)
        sys.exit(result.returncode)
    except subprocess.TimeoutExpired:
        print(f"[0dai] plugin '{name}' timed out (120s)")
        sys.exit(1)


def cmd_validate(target: pathlib.Path) -> None:
    plugins = list_plugins(target)
    if not plugins:
        print("[0dai] no plugins to validate")
        return

    errors = 0
    for p in plugins:
        name = p.get("name", "?")
        issues = []
        if not p.get("name"):
            issues.append("missing name")
        if not p.get("version"):
            issues.append("missing version")
        if not p.get("entry"):
            issues.append("missing entry")
        entry_path = pathlib.Path(p["_path"]) / p.get("entry", "")
        if not entry_path.is_file():
            issues.append(f"entry not found: {p.get('entry')}")

        if issues:
            print(f"  FAIL {name}: {', '.join(issues)}")
            errors += 1
        else:
            print(f"  OK   {name}")

    print(f"\n{len(plugins)} plugin(s), {errors} error(s)")
    if errors:
        sys.exit(1)


def cmd_json(target: pathlib.Path) -> None:
    plugins = list_plugins(target)
    # Remove internal paths
    for p in plugins:
        p.pop("_path", None)
        p.pop("_dir", None)
    print(json.dumps({"plugins": plugins, "count": len(plugins)}, indent=2, ensure_ascii=False))


def main() -> None:
    target = pathlib.Path(".")
    subcmd = "list"
    subcmd_args: list[str] = []
    json_mode = False
    args = sys.argv[1:]

    i = 0
    while i < len(args):
        if args[i] == "--target" and i + 1 < len(args):
            target = pathlib.Path(args[i + 1]).resolve()
            i += 2
        elif args[i] == "--json":
            json_mode = True
            i += 1
        elif args[i] in ("list", "init", "run", "validate"):
            subcmd = args[i]
            i += 1
        elif not args[i].startswith("-"):
            subcmd_args.append(args[i])
            i += 1
        else:
            i += 1

    if json_mode:
        cmd_json(target)
    elif subcmd == "init":
        if not subcmd_args:
            print("Usage: 0dai plugin --target <path> init <name>", file=sys.stderr)
            sys.exit(1)
        cmd_init(target, subcmd_args[0])
    elif subcmd == "run":
        if not subcmd_args:
            print("Usage: 0dai plugin --target <path> run <name>", file=sys.stderr)
            sys.exit(1)
        cmd_run(target, subcmd_args[0], subcmd_args[1:])
    elif subcmd == "validate":
        cmd_validate(target)
    else:
        cmd_list(target)


if __name__ == "__main__":
    main()
