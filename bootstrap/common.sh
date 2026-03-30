#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LAYER_TEMPLATE_DIR="$REPO_ROOT/templates/layer/ai"
CANONICAL_TEMPLATE_DIR="$REPO_ROOT/templates/layer/ai/templates"
NATIVE_OUTPUT_MAP_FILE="$REPO_ROOT/bootstrap/native_output_map.json"
CURRENT_AI_VERSION="1.0.0"

TARGET_DIR="${TARGET_DIR:-}"
STACK_NAME="${STACK_NAME:-}"
AGENTS_CSV="${AGENTS_CSV:-}"
DRY_RUN="${DRY_RUN:-0}"
REPORT_FORMAT="${REPORT_FORMAT:-text}"
NO_GIT="${NO_GIT:-0}"
LAYOUT_ONLY="${LAYOUT_ONLY:-0}"
SKIP_ROOT_CONFIGS="${SKIP_ROOT_CONFIGS:-0}"
SKIP_CI="${SKIP_CI:-0}"
ORG_PACK_NAME="${ORG_PACK_NAME:-}"
VERBOSE="${VERBOSE:-0}"
MANAGED_BEGIN="<!-- zerodayai:managed:begin -->"
MANAGED_END="<!-- zerodayai:managed:end -->"

log() {
  printf '[0dai-repo] %s\n' "$*"
}

debug() {
  if [ "$VERBOSE" = "1" ]; then
    printf '[0dai-repo:debug] %s\n' "$*"
  fi
}

fail() {
  printf '[0dai-repo] error: %s\n' "$*" >&2
  exit 1
}

native_map_path() {
  local key="$1"
  python3 - "$NATIVE_OUTPUT_MAP_FILE" "$REPO_ROOT" "$key" <<'PY'
import json
import pathlib
import sys

mapping = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
root = pathlib.Path(sys.argv[2])
key = sys.argv[3]
print(root / mapping[key])
PY
}

run_or_echo() {
  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run: $*"
  else
    "$@"
  fi
}

default_agents_for_stack() {
  printf 'codex,claude,opencode,gemini,aider\n'
}

parse_kv_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --target|--repo-root)
        TARGET_DIR="$2"
        shift 2
        ;;
      --stack)
        STACK_NAME="$2"
        shift 2
        ;;
      --agents|--tools)
        AGENTS_CSV="$2"
        shift 2
        ;;
      --dry-run)
        DRY_RUN="1"
        shift
        ;;
      --report)
        REPORT_FORMAT="$2"
        shift 2
        ;;
      --no-git)
        NO_GIT="1"
        shift
        ;;
      --layout-only)
        LAYOUT_ONLY="1"
        shift
        ;;
      --skip-root-configs)
        SKIP_ROOT_CONFIGS="1"
        shift
        ;;
      --skip-ci)
        SKIP_CI="1"
        shift
        ;;
      --pack)
        ORG_PACK_NAME="$2"
        shift 2
        ;;
      --verbose|-v)
        VERBOSE="1"
        shift
        ;;
      --write)
        shift
        ;;
      --backup|--with-hooks|--with-agents|--with-skills|--with-opencode|--with-claude|--with-codex|--with-mcp)
        shift
        ;;
      *)
        fail "unknown argument: $1"
        ;;
    esac
  done
}

require_target() {
  if [ -z "$TARGET_DIR" ]; then
    fail "missing --target <path>"
  fi
  if [ ! -d "$TARGET_DIR" ]; then
    fail "target directory does not exist: $TARGET_DIR"
  fi
}

ensure_target_parent() {
  if [ -z "$TARGET_DIR" ]; then
    fail "missing --target <path>"
  fi
  mkdir -p "$TARGET_DIR"
}

detect_available_clis() {
  local clis=""
  command -v codex >/dev/null 2>&1 && clis="${clis},codex"
  command -v claude >/dev/null 2>&1 && clis="${clis},claude"
  command -v opencode >/dev/null 2>&1 && clis="${clis},opencode"
  command -v gemini >/dev/null 2>&1 && clis="${clis},gemini"
  command -v aider >/dev/null 2>&1 && clis="${clis},aider"
  clis="${clis#,}"
  [ -n "$clis" ] || clis="none"
  printf '%s\n' "$clis"
}

detect_native_configs() {
  local target_dir="$1"
  python3 - "$target_dir" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
probes = [
    ".codex/config.toml",
    ".claude/settings.json",
    ".claude/CLAUDE.md",
    "opencode.json",
    ".opencode/agents",
    ".gemini/settings.json",
    ".gemini/agents",
    ".aider.conf.yml",
    ".aider/agents",
    "AGENTS.md",
]
present = [probe for probe in probes if (root / probe).exists()]
print(",".join(present) if present else "none")
PY
}

