#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="$1"

mkdir -p \
  "$TARGET_DIR/services/api/src" \
  "$TARGET_DIR/services/api/tests" \
  "$TARGET_DIR/packages" \
  "$TARGET_DIR/infra" \
  "$TARGET_DIR/tools" \
  "$TARGET_DIR/docs"

if [ ! -f "$TARGET_DIR/pyproject.toml" ]; then
  cat > "$TARGET_DIR/pyproject.toml" <<'EOF'
[project]
name = "ai-ready-python-service"
version = "0.1.0"
requires-python = ">=3.11"
EOF
fi
