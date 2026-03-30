#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="$1"

# Ensure commands manifest exists (added in v0.1.12)
if [ ! -f "$TARGET_DIR/ai/manifest/commands.yaml" ]; then
  mkdir -p "$TARGET_DIR/ai/manifest"
  cat > "$TARGET_DIR/ai/manifest/commands.yaml" <<'EOF'
# managed: true

commands:
  lint:
    command: ""
    tier: safe
  format:
    command: ""
    tier: safe
  test:
    command: ""
    tier: safe
  build:
    command: ""
    tier: workspace
  install:
    command: ""
    tier: workspace
  deploy:
    command: ""
    tier: ops
  migrate:
    command: ""
    tier: ops
EOF
  printf '[0dai-repo] created ai/manifest/commands.yaml\n'
fi

# Ensure environment manifest exists (added in v0.1.11)
if [ ! -f "$TARGET_DIR/ai/manifest/environment.yaml" ]; then
  mkdir -p "$TARGET_DIR/ai/manifest"
  cat > "$TARGET_DIR/ai/manifest/environment.yaml" <<'EOF'
# managed: true

environment:
  kind: unknown
  execution_mode: interactive
  clis: []
  capabilities: []
  constraints: []
EOF
  printf '[0dai-repo] created ai/manifest/environment.yaml\n'
fi

# Ensure experience directories exist (added in v0.1.3)
mkdir -p "$TARGET_DIR/ai/experience/outbox"
mkdir -p "$TARGET_DIR/ai/experience/events"
mkdir -p "$TARGET_DIR/ai/experience/candidates"
mkdir -p "$TARGET_DIR/ai/experience/accepted"

# Ensure VERSION_SCHEMA exists (added in v0.1.1)
if [ ! -f "$TARGET_DIR/ai/VERSION_SCHEMA" ]; then
  printf '1\n' > "$TARGET_DIR/ai/VERSION_SCHEMA"
fi

# Ensure specs directory exists (added in v0.5.1)
mkdir -p "$TARGET_DIR/ai/specs"

printf '[0dai-repo] migration 0.1.1 -> 1.0.0-rc.1 complete\n'
