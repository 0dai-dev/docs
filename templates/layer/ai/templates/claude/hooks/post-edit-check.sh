#!/usr/bin/env bash
set -eu
# managed: true

if [ -x ./ai/bootstrap/hooks/run_tests.sh ]; then
  ./ai/bootstrap/hooks/run_tests.sh
fi
