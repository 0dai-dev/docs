#!/usr/bin/env bash
set -euo pipefail
TARGET_DIR="$1"
mkdir -p "$TARGET_DIR/ai/orchestration"
printf '[0dai-repo] migration 0.5.0 -> 0.5.1 complete\n'
