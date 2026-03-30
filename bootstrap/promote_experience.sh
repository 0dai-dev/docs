#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "$0")" && pwd)/common.sh"

parse_kv_args "$@"
require_target

python3 - "$TARGET_DIR" "$DRY_RUN" "$REPORT_FORMAT" <<'PY'
import pathlib
import re
import shutil
import sys
import json

target = pathlib.Path(sys.argv[1])
dry_run = sys.argv[2] == "1"
report_format = sys.argv[3]

candidates_dir = target / "ai/experience/candidates"
accepted_dir = target / "ai/experience/accepted"

if not candidates_dir.exists():
    raise SystemExit(f"[0dai-repo] error: missing {candidates_dir}")

promoted = []

for path in sorted(candidates_dir.glob("candidate.*.md")):
    text = path.read_text(encoding="utf-8")
    type_match = re.search(r"^type:\s*(.+)$", text, re.MULTILINE)
    id_match = re.search(r"^id:\s*(.+)$", text, re.MULTILINE)
    if not type_match or not id_match:
        continue

    candidate_type = type_match.group(1).strip()
    candidate_id = id_match.group(1).strip()
    destination_dir = accepted_dir / {
        "rule": "rules",
        "skill": "skills",
        "playbook": "playbooks",
        "anti-pattern": "anti-patterns",
    }.get(candidate_type, "skills")
    destination = destination_dir / path.name.replace("candidate.", "accepted.")

    promoted.append(str(destination.relative_to(target)))
    if dry_run:
        continue

    destination_dir.mkdir(parents=True, exist_ok=True)
    updated = text.replace("status: candidate", "status: accepted", 1)
    updated = updated.replace(candidate_id, candidate_id.replace("candidate.", "lesson."), 1)
    destination.write_text(updated, encoding="utf-8")
    path.unlink()

payload = {
    "target": str(target),
    "mode": "promote",
    "promoted": promoted,
}

if report_format == "json":
    print(json.dumps(payload, indent=2))
else:
    print(f"[0dai-repo] promoted {len(promoted)} candidates")
    for item in promoted:
        print(f"[0dai-repo] accepted {item}")
PY
