#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"
ODAI_TRUST_MODE="${ODAI_TRUST_MODE:-trusted}"
ODAI_BOOTSTRAP_MODE="${ODAI_BOOTSTRAP_MODE:-auto}"
ODAI_CHECK_TOOLS="${ODAI_CHECK_TOOLS:-1}"

mkdir -p "$HOME" /state/cache /state/logs

log() {
  printf '[0dai-entrypoint] %s\n' "$*"
}

fail() {
  printf '[0dai-entrypoint] error: %s\n' "$*" >&2
  exit 1
}

if [ ! -d "$WORKSPACE_DIR" ]; then
  fail "workspace directory does not exist: $WORKSPACE_DIR"
fi

case "$ODAI_TRUST_MODE" in
  trusted|untrusted) ;;
  *) fail "ODAI_TRUST_MODE must be trusted or untrusted" ;;
esac

case "$ODAI_BOOTSTRAP_MODE" in
  auto|init|sync|none) ;;
  *) fail "ODAI_BOOTSTRAP_MODE must be auto, init, sync, or none" ;;
esac

if [ "$ODAI_CHECK_TOOLS" = "1" ] && command -v 0dai-check-tools >/dev/null 2>&1; then
  log "tool availability"
  0dai-check-tools || true
fi

if [ -d "$WORKSPACE_DIR/.git" ] && [ -x "$WORKSPACE_DIR/bin/0dai-repo" ]; then
  if [ "$ODAI_BOOTSTRAP_MODE" = "none" ]; then
    log "bootstrap disabled"
  elif [ "$ODAI_TRUST_MODE" = "untrusted" ]; then
    log "untrusted mode: skip automatic bootstrap"
  elif [ "$ODAI_BOOTSTRAP_MODE" = "init" ]; then
    log "running forced init-existing"
    "$WORKSPACE_DIR/bin/0dai-repo" init-existing --target "$WORKSPACE_DIR"
  elif [ "$ODAI_BOOTSTRAP_MODE" = "sync" ]; then
    log "running forced sync"
    "$WORKSPACE_DIR/bin/0dai-repo" sync --target "$WORKSPACE_DIR"
  elif [ ! -d "$WORKSPACE_DIR/ai" ]; then
    log "ai/ missing: running init-existing"
    "$WORKSPACE_DIR/bin/0dai-repo" init-existing --target "$WORKSPACE_DIR"
  else
    log "ai/ present: running sync"
    "$WORKSPACE_DIR/bin/0dai-repo" sync --target "$WORKSPACE_DIR"
  fi
else
  log "workspace is not a bootstrappable git repository; skipping bootstrap"
fi

exec "$@"