detect_environment_json() {
  local target_dir="$1"
  python3 - "$target_dir" <<'PY'
import json
import os
import pathlib
import platform
import shutil
import socket
import sys

root = pathlib.Path(sys.argv[1])
cwd = pathlib.Path.cwd()


def has_command(name: str) -> bool:
    return shutil.which(name) is not None


def env_flag(name: str) -> bool:
    value = os.environ.get(name, "")
    return value not in ("", "0", "false", "False", "no", "NO")


def in_container() -> bool:
    return pathlib.Path("/.dockerenv").exists() or env_flag("container")


def in_ci() -> bool:
    return any(env_flag(name) for name in ["CI", "GITHUB_ACTIONS", "BUILDKITE", "CIRCLECI", "GITLAB_CI"])


def in_cloud_cli() -> bool:
    names = [
        "CODESPACES",
        "GITPOD_WORKSPACE_ID",
        "REMOTE_CONTAINERS",
        "DEVCONTAINER",
        "OPENVSCODE_SERVER_ROOT",
    ]
    return any(env_flag(name) for name in names)


def looks_like_vps() -> bool:
    host = socket.gethostname().lower()
    ssh = env_flag("SSH_CONNECTION") or env_flag("SSH_TTY")
    return ssh or host.startswith(("ip-", "vps", "srv", "vm-"))


def detect_kind() -> str:
    if in_ci():
        return "ci"
    if in_cloud_cli():
        return "cloud-cli"
    if in_container():
        return "container"
    if looks_like_vps():
        return "vps"
    return "local"


def detect_execution(kind: str) -> str:
    if kind in {"ci", "cloud-cli", "container"}:
        return "headless"
    return "interactive"


def writable(path: pathlib.Path) -> bool:
    try:
        probe = path / ".0dai-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


kind = detect_kind()
payload = {
    "kind": kind,
    "execution": detect_execution(kind),
    "os": platform.system(),
    "workspace": {
        "target": str(root),
        "cwd": str(cwd),
        "writable": writable(root),
    },
    "available_clis": [name for name in ["codex", "claude", "opencode"] if has_command(name)],
    "capabilities": {
        "docker": has_command("docker") and (pathlib.Path("/var/run/docker.sock").exists() or env_flag("DOCKER_HOST")),
        "systemd": has_command("systemctl") and pathlib.Path("/run/systemd/system").exists(),
        "network": True,
        "sudo": has_command("sudo"),
        "long_running": kind not in {"ci", "cloud-cli"},
        "gui": any(env_flag(name) for name in ["DISPLAY", "WAYLAND_DISPLAY"]),
    },
    "constraints": {
        "ephemeral": kind in {"ci", "cloud-cli", "container"},
        "limited_fs": kind in {"cloud-cli", "ci"},
        "no_background_processes": kind in {"ci", "cloud-cli"},
        "remote_access": kind in {"vps", "cloud-cli", "ci"} or env_flag("SSH_CONNECTION"),
    },
}

print(json.dumps(payload))
PY
}

detect_commands_json() {
  local target_dir="$1"
  python3 - "$target_dir" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
commands = {"install": "", "build": "", "test": "", "lint": "", "format": ""}
package_manager = "unknown"


def has_any(patterns):
    return any(any(root.glob(pattern)) for pattern in patterns)


def visible_paths(patterns):
    matches = []
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            rel = path.relative_to(root).as_posix()
            if rel.startswith(("ai/", ".git/", "dashboard/venv/")):
                continue
            if rel not in matches:
                matches.append(rel)
    return matches


def join_parts(parts):
    parts = [part for part in parts if part]
    return " && ".join(parts)


def portable_python_entrypoint() -> str:
    if (root / "dashboard" / "app.py").exists():
        return "bash -lc 'cd dashboard && if [ -f venv/bin/activate ]; then . venv/bin/activate; fi; python3 app.py'"
    if (root / "app.py").exists():
        return "python3 app.py"
    return ""


def read_text_if_exists(path: pathlib.Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


def cloud_safe_command(command: str) -> str:
    return (
        command.replace("/home/admin/dashboard", "dashboard")
        .replace("/root/proxy-farm", ".")
        .replace("/home/admin/docker", "docker")
    )

if (root / "package.json").exists():
    package_manager = "npm"
    if (root / "pnpm-workspace.yaml").exists() or (root / "pnpm-lock.yaml").exists():
        package_manager = "pnpm"
    elif (root / "yarn.lock").exists():
        package_manager = "yarn"
    commands.update(
        {
            "install": f"{package_manager} install",
            "build": f"{package_manager} run build",
            "test": f"{package_manager} test",
            "lint": f"{package_manager} run lint",
            "format": f"{package_manager} run format",
        }
    )
elif (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
    package_manager = "pip"
    commands.update(
        {
            "install": "python -m pip install -r requirements.txt",
            "test": "python -m pytest",
            "lint": "python -m ruff check .",
            "format": "python -m ruff format .",
        }
    )
elif (root / "pubspec.yaml").exists():
    package_manager = "flutter"
    commands.update(
        {
            "install": "flutter pub get",
            "test": "flutter test",
            "lint": "flutter analyze",
            "format": "dart format .",
        }
    )
else:
    go_files = visible_paths(["*.go", "**/*.go"])
    python_files = visible_paths(["*.py", "**/*.py"])
    shell_scripts = visible_paths(["*.sh", "**/*.sh"])
    dockerfiles = visible_paths(["Dockerfile", "**/Dockerfile"])
    readme_text = "\n".join(
        filter(
            None,
            [
                read_text_if_exists(root / "README.md"),
                read_text_if_exists(root / "README-APP.md"),
                read_text_if_exists(root / "START-HERE.md"),
                read_text_if_exists(root / "potato.sh"),
                read_text_if_exists(root / "services.sh"),
            ],
        )
    )

    install_parts = []
    build_parts = []
    test_parts = []
    lint_parts = []
    format_parts = []

    if (root / "go.mod").exists() or go_files:
        package_manager = "multi"
        install_parts.append("go mod download")
        build_parts.append("go build ./...")
        test_parts.append("go test ./...")
        if go_files:
            quoted_go_files = " ".join(json.dumps(path) for path in go_files)
            format_parts.append(f"gofmt -w {quoted_go_files}")

    if python_files:
        package_manager = "multi" if package_manager != "unknown" else "python-cli"
        python_targets = []
        if (root / "dashboard").exists():
            python_targets.append("dashboard")
            install_parts.append("python3 -m venv dashboard/venv")
        for candidate in ["monitor.py", "health_monitor.py", "docker/browser-launcher.py"]:
            if (root / candidate).exists():
                python_targets.append(candidate)
        if not python_targets:
            python_targets = python_files
        quoted_targets = " ".join(json.dumps(path) for path in python_targets)
        compile_cmd = f"python3 -m compileall {quoted_targets}" if quoted_targets else ""
        if compile_cmd:
            test_parts.append(compile_cmd)
            lint_parts.append(compile_cmd)

    if dockerfiles:
        package_manager = "multi" if package_manager != "unknown" else "docker"
        for dockerfile in dockerfiles:
            docker_dir = pathlib.Path(dockerfile).parent.as_posix()
            if docker_dir == ".":
                build_parts.append("docker build .")
            else:
                build_parts.append(f"docker build {json.dumps(docker_dir)}")

    entrypoint = portable_python_entrypoint()
    if entrypoint and not build_parts:
        build_parts.append(entrypoint)

    if "docker build -t potato-browser:latest ." in readme_text or 'docker build -t potato-browser:latest .' in readme_text:
        build_parts.append("docker build -t potato-browser:latest ./docker")

    if "python3 container_manager.py health" in readme_text or "health" in readme_text:
        test_parts.append("python3 dashboard/container_manager.py health")

    if readme_text:
        install_parts = [cloud_safe_command(part) for part in install_parts]
        build_parts = [cloud_safe_command(part) for part in build_parts]
        test_parts = [cloud_safe_command(part) for part in test_parts]
        lint_parts = [cloud_safe_command(part) for part in lint_parts]
        format_parts = [cloud_safe_command(part) for part in format_parts]

    if shell_scripts:
        package_manager = "multi" if package_manager != "unknown" else "shell"

    commands.update(
        {
            "install": join_parts(install_parts),
            "build": join_parts(build_parts),
            "test": join_parts(test_parts),
            "lint": join_parts(lint_parts),
            "format": join_parts(format_parts),
        }
    )

print(json.dumps({"commands": commands, "package_manager": package_manager}))
PY
}

detect_structure_json() {
  local target_dir="$1"
  python3 - "$target_dir" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])

def existing(patterns):
    out = []
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            rel = path.relative_to(root).as_posix()
            if rel not in out:
                out.append(rel)
    return out

monorepo = any((root / name).exists() for name in ["pnpm-workspace.yaml", "turbo.json", "nx.json", "melos.yaml"]) or ((root / "apps").is_dir() and ((root / "packages").is_dir() or (root / "services").is_dir()))

payload = {
    "monorepo": monorepo,
    "paths": {
        "app": existing([
            "app",
            "src/app",
            "pages",
            "src/pages",
            "apps/*",
            "apps/*/app",
            "apps/*/src/app",
            "dashboard",
            "www",
        ]),
        "services": existing([
            "services/*",
            "docker",
            "scripts",
            "systemd",
            "linux",
            "main.go",
            "monitor.py",
            "health_monitor.py",
        ]),
        "packages": existing(["packages/*"]),
        "infra": existing(["infra", "terraform", ".github", "docker", "systemd", "linux"]),
        "docs": existing(["docs", "memory-bank"]),
    },
    "protected_paths": [
        ".env*",
        ".git/**",
        "terraform.tfstate*",
        "infra/secrets/**",
        "secrets/**",
    ],
}

print(json.dumps(payload))
PY
}

