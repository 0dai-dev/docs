#!/usr/bin/env bash
set -euo pipefail
# managed: true

# Shared helpers for project-local ZeroDayAI bootstrap wrappers.
# The upstream repository owns the main bootstrap implementation;
# this file defines the local contract expected inside generated repos.

ai_log() {
  printf '[zerodayai] %s\n' "$*"
}

ai_fail() {
  printf '[zerodayai] error: %s\n' "$*" >&2
  exit 1
}
