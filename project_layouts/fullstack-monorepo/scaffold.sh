#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="$1"

mkdir -p \
  "$TARGET_DIR/apps/web/app" \
  "$TARGET_DIR/services/api/src" \
  "$TARGET_DIR/packages/ui" \
  "$TARGET_DIR/packages/sdk" \
  "$TARGET_DIR/infra" \
  "$TARGET_DIR/tools" \
  "$TARGET_DIR/docs"

if [ ! -f "$TARGET_DIR/package.json" ]; then
  cat > "$TARGET_DIR/package.json" <<'EOF'
{
  "name": "ai-ready-fullstack-monorepo",
  "private": true,
  "workspaces": ["apps/*", "services/*", "packages/*"]
}
EOF
fi