resolve_agents() {
  local stack_name="$1"
  if [ -z "$AGENTS_CSV" ] || [ "$AGENTS_CSV" = "auto" ]; then
    AGENTS_CSV="$(default_agents_for_stack "$stack_name")"
  fi
  printf '%s\n' "$AGENTS_CSV"
}

csv_contains() {
  local csv=",$1,"
  local item="$2"
  case "$csv" in
    *",$item,"*) return 0 ;;
    *) return 1 ;;
  esac
}

detect_stack() {
  local project_dir="$1"

  python3 - "$LAYER_TEMPLATE_DIR/patterns/detectors" "$project_dir" <<'PY'
import pathlib
import sys

detectors_dir = pathlib.Path(sys.argv[1])
project_dir = pathlib.Path(sys.argv[2])

# Collect detector sources: project-local ai/stacks/ first (priority), then upstream
detector_files = []
custom_dir = project_dir / "ai" / "stacks"
if custom_dir.is_dir():
    detector_files.extend(sorted(custom_dir.glob("*.yaml")))
detector_files.extend(sorted(detectors_dir.glob("*.yaml")))

PRIMARY_WEIGHT = 3
SECONDARY_WEIGHT = 1

best_name = "generic"
best_score = 0
best_priority = 999


def probe(candidate):
    path = project_dir / candidate
    if candidate.endswith("/"):
        return path.is_dir()
    return path.exists()


for detector in detector_files:
    name = None
    priority = 50
    primary = []
    secondary = []
    current_section = None

    for raw_line in detector.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip()
            continue
        if line.startswith("priority:"):
            try:
                priority = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
            continue
        if line.startswith("match_primary:"):
            current_section = "primary"
            continue
        if line.startswith("match_any:"):
            current_section = "secondary"
            continue
        if line.startswith(("recommended_layout:", "agents:")):
            current_section = None
            continue
        if current_section and line.startswith("- "):
            marker = line[2:].strip()
            if current_section == "primary":
                primary.append(marker)
            else:
                secondary.append(marker)

    if not name:
        continue
    if not primary and not secondary:
        continue

    score = 0
    for marker in primary:
        if probe(marker):
            score += PRIMARY_WEIGHT
    for marker in secondary:
        if probe(marker):
            score += SECONDARY_WEIGHT

    if score > best_score or (score == best_score and score > 0 and priority < best_priority):
        best_name = name
        best_score = score
        best_priority = priority

print(best_name)
PY
}

layout_for_stack() {
  case "$1" in
    flutter) printf 'flutter\n' ;;
    nextjs) printf 'nextjs\n' ;;
    python-service) printf 'python-service\n' ;;
    ops-dashboard) printf 'backend-api\n' ;;
    fullstack|fullstack-monorepo) printf 'fullstack-monorepo\n' ;;
    go-service) printf 'go-service\n' ;;
    fastapi) printf 'fastapi\n' ;;
    data-ml) printf 'data-ml\n' ;;
    react-native) printf 'react-native\n' ;;
    node|python|go|backend-api) printf 'backend-api\n' ;;
    *) printf 'generic\n' ;;
  esac
}

is_managed_file() {
  local file="$1"
  [ -f "$file" ] || return 1
  grep -Eq 'managed[": ]+true' "$file"
}

