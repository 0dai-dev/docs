#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="$1"

# v0.4.1: Code graph analysis — re-run sync to regenerate codebase-map with import_graph.

printf '[0dai-repo] migration 0.4.0 -> 0.4.1 complete\n'
