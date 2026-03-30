#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="$1"

mkdir -p \
  "$TARGET_DIR/apps/web/app" \
  "$TARGET_DIR/apps/web/public" \
  "$TARGET_DIR/packages/ui" \
  "$TARGET_DIR/packages/config" \
  "$TARGET_DIR/infra" \
  "$TARGET_DIR/tools" \
  "$TARGET_DIR/docs"

if [ ! -f "$TARGET_DIR/package.json" ]; then
  cat > "$TARGET_DIR/package.json" <<'EOF'
{
  "name": "ai-ready-nextjs-app",
  "private": true,
  "workspaces": ["apps/*", "packages/*"]
}
EOF
fi

if [ ! -f "$TARGET_DIR/next.config.js" ]; then
  cat > "$TARGET_DIR/next.config.js" <<'EOF'
module.exports = {};
EOF
fi
