#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="$1"

mkdir -p \
  "$TARGET_DIR/app/lib" \
  "$TARGET_DIR/app/test" \
  "$TARGET_DIR/app/assets" \
  "$TARGET_DIR/packages" \
  "$TARGET_DIR/infra" \
  "$TARGET_DIR/tools" \
  "$TARGET_DIR/docs"

if [ ! -f "$TARGET_DIR/pubspec.yaml" ]; then
  cat > "$TARGET_DIR/pubspec.yaml" <<'EOF'
name: ai_ready_flutter_app
description: AI-ready Flutter application scaffold.
publish_to: none
version: 0.1.0+1
environment:
  sdk: '>=3.3.0 <4.0.0'
EOF
fi