sync_managed_or_stage() {
  local src="$1"
  local dest="$2"
  mkdir -p "$(dirname "$dest")"

  if [ "$DRY_RUN" = "1" ]; then
    if [ ! -e "$dest" ]; then
      log "dry-run: create $dest"
    elif is_managed_file "$dest"; then
      log "dry-run: update managed $dest"
    else
      log "dry-run: preserve custom $dest and stage $dest.generated"
    fi
    return
  fi

  if [ ! -e "$dest" ]; then
    cp "$src" "$dest"
    log "create $dest"
    return
  fi

  if is_managed_file "$dest"; then
    cp "$src" "$dest"
    log "update managed $dest"
    return
  fi

  if cmp -s "$src" "$dest"; then
    rm -f "$dest.generated"
    log "preserve custom $dest (no generated drift)"
    return
  fi

  cp "$src" "$dest.generated"
  log "preserve custom $dest and stage $dest.generated"
}

merge_managed_markdown_block() {
  local src="$1"
  local dest="$2"
  mkdir -p "$(dirname "$dest")"

  if [ "$DRY_RUN" = "1" ]; then
    if [ ! -e "$dest" ]; then
      log "dry-run: create $dest"
    elif is_managed_file "$dest"; then
      log "dry-run: update managed $dest"
    else
      log "dry-run: merge managed block into $dest"
    fi
    return
  fi

  if [ ! -e "$dest" ] || is_managed_file "$dest"; then
    cp "$src" "$dest"
    log "$([ -e "$dest" ] && printf 'update managed' || printf 'create') $dest"
    return
  fi

  python3 - "$src" "$dest" "$MANAGED_BEGIN" "$MANAGED_END" <<'PY'
import pathlib
import sys

src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
dest_path = pathlib.Path(sys.argv[2])
begin = sys.argv[3]
end = sys.argv[4]
dest = dest_path.read_text(encoding="utf-8")

lines = src.splitlines()
if lines and "managed: true" in lines[0]:
    src = "\n".join(lines[1:]).lstrip()

managed_body = begin + "\n" + src.strip() + "\n" + end + "\n"

if begin in dest and end in dest:
    start = dest.index(begin)
    finish = dest.index(end) + len(end)
    updated = dest[:start] + managed_body + dest[finish:]
else:
    updated = managed_body + "\n" + dest

dest_path.write_text(updated, encoding="utf-8")
PY
  log "merge managed block into $dest"
}

install_tree_from_template() {
  local src_dir="$1"
  local dest_dir="$2"
  [ -d "$src_dir" ] || return
  while IFS= read -r src; do
    local rel="${src#"$src_dir"/}"
    rel="${rel%.tmpl}"
    sync_managed_or_stage "$src" "$dest_dir/$rel"
  done < <(python3 - "$src_dir" <<'PY'
import pathlib
import sys
root = pathlib.Path(sys.argv[1])
for path in sorted(root.rglob('*')):
    if path.is_file():
        print(path)
PY
)
}

install_layer_tree() {
  local target_dir="$1"
  local project_stack="$2"
  local target_ai_dir="$target_dir/ai"

  mkdir -p "$target_ai_dir"

  python3 - "$LAYER_TEMPLATE_DIR" "$target_ai_dir" "$DRY_RUN" <<'PY'
import pathlib
import shutil
import sys

source_root = pathlib.Path(sys.argv[1])
target_root = pathlib.Path(sys.argv[2])
dry_run = sys.argv[3] == "1"
seed_only = {
    pathlib.Path("docs/changelog.md"),
    pathlib.Path("docs/decisions.md"),
    pathlib.Path("manifest/project.yaml"),
    pathlib.Path("manifest/discovery.json"),
    pathlib.Path("manifest/init-report.md"),
    pathlib.Path("experience/outbox/.gitkeep"),
    pathlib.Path("experience/events/.gitkeep"),
    pathlib.Path("experience/events/example.jsonl"),
    pathlib.Path("experience/candidates/.gitkeep"),
    pathlib.Path("experience/rejected/.gitkeep"),
    pathlib.Path("experience/archived/.gitkeep"),
    pathlib.Path("experience/accepted/rules/.gitkeep"),
    pathlib.Path("experience/accepted/skills/.gitkeep"),
    pathlib.Path("experience/accepted/playbooks/.gitkeep"),
    pathlib.Path("experience/accepted/anti-patterns/.gitkeep"),
}

for source in source_root.rglob("*"):
    if source.is_dir():
        continue
    relative = source.relative_to(source_root)
    target = target_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        print(f"[0dai-repo] {'dry-run: ' if dry_run else ''}create {target}")
        if not dry_run:
            shutil.copy2(source, target)
        continue
    if relative in seed_only:
        continue
    text = target.read_text(errors="ignore")
    if "managed: true" in text or '"managed": true' in text:
        print(f"[0dai-repo] {'dry-run: ' if dry_run else ''}update managed {target}")
        if not dry_run:
            shutil.copy2(source, target)
    else:
        generated = target.with_name(target.name + ".generated")
        source_bytes = source.read_bytes()
        target_bytes = target.read_bytes()
        if source_bytes == target_bytes:
            if generated.exists() and not dry_run:
                generated.unlink()
            print(f"[0dai-repo] {'dry-run: ' if dry_run else ''}preserve custom {target} (no generated drift)")
            continue
        print(f"[0dai-repo] {'dry-run: ' if dry_run else ''}preserve custom {target} and stage {generated}")
        if not dry_run:
            shutil.copy2(source, generated)
PY

  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run: write $target_ai_dir/VERSION"
  else
    printf '%s\n' "$CURRENT_AI_VERSION" > "$target_ai_dir/VERSION"
  fi
}

read_ai_version() {
  local target_dir="$1"
  if [ -f "$target_dir/ai/VERSION" ]; then
    tr -d '[:space:]' < "$target_dir/ai/VERSION"
  else
    printf 'none\n'
  fi
}

