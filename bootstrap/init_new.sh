#!/usr/bin/env bash
set -euo pipefail

. "$(cd "$(dirname "$0")" && pwd)/common.sh"

parse_kv_args "$@"
ensure_target_parent

project_stack="${STACK_NAME:-generic}"
selected_agents="$(resolve_agents "$project_stack")"
layout_name="$(layout_for_stack "$project_stack")"

if [ -f "$REPO_ROOT/project_layouts/$layout_name/scaffold.sh" ]; then
  log "scaffolding stack: $project_stack"
  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run: execute $REPO_ROOT/project_layouts/$layout_name/scaffold.sh $TARGET_DIR"
  else
    "$REPO_ROOT/project_layouts/$layout_name/scaffold.sh" "$TARGET_DIR"
  fi
else
  log "no dedicated scaffold for $project_stack, creating generic project"
  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run: create generic src/tests/docs/tools layout"
  else
    mkdir -p "$TARGET_DIR/src" "$TARGET_DIR/tests" "$TARGET_DIR/docs" "$TARGET_DIR/tools"
  fi
fi

if [ "$LAYOUT_ONLY" != "1" ]; then
  install_layer_tree "$TARGET_DIR" "$project_stack"
  write_discovery_json "$TARGET_DIR" "$project_stack" "$selected_agents" "none"
  write_project_manifest "$TARGET_DIR" "$project_stack" "$selected_agents"
  write_environment_manifest "$TARGET_DIR"
  write_commands_manifest "$TARGET_DIR"
  install_root_configs "$TARGET_DIR" "$selected_agents"
  write_meta_manifest "$TARGET_DIR" "$project_stack" "$selected_agents"
  copy_if_missing "$(native_map_path compat_gitignore)" "$TARGET_DIR/.gitignore"
  install_recommended_structure "$TARGET_DIR" "$project_stack" "init-new"
  write_applied_lock "$TARGET_DIR" "$project_stack" "$selected_agents"
  write_init_report "$TARGET_DIR" "init-new" "$project_stack" "$selected_agents"
fi

initialize_git_repo "$TARGET_DIR"
print_summary "new project" "$TARGET_DIR" "$project_stack" "$selected_agents" "none"
