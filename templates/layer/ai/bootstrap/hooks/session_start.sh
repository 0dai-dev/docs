#!/usr/bin/env bash
set -eu
# managed: true

printf '[ai-layer] session start: read ai/docs/README.ai.md and ai/playbooks/onboarding.md\n'

# Session roaming: if another agent left an active session, show handoff notes
if [ -f "ai/sessions/active.json" ]; then
  printf '[ai-layer] ACTIVE SESSION DETECTED — pick up where the last agent left off:\n'
  python3 -c "
import json, pathlib
s = json.loads(pathlib.Path('ai/sessions/active.json').read_text())
print(f\"  Goal: {s.get('task',{}).get('goal','?')}\")
print(f\"  Last agent: {s.get('current_agent','?')}\")
notes = s.get('handoff_notes','')
if notes: print(f'  Handoff: {notes}')
files = s.get('context',{}).get('files_touched',[])
if files: print(f'  Files: {\", \".join(files[:5])}')
" 2>/dev/null || true
fi
