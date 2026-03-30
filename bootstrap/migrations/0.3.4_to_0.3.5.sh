#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="$1"

# v0.3.5: Spec-driven development — create ai/specs/ directory
mkdir -p "$TARGET_DIR/ai/specs"

printf '[0dai-repo] migration 0.3.4 -> 0.3.5 complete\n'
