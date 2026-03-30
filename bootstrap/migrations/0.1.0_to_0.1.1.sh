#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="$1"

mkdir -p "$TARGET_DIR/ai/manifest"

if [ ! -f "$TARGET_DIR/ai/manifest/project.yaml" ] && [ -f "$TARGET_DIR/ai/meta/project.manifest.yaml" ]; then
  cat > "$TARGET_DIR/ai/manifest/project.yaml" <<'EOF'
managed: true
project:
  type: generic
  monorepo: false
  package_manager: unknown

commands:
  install: ""
  build: ""
  test: ""
  lint: ""
  format: ""

paths:
  app:
    - app/**
  services:
    - services/**
  packages:
    - packages/**
  infra:
    - infra/**
  docs:
    - docs/**

ai:
  tools:
    codex: true
    claude: true
    opencode: true
  plans_dir: ai/plans
  protected_paths:
    - .env*
    - .git/**
    - terraform.tfstate*
EOF
fi

if [ ! -f "$TARGET_DIR/ai/manifest/discovery.json" ]; then
  cat > "$TARGET_DIR/ai/manifest/discovery.json" <<'EOF'
{
  "managed": true,
  "stack": "generic",
  "detected_files": [],
  "native_configs": [],
  "commands": {}
}
EOF
fi

if [ ! -f "$TARGET_DIR/ai/manifest/init-report.md" ]; then
  cat > "$TARGET_DIR/ai/manifest/init-report.md" <<'EOF'
# managed: true

# Init Report

- mode: migration
- stack: generic
- selected_agents: codex,claude,opencode
- note: migrated to manifest-aware ZeroDayAI layout.
EOF
fi