run_sync_migrations() {
  local target_dir="$1"
  local from_version
  from_version="$(read_ai_version "$target_dir")"

  if [ "$from_version" = "$CURRENT_AI_VERSION" ]; then
    log "ai layer already at version $CURRENT_AI_VERSION"
    return
  fi

  if [ "$from_version" = "none" ]; then
    log "no prior ai/VERSION found; treating sync as fresh canonical install"
    return
  fi

  log "migrating ai layer from $from_version to $CURRENT_AI_VERSION"

  python3 - "$REPO_ROOT/bootstrap/migrations" "$from_version" "$CURRENT_AI_VERSION" "$target_dir" "$DRY_RUN" "$REPO_ROOT" <<'PY'
import pathlib
import re
import subprocess
import sys

migrations_dir = pathlib.Path(sys.argv[1])
from_ver = sys.argv[2]
to_ver = sys.argv[3]
target_dir = sys.argv[4]
dry_run = sys.argv[5] == "1"
repo_root = sys.argv[6]

pattern = re.compile(r"^(.+)_to_(.+)\.sh$")

graph: dict[str, dict[str, pathlib.Path]] = {}
for script in sorted(migrations_dir.glob("*_to_*.sh")):
    m = pattern.match(script.name)
    if not m:
        continue
    src, dst = m.group(1), m.group(2)
    graph.setdefault(src, {})[dst] = script


def find_chain(start: str, end: str) -> list[tuple[str, str, pathlib.Path]] | None:
    visited: set[str] = set()
    queue: list[tuple[str, list[tuple[str, str, pathlib.Path]]]] = [(start, [])]
    while queue:
        current, path = queue.pop(0)
        if current == end:
            return path
        if current in visited:
            continue
        visited.add(current)
        for nxt, script in sorted(graph.get(current, {}).items()):
            queue.append((nxt, path + [(current, nxt, script)]))
    return None


chain = find_chain(from_ver, to_ver)
if chain is None:
    print(f"[0dai-repo] no migration chain from {from_ver} to {to_ver}; proceeding with managed sync")
    sys.exit(0)

if not chain:
    sys.exit(0)

for src, dst, script in chain:
    if dry_run:
        print(f"[0dai-repo] dry-run: execute {script.name} ({src} -> {dst})")
    else:
        print(f"[0dai-repo] running migration {script.name} ({src} -> {dst})")
        subprocess.run([str(script), target_dir], check=True)
PY
}

write_discovery_json() {
  local target_dir="$1"
  local project_stack="$2"
  local agents_csv="$3"
  local native_configs="$4"
  local commands_json
  commands_json="$(detect_commands_json "$target_dir")"
  local structure_json
  structure_json="$(detect_structure_json "$target_dir")"
  local discovery_file="$target_dir/ai/manifest/discovery.json"

  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run: write $discovery_file"
    return
  fi

  python3 - "$discovery_file" "$project_stack" "$agents_csv" "$native_configs" "$commands_json" "$structure_json" <<'PY'
import json
import pathlib
import sys

target = pathlib.Path(sys.argv[1])
stack = sys.argv[2]
agents = [item for item in sys.argv[3].split(",") if item]
native = [] if sys.argv[4] == "none" else sys.argv[4].split(",")
commands = json.loads(sys.argv[5])
structure = json.loads(sys.argv[6])

payload = {
    "managed": True,
    "stack": stack,
    "selected_agents": agents,
    "native_configs": native,
    "commands": commands["commands"],
    "package_manager": commands["package_manager"],
    "monorepo": structure["monorepo"],
    "paths": structure["paths"],
    "protected_paths": structure["protected_paths"],
}
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
}

write_project_manifest() {
  local target_dir="$1"
  local project_stack="$2"
  local agents_csv="$3"
  local commands_json
  commands_json="$(detect_commands_json "$target_dir")"
  local structure_json
  structure_json="$(detect_structure_json "$target_dir")"
  local manifest_file="$target_dir/ai/manifest/project.yaml"

  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run: write $manifest_file"
    return
  fi

  python3 - "$manifest_file" "$project_stack" "$agents_csv" "$commands_json" "$structure_json" <<'PY'
import json
import pathlib
import sys

target = pathlib.Path(sys.argv[1])
stack = sys.argv[2]
agents = [item for item in sys.argv[3].split(",") if item]
commands = json.loads(sys.argv[4])
structure = json.loads(sys.argv[5])

def enabled(name: str) -> str:
    return "true" if name in agents else "false"

def render_list(items, fallback):
    if items:
        return "".join(f"    - {item}\n" for item in items)
    return f"    - {fallback}\n"

monorepo_text = "true" if structure["monorepo"] else "false"
app_paths = render_list(structure["paths"]["app"], "app/**")
service_paths = render_list(structure["paths"]["services"], "services/**")
package_paths = render_list(structure["paths"]["packages"], "packages/**")
infra_paths = render_list(structure["paths"]["infra"], "infra/**")
doc_paths = render_list(structure["paths"]["docs"], "docs/**")
protected_paths = "".join(f"    - {item}\n" for item in structure["protected_paths"])

text = """managed: true
project:
  type: {stack}
  monorepo: {monorepo_text}
  package_manager: {package_manager}

commands:
  install: {install_command}
  build: {build_command}
  test: {test_command}
  lint: {lint_command}
  format: {format_command}

paths:
  app:
{app_paths}  services:
{service_paths}  packages:
{package_paths}  infra:
{infra_paths}  docs:
{doc_paths}

ai:
  tools:
    codex: {codex_enabled}
    claude: {claude_enabled}
    opencode: {opencode_enabled}
  plans_dir: ai/plans
  protected_paths:
{protected_paths}
""".format(
    stack=stack,
    monorepo_text=monorepo_text,
    package_manager=commands["package_manager"],
    install_command=json.dumps(commands["commands"].get("install", "")),
    build_command=json.dumps(commands["commands"].get("build", "")),
    test_command=json.dumps(commands["commands"].get("test", "")),
    lint_command=json.dumps(commands["commands"].get("lint", "")),
    format_command=json.dumps(commands["commands"].get("format", "")),
    app_paths=app_paths,
    service_paths=service_paths,
    package_paths=package_paths,
    infra_paths=infra_paths,
    doc_paths=doc_paths,
    codex_enabled=enabled("codex"),
    claude_enabled=enabled("claude"),
    opencode_enabled=enabled("opencode"),
    protected_paths=protected_paths,
)
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(text, encoding="utf-8")
PY
}

