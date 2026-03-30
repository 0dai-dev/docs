#!/usr/bin/env bash
set -eu
# managed: true

if [ -x ./tools/test.sh ]; then
  ./tools/test.sh
  exit 0
fi

if [ -f ./package.json ]; then
  npm test --silent
  exit 0
fi

if [ -f ./pyproject.toml ] || [ -f ./requirements.txt ]; then
  python -m pytest
  exit 0
fi

if [ -f ./pubspec.yaml ]; then
  flutter test
  exit 0
fi

printf '[ai-layer] no known test command for this repository\n'
