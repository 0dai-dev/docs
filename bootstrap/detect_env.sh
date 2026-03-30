#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "$0")" && pwd)/common.sh"

TARGET_DIR=""
parse_kv_args "$@"
require_target

project_stack="$(detect_stack "$TARGET_DIR")"
available_clis="$(detect_available_clis)"

printf 'target=%s\n' "$TARGET_DIR"
printf 'stack=%s\n' "$project_stack"
printf 'available_clis=%s\n' "$available_clis"
printf 'os=%s\n' "$(uname -s)"
printf 'shell=%s\n' "${SHELL:-unknown}"

if command -v codex >/dev/null 2>&1; then
  printf 'codex=installed\n'
else
  printf 'codex=missing\n'
fi

if command -v claude >/dev/null 2>&1; then
  printf 'claude=installed\n'
else
  printf 'claude=missing\n'
fi

if command -v opencode >/dev/null 2>&1; then
  printf 'opencode=installed\n'
else
  printf 'opencode=missing\n'
fi

if command -v gemini >/dev/null 2>&1; then
  printf 'gemini=installed\n'
else
  printf 'gemini=missing\n'
fi

if command -v aider >/dev/null 2>&1; then
  printf 'aider=installed\n'
else
  printf 'aider=missing\n'
fi

for probe in "$TARGET_DIR/.codex/config.toml" "$TARGET_DIR/.claude/settings.json" "$TARGET_DIR/.claude/CLAUDE.md" "$TARGET_DIR/opencode.json" "$TARGET_DIR/.opencode" "$TARGET_DIR/.gemini/settings.json" "$TARGET_DIR/.gemini" "$TARGET_DIR/.aider.conf.yml" "$TARGET_DIR/.aider" "$TARGET_DIR/.claude" "$TARGET_DIR/.codex" "$TARGET_DIR/.agents/skills" "$TARGET_DIR/ai/VERSION"; do
  if [ -e "$probe" ]; then
    printf 'present=%s\n' "$probe"
  fi
done
