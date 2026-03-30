#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "$0")" && pwd)/common.sh"

parse_kv_args "$@"
require_target

project_stack="${STACK_NAME:-auto}"
if [ -z "$project_stack" ] || [ "$project_stack" = "auto" ]; then
  project_stack="$(detect_stack "$TARGET_DIR")"
fi

native_configs="$(detect_native_configs "$TARGET_DIR")"
available_clis="$(detect_available_clis)"
selected_agents="$(resolve_agents "$project_stack")"

install_layer_tree "$TARGET_DIR" "$project_stack"
write_discovery_json "$TARGET_DIR" "$project_stack" "$selected_agents" "$native_configs"
write_project_manifest "$TARGET_DIR" "$project_stack" "$selected_agents"
write_environment_manifest "$TARGET_DIR"
write_commands_manifest "$TARGET_DIR"
write_codebase_map "$TARGET_DIR"
install_personas "$TARGET_DIR"
install_ide_configs "$TARGET_DIR"
apply_mcp_catalog "$TARGET_DIR" "$project_stack"
install_root_configs "$TARGET_DIR" "$selected_agents"
write_meta_manifest "$TARGET_DIR" "$project_stack" "$selected_agents"
install_recommended_structure "$TARGET_DIR" "$project_stack" "init-existing"
write_applied_lock "$TARGET_DIR" "$project_stack" "$selected_agents"
write_init_report "$TARGET_DIR" "init-existing" "$project_stack" "$selected_agents"

python3 "$REPO_ROOT/scripts/audit.py" --target "$TARGET_DIR" --action init-existing --details "stack=$project_stack agents=$selected_agents"
log "available CLIs: $available_clis"
print_summary "existing project" "$TARGET_DIR" "$project_stack" "$selected_agents" "$native_configs"
