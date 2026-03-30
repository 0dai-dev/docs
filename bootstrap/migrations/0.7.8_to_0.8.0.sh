#!/usr/bin/env bash
set -euo pipefail
TARGET_DIR="$1"
# v0.8.0: Plugin system — create plugins directory
mkdir -p "$TARGET_DIR/ai/plugins"
printf '[0dai-repo] migration 0.7.8 -> 0.8.0 complete\n'
