#!/usr/bin/env bash
set -euo pipefail
TARGET_DIR="$1"

# v0.5.0: MCP write tools — ensure experience events dir exists
mkdir -p "$TARGET_DIR/ai/experience/events"
mkdir -p "$TARGET_DIR/ai/specs"

printf '[0dai-repo] migration 0.4.4 -> 0.5.0 complete\n'
