#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="$1"

# v0.7.3: Session roaming — create sessions directory
mkdir -p "$TARGET_DIR/ai/sessions/archive"

printf '[0dai-repo] migration 0.7.2 -> 0.7.3 complete\n'
