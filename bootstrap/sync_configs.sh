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
selected_agents="$(resolve_agents "$project_stack")"

log "syncing canonical ai/ layer and native outputs"

# Pre-sync backup of ai/ directory
if [ -d "$TARGET_DIR/ai" ]; then
  backup_dir="$TARGET_DIR/ai/.backups"
  mkdir -p "$backup_dir"
  backup_name="pre-sync-$(date -u +%Y%m%dT%H%M%SZ).tar.gz"
  if [ "$DRY_RUN" = "1" ]; then
    log "dry-run: backup ai/ to $backup_dir/$backup_name"
  else
    tar -czf "$backup_dir/$backup_name" -C "$TARGET_DIR" \
      --exclude='ai/.backups' ai/ 2>/dev/null || true
    # Keep only last 5 backups
    ls -1t "$backup_dir"/pre-sync-*.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm -f
    log "created pre-sync backup: $backup_name"
  fi
fi

run_sync_migrations "$TARGET_DIR"
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
install_recommended_structure "$TARGET_DIR" "$project_stack" "sync"
"$REPO_ROOT/bootstrap/apply_org_pack.sh" --target "$TARGET_DIR"
"$REPO_ROOT/bootstrap/sync_bulletins.sh" --target "$TARGET_DIR"
write_applied_lock "$TARGET_DIR" "$project_stack" "$selected_agents"
write_init_report "$TARGET_DIR" "sync" "$project_stack" "$selected_agents"

python3 "$REPO_ROOT/scripts/audit.py" --target "$TARGET_DIR" --action sync --details "stack=$project_stack agents=$selected_agents"
print_summary "sync" "$TARGET_DIR" "$project_stack" "$selected_agents" "$native_configs"
