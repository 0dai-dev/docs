#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "$0")" && pwd)/common.sh"

parse_kv_args "$@"
require_target

BULLETINS_SRC="$REPO_ROOT/templates/layer/ai/bulletins"
BULLETINS_DST="$TARGET_DIR/ai/bulletins"

if [ ! -d "$BULLETINS_SRC" ]; then
  log "no bulletins source directory"
  exit 0
fi

mkdir -p "$BULLETINS_DST"

installed=0
skipped=0

for src_file in "$BULLETINS_SRC"/*.yaml; do
  [ -f "$src_file" ] || continue
  name="$(basename "$src_file")"
  dst_file="$BULLETINS_DST/$name"

  if [ -f "$dst_file" ]; then
    skipped=$((skipped + 1))
    debug "bulletin already installed: $name"
  else
    if [ "$DRY_RUN" = "1" ]; then
      log "dry-run: install bulletin $name"
    else
      cp "$src_file" "$dst_file"
      log "installed bulletin: $name"
    fi
    installed=$((installed + 1))
  fi
done

# Prune expired bulletins
python3 - "$BULLETINS_DST" <<'PY'
import datetime
import pathlib
import sys

bulletins_dir = pathlib.Path(sys.argv[1])
today = datetime.date.today()
pruned = 0

for path in sorted(bulletins_dir.glob("*.yaml")):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("expires:"):
            try:
                expires = datetime.date.fromisoformat(line.split(":", 1)[1].strip())
                if expires < today:
                    path.unlink()
                    pruned += 1
                    print(f"[0dai-repo] pruned expired bulletin: {path.name}")
            except ValueError:
                pass
            break

if pruned:
    print(f"[0dai-repo] pruned {pruned} expired bulletin(s)")
PY

log "bulletins: $installed new, $skipped already present"
