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

if [ ! -f "$TARGET_DIR/README.md" ]; then
  cat > "$TARGET_DIR/README.md" <<'EOF'
# Backend API

AI-ready backend repository scaffold.
EOF
fi