write_commands_manifest() {
  local target_dir="$1"
  local commands_json
  commands_json="$(detect_commands_json "$target_dir")"
  local structure_json
  structure_json="$(detect_structure_json "$target_dir")"
  local env_json
  env_json="$(detect_environment_json "$target_dir")"
  local manifest_file="$target_dir/ai/manifest/commands.yaml"

  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run: write $manifest_file"
    return
  fi

  python3 - "$manifest_file" "$commands_json" "$structure_json" "$env_json" <<'PY'
import json
import pathlib
import sys

target = pathlib.Path(sys.argv[1])
commands = json.loads(sys.argv[2])["commands"]
structure = json.loads(sys.argv[3])
environment = json.loads(sys.argv[4])

def tier_for(name: str, command: str) -> str:
    if not command:
        return "safe"
    lowered = command.lower()
    if any(token in lowered for token in ["deploy", "terraform apply", "systemctl", "docker run", "docker compose up", "kubectl apply", "service "]):
        return "ops"
    if name in {"install", "build", "test"}:
        return "workspace"
    if environment.get("kind") in {"ci", "cloud-cli"} and name == "build":
        return "workspace"
    return "safe"

text = "# managed: true\n\ncommands:\n"
for name in ["install", "build", "test", "lint", "format"]:
    command = commands.get(name, "")
    text += f"  {name}:\n"
    text += f"    command: {json.dumps(command)}\n"
    text += f"    tier: {tier_for(name, command)}\n"

text += "\npolicy:\n"
text += f"  monorepo: {'true' if structure.get('monorepo') else 'false'}\n"
text += f"  execution: {environment.get('execution', 'interactive')}\n"
text += f"  environment: {environment.get('kind', 'local')}\n"

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(text, encoding="utf-8")
PY
}

