#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="$1"

mkdir -p \
  "$TARGET_DIR/notebooks" \
  "$TARGET_DIR/src/data" \
  "$TARGET_DIR/src/features" \
  "$TARGET_DIR/src/models" \
  "$TARGET_DIR/src/pipelines" \
  "$TARGET_DIR/tests" \
  "$TARGET_DIR/data/raw" \
  "$TARGET_DIR/data/processed" \
  "$TARGET_DIR/models" \
  "$TARGET_DIR/configs" \
  "$TARGET_DIR/infra" \
  "$TARGET_DIR/tools" \
  "$TARGET_DIR/docs"

if [ ! -f "$TARGET_DIR/pyproject.toml" ]; then
  cat > "$TARGET_DIR/pyproject.toml" <<'EOF'
[project]
name = "ai-ready-data-ml-workspace"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pandas>=2.0",
    "scikit-learn>=1.4",
]

[project.optional-dependencies]
dev = ["pytest", "jupyter", "ruff"]
EOF
fi

if [ ! -f "$TARGET_DIR/.gitignore" ]; then
  cat > "$TARGET_DIR/.gitignore" <<'EOF'
data/raw/
data/processed/
models/*.pkl
models/*.pt
*.pyc
__pycache__/
.ipynb_checkpoints/
EOF
fi
