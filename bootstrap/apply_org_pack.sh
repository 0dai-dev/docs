#!/usr/bin/env bash
set -euo pipefail

# Apply an org policy pack to a target project's ai/ layer.
# Usage: apply_org_pack.sh --target <path> [--pack <name>] [--dry-run]

. "$(cd "$(dirname "$0")" && pwd)/common.sh"

parse_kv_args "$@"
require_target

ORG_PACK_NAME="${ORG_PACK_NAME:-}"

apply_org_pack() {
  local target_dir="$1"
  local pack_name="${2:-}"

  python3 - "$REPO_ROOT" "$target_dir" "$pack_name" "$DRY_RUN" <<'PY'
import json
import pathlib
import sys

repo_root = pathlib.Path(sys.argv[1])
target_dir = pathlib.Path(sys.argv[2])
pack_name = sys.argv[3]
dry_run = sys.argv[4] == "1"

org_packs_root = repo_root / "templates" / "layer" / "ai" / "packs" / "org"
target_packs_dir = target_dir / "ai" / "packs" / "org"


def find_pack(name: str) -> pathlib.Path | None:
    if name:
        pack_dir = org_packs_root / name
        if pack_dir.is_dir():
            versions = sorted(pack_dir.iterdir(), reverse=True)
            for v in versions:
                pack_file = v / "pack.yaml"
                if pack_file.is_file():
                    return pack_file
    return None


def find_all_packs() -> list[pathlib.Path]:
    packs = []
    if not org_packs_root.is_dir():
        return packs
    for org_dir in sorted(org_packs_root.iterdir()):
        if not org_dir.is_dir():
            continue
        versions = sorted(org_dir.iterdir(), reverse=True)
        for v in versions:
            pack_file = v / "pack.yaml"
            if pack_file.is_file():
                packs.append(pack_file)
                break
    return packs


def parse_yaml_simple(text: str) -> dict:
    """Minimal YAML-like parser for flat and one-level nested keys."""
    result: dict = {}
    current_key = None
    current_list: list | None = None
    current_dict: dict | None = None

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip())

        if indent == 0 and ":" in stripped:
            if current_key and current_list is not None:
                result[current_key] = current_list
            elif current_key and current_dict is not None:
                result[current_key] = current_dict
            current_list = None
            current_dict = None

            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if value:
                if value in ("true", "false"):
                    result[key] = value == "true"
                else:
                    try:
                        result[key] = int(value)
                    except ValueError:
                        result[key] = value
                current_key = None
            else:
                current_key = key
            continue

        if current_key and stripped.startswith("- "):
            if current_list is None:
                current_list = []
            current_list.append(stripped[2:].strip().strip('"').strip("'"))
            continue

        if current_key and ":" in stripped and indent > 0:
            if current_dict is None:
                current_dict = {}
            k, _, v = stripped.partition(":")
            v = v.strip()
            if v in ("true", "false"):
                v = v == "true"
            else:
                try:
                    v = int(v)
                except ValueError:
                    pass
            current_dict[k.strip()] = v
            continue

    if current_key and current_list is not None:
        result[current_key] = current_list
    elif current_key and current_dict is not None:
        result[current_key] = current_dict

    return result


def install_pack(pack_file: pathlib.Path) -> None:
    text = pack_file.read_text(encoding="utf-8")
    data = parse_yaml_simple(text)
    name = data.get("name", "unknown")
    version = data.get("version", "0.0.0")

    dest_dir = target_packs_dir / pathlib.Path(name).name / str(version)

    if dry_run:
        print(f"[0dai-repo] dry-run: install org pack {name} v{version} to {dest_dir}")
        return

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / "pack.yaml"
    dest_file.write_text(text, encoding="utf-8")
    print(f"[0dai-repo] installed org pack {name} v{version}")

    # Write org policy manifest for agents to read
    manifest_dir = target_dir / "ai" / "manifest"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    org_manifest = manifest_dir / "org-policy.json"

    existing = {}
    if org_manifest.is_file():
        try:
            existing = json.loads(org_manifest.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    packs_applied = existing.get("packs_applied", [])
    entry = {"name": name, "version": str(version)}
    if entry not in packs_applied:
        packs_applied.append(entry)

    manifest = {
        "managed": True,
        "packs_applied": packs_applied,
        "permissions": data.get("permissions", {}),
        "mcp": data.get("mcp", {}),
        "hooks": data.get("hooks", {}),
        "constraints": data.get("constraints", {}),
    }
    org_manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"[0dai-repo] wrote org policy manifest to ai/manifest/org-policy.json")


if pack_name:
    pack_file = find_pack(pack_name)
    if pack_file is None:
        print(f"[0dai-repo] org pack not found: {pack_name}")
        sys.exit(1)
    install_pack(pack_file)
else:
    packs = find_all_packs()
    if not packs:
        print("[0dai-repo] no org packs found; skipping")
    for pf in packs:
        install_pack(pf)
PY
}

apply_org_pack "$TARGET_DIR" "$ORG_PACK_NAME"
