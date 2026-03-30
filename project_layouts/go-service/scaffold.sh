#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="$1"

mkdir -p \
  "$TARGET_DIR/cmd/server" \
  "$TARGET_DIR/internal/handler" \
  "$TARGET_DIR/internal/service" \
  "$TARGET_DIR/internal/store" \
  "$TARGET_DIR/pkg" \
  "$TARGET_DIR/migrations" \
  "$TARGET_DIR/infra" \
  "$TARGET_DIR/tools" \
  "$TARGET_DIR/docs"

if [ ! -f "$TARGET_DIR/go.mod" ]; then
  cat > "$TARGET_DIR/go.mod" <<'EOF'
module ai-ready-go-service

go 1.22
EOF
fi

if [ ! -f "$TARGET_DIR/cmd/server/main.go" ]; then
  cat > "$TARGET_DIR/cmd/server/main.go" <<'EOF'
package main

import "fmt"

func main() {
	fmt.Println("server starting")
}
EOF
fi
