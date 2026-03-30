#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="$1"

mkdir -p \
  "$TARGET_DIR/app/api/routes" \
  "$TARGET_DIR/app/core" \
  "$TARGET_DIR/app/models" \
  "$TARGET_DIR/app/schemas" \
  "$TARGET_DIR/app/services" \
  "$TARGET_DIR/tests" \
  "$TARGET_DIR/migrations" \
  "$TARGET_DIR/infra" \
  "$TARGET_DIR/tools" \
  "$TARGET_DIR/docs"

if [ ! -f "$TARGET_DIR/pyproject.toml" ]; then
  cat > "$TARGET_DIR/pyproject.toml" <<'EOF'
[project]
name = "ai-ready-fastapi-service"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.29",
]

[project.optional-dependencies]
dev = ["pytest", "httpx"]
EOF
fi

if [ ! -f "$TARGET_DIR/app/main.py" ]; then
  cat > "$TARGET_DIR/app/main.py" <<'EOF'
from fastapi import FastAPI

app = FastAPI(title="AI-Ready FastAPI Service")


@app.get("/health")
def health():
    return {"status": "ok"}
EOF
fi