install_personas() {
  local target_dir="$1"
  local src_dir="$REPO_ROOT/templates/layer/ai/personas"
  local dst_dir="$target_dir/ai/personas"

  if [ ! -d "$src_dir" ]; then
    return
  fi

  mkdir -p "$dst_dir"
  for src_file in "$src_dir"/*.yaml; do
    [ -f "$src_file" ] || continue
    local name
    name="$(basename "$src_file")"
    local dst_file="$dst_dir/$name"
    if [ ! -f "$dst_file" ] || grep -q "^managed: true" "$dst_file" 2>/dev/null; then
      cp "$src_file" "$dst_file"
      debug "installed persona: $name"
    fi
  done
}

install_ide_configs() {
  local target_dir="$1"
  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run: generate IDE configs for VS Code and JetBrains"
  else
    python3 "$REPO_ROOT/scripts/generate_ide_configs.py" "$target_dir"
  fi
}

apply_mcp_catalog() {
  local target_dir="$1"
  local project_stack="$2"
  local catalog="$REPO_ROOT/templates/layer/ai/registry/mcp-catalog.json"

  if [ ! -f "$catalog" ]; then
    return
  fi

  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run: apply MCP catalog for stack $project_stack"
    return
  fi

  python3 - "$catalog" "$target_dir" "$project_stack" <<'PY'
import json
import pathlib
import sys

catalog_path = pathlib.Path(sys.argv[1])
target_dir = pathlib.Path(sys.argv[2])
stack = sys.argv[3]

catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
mcp_path = target_dir / ".mcp.json"

existing = {}
if mcp_path.is_file():
    try:
        existing = json.loads(mcp_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass

servers = existing.get("mcpServers", {})
added = 0

for name, config in catalog.get("common", {}).items():
    if name not in servers:
        cfg = dict(config)
        cfg.pop("description", None)
        servers[name] = cfg
        added += 1

stack_entry = catalog.get("stacks", {}).get(stack, {})
for name, config in stack_entry.get("servers", {}).items():
    if name not in servers:
        cfg = dict(config)
        cfg.pop("description", None)
        servers[name] = cfg
        added += 1

if added > 0:
    existing["mcpServers"] = servers
    mcp_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[0dai-repo] MCP catalog: added {added} server(s) for stack {stack}")
PY
}

write_codebase_map() {
  local target_dir="$1"
  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run: analyze codebase and write ai/manifest/codebase-map.json"
  else
    python3 "$REPO_ROOT/scripts/analyze_codebase.py" "$target_dir"
  fi
}

write_environment_manifest() {
  local target_dir="$1"
  local env_json
  env_json="$(detect_environment_json "$target_dir")"
  local manifest_file="$target_dir/ai/manifest/environment.yaml"

  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run: write $manifest_file"
    return
  fi

  python3 - "$manifest_file" "$env_json" <<'PY'
import json
import pathlib
import sys

target = pathlib.Path(sys.argv[1])
env = json.loads(sys.argv[2])

def yaml_bool(value):
    return "true" if value else "false"

text = "# managed: true\n\n"
text += f"kind: {env['kind']}\n"
text += f"execution: {env['execution']}\n"
text += f"os: {env['os']}\n"
text += "workspace:\n"
text += f"  target: {env['workspace']['target']}\n"
text += f"  cwd: {env['workspace']['cwd']}\n"
text += f"  writable: {yaml_bool(env['workspace']['writable'])}\n"
text += "available_clis:\n"
for item in env["available_clis"] or ["none"]:
    text += f"  - {item}\n"
text += "capabilities:\n"
for key, value in env["capabilities"].items():
    text += f"  {key}: {yaml_bool(value)}\n"
text += "constraints:\n"
for key, value in env["constraints"].items():
    text += f"  {key}: {yaml_bool(value)}\n"

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(text, encoding="utf-8")
PY
}

write_meta_manifest() {
  local target_dir="$1"
  local project_stack="$2"
  local agents_csv="$3"
  local manifest_file="$target_dir/ai/meta/project.manifest.yaml"

  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run: write $manifest_file"
    return
  fi

  python3 - "$manifest_file" "$project_stack" "$agents_csv" <<'PY'
import pathlib
import sys

target = pathlib.Path(sys.argv[1])
stack = sys.argv[2]
agents = [item for item in sys.argv[3].split(",") if item]

managed_paths = [
    "ai",
    "AGENTS.md",
    ".github/workflows/ai-layer-check.yml",
    ".agents/skills",
]

if "codex" in agents:
    managed_paths.extend([
        ".codex/config.toml",
        ".codex/agents",
    ])

if "claude" in agents:
    managed_paths.extend([
        ".claude/settings.json",
        ".claude/CLAUDE.md",
        ".claude/rules",
        ".claude/agents",
        ".claude/hooks",
        ".claude/skills",
        ".mcp.json",
    ])

if "opencode" in agents:
    managed_paths.extend([
        "opencode.json",
        ".opencode/agents",
    ])

text = "# managed: true\n\n"
text += "installed_from: ZeroDayAI\n"
text += f"stack: {stack}\n"
text += "managed_paths:\n"
for item in managed_paths:
    text += f"  - {item}\n"

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(text, encoding="utf-8")
PY
}

write_applied_lock() {
  local target_dir="$1"
  local project_stack="$2"
  local agents_csv="$3"
  local lock_file="$target_dir/ai/manifest/applied-lock.json"

  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run: write $lock_file"
    return
  fi

  python3 - "$target_dir" "$project_stack" "$agents_csv" "$lock_file" <<'PY'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
stack = sys.argv[2]
agents = [item for item in sys.argv[3].split(",") if item]
lock_file = pathlib.Path(sys.argv[4])

packs = {"core": "1.0.0"}
if "codex" in agents:
    packs["tool/codex"] = "1.0.0"
if "claude" in agents:
    packs["tool/claude"] = "1.0.0"
if "opencode" in agents:
    packs["tool/opencode"] = "1.0.0"
if stack and stack != "generic":
    packs[f"stack/{stack}"] = "1.0.0"

generated_paths = [
    "AGENTS.md",
    ".codex/config.toml",
    ".claude/settings.json",
    ".claude/CLAUDE.md",
    "opencode.json",
]

generated = {}
for rel in generated_paths:
    path = root / rel
    if path.exists() and path.is_file():
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        generated[rel] = f"sha256:{digest}"

payload = {
    "managed": True,
    "schema": 1,
    "channel": "stable",
    "packs": packs,
    "generated": generated,
}

lock_file.parent.mkdir(parents=True, exist_ok=True)
lock_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
}

write_init_report() {
  local target_dir="$1"
  local mode="$2"
  local project_stack="$3"
  local agents_csv="$4"
  local report_file="$target_dir/ai/manifest/init-report.md"

  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run: write $report_file"
    return
  fi

  cat > "$report_file" <<EOF
# managed: true

# Init Report

- mode: $mode
- stack: $project_stack
- selected_agents: $agents_csv
- ai_version: $CURRENT_AI_VERSION
- note: native tool files are generated from the canonical ai/ layer.
EOF
}

install_root_configs() {
  local target_dir="$1"
  local agents_csv="$2"
  local agents_md_source="$(native_map_path shared_agents_md)"
  local claude_md_source="$(native_map_path claude_md)"
  local codex_config_source="$(native_map_path codex_config)"
  local claude_settings_source="$(native_map_path claude_settings)"
  local opencode_config_source="$(native_map_path opencode_config)"
  local shared_rules_source="$(native_map_path shared_rules_dir)"
  local codex_agents_source="$(native_map_path codex_agents_dir)"
  local claude_agents_source="$(native_map_path claude_agents_dir)"
  local claude_hooks_source="$(native_map_path claude_hooks_dir)"
  local opencode_agents_source="$(native_map_path opencode_agents_dir)"
  local skills_source="$(native_map_path skills_dir)"
  local ci_workflow_source="$(native_map_path compat_ci_workflow)"
  local mcp_source="$(native_map_path compat_mcp)"

  if [ "$SKIP_ROOT_CONFIGS" = "1" ]; then
    log "skip root configs"
    return
  fi

  merge_managed_markdown_block "$agents_md_source" "$target_dir/AGENTS.md"

  if [ "$SKIP_CI" != "1" ]; then
    sync_managed_or_stage "$ci_workflow_source" "$target_dir/.github/workflows/ai-layer-check.yml"
  fi

  if csv_contains "$agents_csv" codex; then
    sync_managed_or_stage "$codex_config_source" "$target_dir/.codex/config.toml"
    install_tree_from_template "$codex_agents_source" "$target_dir/.codex/agents"
  fi

  if csv_contains "$agents_csv" claude; then
    sync_managed_or_stage "$claude_settings_source" "$target_dir/.claude/settings.json"
    merge_managed_markdown_block "$claude_md_source" "$target_dir/.claude/CLAUDE.md"
    sync_managed_or_stage "$mcp_source" "$target_dir/.mcp.json"
    install_tree_from_template "$shared_rules_source" "$target_dir/.claude/rules"
    install_tree_from_template "$claude_agents_source" "$target_dir/.claude/agents"
    install_tree_from_template "$claude_hooks_source" "$target_dir/.claude/hooks"
  fi

  if csv_contains "$agents_csv" opencode; then
    sync_managed_or_stage "$opencode_config_source" "$target_dir/opencode.json"
    install_tree_from_template "$opencode_agents_source" "$target_dir/.opencode/agents"
  fi

  if csv_contains "$agents_csv" gemini; then
    local gemini_config_source="$(native_map_path gemini_config)"
    local gemini_agents_source="$(native_map_path gemini_agents_dir)"
    sync_managed_or_stage "$gemini_config_source" "$target_dir/.gemini/settings.json"
    install_tree_from_template "$gemini_agents_source" "$target_dir/.gemini/agents"
  fi

  if csv_contains "$agents_csv" aider; then
    local aider_config_source="$(native_map_path aider_config)"
    local aider_agents_source="$(native_map_path aider_agents_dir)"
    sync_managed_or_stage "$aider_config_source" "$target_dir/.aider.conf.yml"
    install_tree_from_template "$aider_agents_source" "$target_dir/.aider/agents"
  fi

  install_tree_from_template "$skills_source" "$target_dir/.agents/skills"
  if csv_contains "$agents_csv" claude; then
    install_tree_from_template "$skills_source" "$target_dir/.claude/skills"
  fi
}

copy_if_missing() {
  local src="$1"
  local dest="$2"
  if [ -e "$dest" ]; then
    log "skip existing $dest"
  elif [ "$DRY_RUN" = "1" ]; then
    log "dry-run: create $dest"
  else
    mkdir -p "$(dirname "$dest")"
    cp "$src" "$dest"
    log "create $dest"
  fi
}

legacy_greenfield_structure_doc() {
  local project_stack="$1"
  local dest="$2"
  local layout_name
  layout_name="$(layout_for_stack "$project_stack")"
  [ -f "$REPO_ROOT/project_layouts/$layout_name/structure.md" ] || return 1
  cmp -s "$REPO_ROOT/project_layouts/$layout_name/structure.md" "$dest"
}

write_existing_structure_guidance() {
  local target_dir="$1"
  local project_stack="$2"
  local structure_json
  structure_json="$(detect_structure_json "$target_dir")"
  local dest="$target_dir/ai/docs/recommended-project-structure.md"

  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run: write $dest"
    return
  fi

  python3 - "$dest" "$project_stack" "$structure_json" <<'PY'
import json
import pathlib
import sys

dest = pathlib.Path(sys.argv[1])
stack = sys.argv[2]
structure = json.loads(sys.argv[3])

def fmt(items, fallback):
    if not items:
        return f"- {fallback}"
    return "\n".join(f"- `{item}`" for item in items)

title = {
    "nextjs": "Next.js Existing Repository Guidance",
    "flutter": "Flutter Existing Repository Guidance",
    "python-service": "Python Service Existing Repository Guidance",
    "ops-dashboard": "Ops Dashboard Existing Repository Guidance",
}.get(stack, "Existing Repository Guidance")

monorepo_text = "true" if structure["monorepo"] else "false"
app_paths = fmt(structure["paths"]["app"], "no app paths detected")
service_paths = fmt(structure["paths"]["services"], "no service paths detected")
package_paths = fmt(structure["paths"]["packages"], "no package paths detected")
infra_paths = fmt(structure["paths"]["infra"], "no infra paths detected")

text = """# managed: true

# {title}

This repository was onboarded with `0dai init-existing`, so the goal is to adapt to the current layout instead of forcing a greenfield reshape.

## Detected Shape

- stack: `{stack}`
- monorepo: `{monorepo_text}`

### App Paths

{app_paths}

### Service Paths

{service_paths}

### Package Paths

{package_paths}

### Infra Paths

{infra_paths}

## Guidance

- Preserve the current repository shape unless there is an explicit migration plan.
- Prefer updating `ai/manifest/project.yaml` and project docs over moving source directories.
- Add new AI-specific guidance in `ai/docs/` instead of rewriting existing product docs.
- Treat detected paths as the default review and planning scope for agents.
""".format(
    title=title,
    stack=stack,
    monorepo_text=monorepo_text,
    app_paths=app_paths,
    service_paths=service_paths,
    package_paths=package_paths,
    infra_paths=infra_paths,
)

dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(text + "\n", encoding="utf-8")
PY
}

install_recommended_structure() {
  local target_dir="$1"
  local project_stack="$2"
  local mode="${3:-init-new}"
  local dest="$target_dir/ai/docs/recommended-project-structure.md"

  if [ "$mode" = "init-existing" ] || [ "$mode" = "sync" ]; then
    if [ ! -e "$dest" ] || is_managed_file "$dest" || legacy_greenfield_structure_doc "$project_stack" "$dest"; then
      write_existing_structure_guidance "$target_dir" "$project_stack"
    else
      log "skip existing $dest"
    fi
    return
  fi

  local layout_name
  layout_name="$(layout_for_stack "$project_stack")"
  if [ -f "$REPO_ROOT/project_layouts/$layout_name/structure.md" ]; then
    copy_if_missing "$REPO_ROOT/project_layouts/$layout_name/structure.md" "$dest"
  fi
}

initialize_git_repo() {
  local target_dir="$1"
  if [ "$NO_GIT" = "1" ]; then
    return
  fi
  if [ -d "$target_dir/.git" ] || ! command -v git >/dev/null 2>&1; then
    return
  fi
  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run: initialize git repository"
  else
    git init "$target_dir" >/dev/null 2>&1
    log "initialized git repository"
  fi
}

print_summary() {
  local mode="$1"
  local target_dir="$2"
  local project_stack="$3"
  local agents_csv="$4"
  local native_configs="$5"

  if [ "$REPORT_FORMAT" = "json" ]; then
    python3 - "$mode" "$target_dir" "$project_stack" "$agents_csv" "$native_configs" <<'PY'
import json
import sys

native = [] if sys.argv[5] == "none" else sys.argv[5].split(",")
print(json.dumps({
    "mode": sys.argv[1],
    "target": sys.argv[2],
    "stack": sys.argv[3],
    "selected_agents": [item for item in sys.argv[4].split(",") if item],
    "native_configs": native,
}, indent=2))
PY
    return
  fi

  log "detected stack: $project_stack"
  log "selected agents: $agents_csv"
  [ "$native_configs" = "none" ] || log "existing native configs: $native_configs"
  log "$mode initialized at $target_dir"
}
