#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "$0")" && pwd)/common.sh"

parse_kv_args "$@"
require_target

if [ ! -d "$TARGET_DIR/ai/experience/outbox" ]; then
  fail "missing ai/experience/outbox in target: $TARGET_DIR"
fi

python3 - "$TARGET_DIR" "$DRY_RUN" "$REPORT_FORMAT" <<'PY'
import collections
import datetime as dt
import json
import os
import pathlib
import sys

target = pathlib.Path(sys.argv[1])
dry_run = sys.argv[2] == "1"
report_format = sys.argv[3]

outbox = target / "ai/experience/outbox"
candidates_dir = target / "ai/experience/candidates"
events_dir = target / "ai/experience/events"

events = []
for path in sorted(outbox.glob("*.json")):
    events.append((path, json.loads(path.read_text(encoding="utf-8"))))

for path in sorted(outbox.glob("*.jsonl")):
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            events.append((path.with_name(f"{path.stem}-{idx}.json"), json.loads(line)))

groups = collections.defaultdict(list)
for synthetic_path, event in events:
    kind = event.get("candidate_type", "none")
    if kind == "none":
        continue
    summary = event.get("summary", "candidate").strip().lower().replace(" ", "-")
    key = (kind, event.get("task_type", "unknown"), summary)
    groups[key].append(event)

created = []
archived = []
today = dt.date.today().isoformat()
ttl_days = int(os.environ.get("ODAI_EXPERIENCE_TTL_DAYS", "180"))
expires_at = (dt.date.today() + dt.timedelta(days=ttl_days)).isoformat()

for (kind, task_type, summary), grouped_events in groups.items():
    candidate_id = f"candidate.{task_type}.{summary}"[:120]
    candidate_path = candidates_dir / f"{candidate_id}.md"
    tools = sorted({event.get("tool", "mixed") for event in grouped_events})
    paths = sorted({path for event in grouped_events for path in event.get("paths", ["**/*"])}) or ["**/*"]
    sources = [event.get("id", f"event-{index+1}") for index, event in enumerate(grouped_events)]
    confidence = "high" if len(grouped_events) >= 3 else "medium"
    body = f"""---
managed: true
id: {candidate_id}
type: {kind}
version: 0.1.0
status: candidate
scope:
  paths: {json.dumps(paths)}
  tools: {json.dumps(tools)}
confidence: {confidence}
sources: {json.dumps(sources)}
validated_by: []
last_validated: {today}
expires_at: {expires_at}
---

# Candidate Lesson

## Observation

{grouped_events[0].get('summary', 'No summary provided.')}

## Proposed Promotion

- `{kind}`

## Evidence

- occurrences: {len(grouped_events)}
- source events: {', '.join(sources)}
"""
    created.append(str(candidate_path.relative_to(target)))
    if not dry_run:
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        candidate_path.write_text(body, encoding="utf-8")

for source_path, event in events:
    archived_path = events_dir / source_path.name
    archived.append(str(archived_path.relative_to(target)))
    if not dry_run:
        archived_path.parent.mkdir(parents=True, exist_ok=True)
        archived_path.write_text(json.dumps(event) + "\n", encoding="utf-8")
        if source_path.exists():
            source_path.unlink()

payload = {
    "target": str(target),
    "mode": "harvest",
    "events_processed": len(events),
    "candidates_created": created,
    "events_archived": archived,
}

if report_format == "json":
    print(json.dumps(payload, indent=2))
else:
    print(f"[0dai-repo] harvested {len(events)} events")
    for item in created:
        print(f"[0dai-repo] candidate {item}")
    for item in archived:
        print(f"[0dai-repo] archive {item}")
PY
