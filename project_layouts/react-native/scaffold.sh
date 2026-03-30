#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="$1"

mkdir -p \
  "$TARGET_DIR/src/screens" \
  "$TARGET_DIR/src/navigation" \
  "$TARGET_DIR/src/components" \
  "$TARGET_DIR/src/services" \
  "$TARGET_DIR/src/hooks" \
  "$TARGET_DIR/src/assets" \
  "$TARGET_DIR/__tests__" \
  "$TARGET_DIR/infra" \
  "$TARGET_DIR/tools" \
  "$TARGET_DIR/docs"

if [ ! -f "$TARGET_DIR/package.json" ]; then
  cat > "$TARGET_DIR/package.json" <<'EOF'
{
  "name": "ai-ready-react-native-app",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "start": "react-native start",
    "test": "jest",
    "lint": "eslint ."
  }
}
EOF
fi

if [ ! -f "$TARGET_DIR/app.json" ]; then
  cat > "$TARGET_DIR/app.json" <<'EOF'
{
  "name": "AiReadyApp",
  "displayName": "AI Ready App"
}
EOF
fi

if [ ! -f "$TARGET_DIR/metro.config.js" ]; then
  cat > "$TARGET_DIR/metro.config.js" <<'EOF'
module.exports = {};
EOF
fi
