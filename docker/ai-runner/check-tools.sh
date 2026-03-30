#!/usr/bin/env bash
set -euo pipefail

printf 'git:       %s\n' "$(git --version 2>/dev/null || echo missing)"
printf 'python3:   %s\n' "$(python3 --version 2>/dev/null || echo missing)"
printf 'codex:     %s\n' "$(codex --version 2>/dev/null || echo missing)"
printf 'claude:    %s\n' "$(claude --version 2>/dev/null || echo missing)"
printf 'opencode:  %s\n' "$(opencode --version 2>/dev/null || echo missing)"
printf 'bubblewrap:%s\n' "$(bwrap --version 2>/dev/null || echo missing)"
printf 'socat:     %s\n' "$(socat -V 2>/dev/null | head -n 1 || echo missing)"
