#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

python3 "$ROOT_DIR/scripts/validate_templates.py"

chmod +x \
  "$ROOT_DIR/bin/0dai" \
  "$ROOT_DIR/bin/0dai-repo" \
  "$ROOT_DIR/bin/ai-repo" \
  "$ROOT_DIR/bin/0dai-task" \
  "$ROOT_DIR/bin/ai-task" \
  "$ROOT_DIR/bootstrap/detect_env.sh" \
  "$ROOT_DIR/bootstrap/init_existing.sh" \
  "$ROOT_DIR/bootstrap/init_new.sh" \
  "$ROOT_DIR/bootstrap/sync_configs.sh" \
  "$ROOT_DIR/project_layouts/backend-api/scaffold.sh" \
  "$ROOT_DIR/project_layouts/flutter/scaffold.sh" \
  "$ROOT_DIR/project_layouts/nextjs/scaffold.sh" \
  "$ROOT_DIR/project_layouts/python-service/scaffold.sh" \
  "$ROOT_DIR/project_layouts/fullstack-monorepo/scaffold.sh" \
  "$ROOT_DIR/project_layouts/go-service/scaffold.sh" \
  "$ROOT_DIR/project_layouts/fastapi/scaffold.sh" \
  "$ROOT_DIR/project_layouts/data-ml/scaffold.sh" \
  "$ROOT_DIR/project_layouts/react-native/scaffold.sh" \
  "$ROOT_DIR/bootstrap/apply_org_pack.sh" \
  "$ROOT_DIR/bootstrap/sync_bulletins.sh" \
  "$ROOT_DIR/templates/layer/ai/bootstrap/hooks/session_start.sh" \
  "$ROOT_DIR/templates/layer/ai/bootstrap/hooks/pre_tool_use.sh" \
  "$ROOT_DIR/templates/layer/ai/bootstrap/hooks/run_tests.sh" \
  "$ROOT_DIR/templates/layer/ai/configs/claude/hooks/pre_plan.hook.sh" \
  "$ROOT_DIR/templates/layer/ai/configs/claude/hooks/post_apply.hook.sh"

EXISTING_DIR="$WORK_DIR/existing-node"
NEW_NEXT_DIR="$WORK_DIR/new-next"
NEW_PY_DIR="$WORK_DIR/new-python"
NEW_MONO_DIR="$WORK_DIR/new-mono"

mkdir -p "$EXISTING_DIR"
printf '{"name":"demo"}\n' > "$EXISTING_DIR/package.json"
printf '# Team Notes\n\nCustom AGENTS content.\n' > "$EXISTING_DIR/AGENTS.md"
mkdir -p "$EXISTING_DIR/.claude"
printf '# Local Claude Notes\n\nProject-specific Claude guidance.\n' > "$EXISTING_DIR/.claude/CLAUDE.md"

"$ROOT_DIR/bin/0dai" init-existing --target "$EXISTING_DIR"
printf '0.1.0\n' > "$EXISTING_DIR/ai/VERSION"
"$ROOT_DIR/bin/0dai" sync --target "$EXISTING_DIR"
"$ROOT_DIR/bin/0dai" doctor --target "$EXISTING_DIR" > "$EXISTING_DIR/doctor.txt"
test -f "$EXISTING_DIR/ai/manifest/audit.jsonl"
grep -q '"action": "sync"' "$EXISTING_DIR/ai/manifest/audit.jsonl"

test -f "$EXISTING_DIR/.codex/config.toml"
test -f "$EXISTING_DIR/.claude/settings.json"
test -f "$EXISTING_DIR/.claude/CLAUDE.md"
test -f "$EXISTING_DIR/opencode.json"
test -f "$EXISTING_DIR/.gemini/settings.json"
test -d "$EXISTING_DIR/.gemini/agents"
test -f "$EXISTING_DIR/.aider.conf.yml"
test -d "$EXISTING_DIR/.aider/agents"
grep -q "managed" "$EXISTING_DIR/.aider.conf.yml"
test -f "$EXISTING_DIR/.vscode/settings.json"
test -f "$EXISTING_DIR/.vscode/extensions.json"
test -f "$EXISTING_DIR/.idea/0dai.xml"
grep -q "filesystem" "$EXISTING_DIR/.mcp.json"
test -f "$EXISTING_DIR/ai/VERSION"
test -f "$EXISTING_DIR/ai/manifest/project.yaml"
test -f "$EXISTING_DIR/ai/manifest/discovery.json"
test -f "$EXISTING_DIR/ai/manifest/applied-lock.json"
test -f "$EXISTING_DIR/ai/manifest/codebase-map.json"
grep -q '"entry_points"' "$EXISTING_DIR/ai/manifest/codebase-map.json"
grep -q '"repo_mode"' "$EXISTING_DIR/ai/manifest/codebase-map.json"
grep -q '"import_graph"' "$EXISTING_DIR/ai/manifest/codebase-map.json"
grep -q '"files_with_imports"' "$EXISTING_DIR/ai/manifest/codebase-map.json"
test -f "$EXISTING_DIR/ai/manifest/commands.yaml"
grep -q "1.0.0" "$EXISTING_DIR/ai/VERSION"
grep -q '"channel": "stable"' "$EXISTING_DIR/ai/manifest/applied-lock.json"
grep -q 'sha256:' "$EXISTING_DIR/ai/manifest/applied-lock.json"
grep -q "tier:" "$EXISTING_DIR/ai/manifest/commands.yaml"
test -f "$EXISTING_DIR/ai/personas/architect.yaml"
test -f "$EXISTING_DIR/ai/personas/qa.yaml"
test -f "$EXISTING_DIR/ai/personas/security.yaml"
test -f "$EXISTING_DIR/ai/personas/devops.yaml"
grep -q "doctor=ok" "$EXISTING_DIR/doctor.txt"
grep -q "command=lint" "$EXISTING_DIR/doctor.txt"
grep -q "status=allowed" "$EXISTING_DIR/doctor.txt"
"$ROOT_DIR/bin/0dai" maturity --target "$EXISTING_DIR" --json > "$EXISTING_DIR/maturity.json"
grep -q '"score"' "$EXISTING_DIR/maturity.json"
grep -q '"grade"' "$EXISTING_DIR/maturity.json"
test -f "$EXISTING_DIR/.claude/agents/planner.md"
test -f "$EXISTING_DIR/.claude/agents/reviewer.md"
test -f "$EXISTING_DIR/.claude/agents/architect.md"
test -f "$EXISTING_DIR/.claude/agents/qa.md"
test -f "$EXISTING_DIR/.claude/agents/devops.md"
test -f "$EXISTING_DIR/.claude/agents/security.md"
grep -q "managed: true" "$EXISTING_DIR/.claude/agents/architect.md"
python3 "$ROOT_DIR/scripts/generate_agent_teams.py" --target "$EXISTING_DIR" --list | grep -q "architect"
python3 "$ROOT_DIR/scripts/generate_agent_teams.py" --target "$EXISTING_DIR" --json | grep -q '"installed"'
test -d "$EXISTING_DIR/.agents/skills"
grep -q "zerodayai:managed:begin" "$EXISTING_DIR/AGENTS.md"
grep -q "Custom AGENTS content" "$EXISTING_DIR/AGENTS.md"
grep -q "zerodayai:managed:begin" "$EXISTING_DIR/.claude/CLAUDE.md"
grep -q "Project-specific Claude guidance" "$EXISTING_DIR/.claude/CLAUDE.md"

"$ROOT_DIR/bin/0dai" task run --target "$EXISTING_DIR" --tool claude --task-type bugfix --summary "reset seeded fixtures before auth tests" --candidate-type skill --paths "services/api/**" -- bash -lc "exit 0"
"$ROOT_DIR/bin/0dai" harvest --target "$EXISTING_DIR"
test -f "$EXISTING_DIR/ai/experience/candidates/candidate.bugfix.reset-seeded-fixtures-before-auth-tests.md"
test -n "$(ls "$EXISTING_DIR/ai/experience/events"/*.json 2>/dev/null)"
"$ROOT_DIR/bin/0dai" promote --target "$EXISTING_DIR"
test -f "$EXISTING_DIR/ai/experience/accepted/skills/accepted.bugfix.reset-seeded-fixtures-before-auth-tests.md"
test ! -f "$EXISTING_DIR/ai/experience/candidates/candidate.bugfix.reset-seeded-fixtures-before-auth-tests.md"
cp "$ROOT_DIR/scripts/aggregate_experience.py" "$EXISTING_DIR/scripts-aggregate.py"
(cd "$EXISTING_DIR" && python3 "scripts-aggregate.py" >/dev/null)
test -f "$EXISTING_DIR/ai/experience/reports/0dai-experience-report.json"
cp "$ROOT_DIR/scripts/prepare_knowledge_issue.py" "$EXISTING_DIR/scripts-prepare-intake.py"
(cd "$EXISTING_DIR" && python3 "scripts-prepare-intake.py" >/dev/null)
test -f "$EXISTING_DIR/ai/experience/reports/0dai-knowledge-intake.json"
cp "$ROOT_DIR/scripts/score_knowledge_intake.py" "$EXISTING_DIR/scripts-score-intake.py"
(cd "$EXISTING_DIR" && python3 "scripts-score-intake.py" >/dev/null)
test -f "$EXISTING_DIR/ai/experience/reports/0dai-knowledge-intake-scored.json"
cp "$ROOT_DIR/scripts/create_knowledge_issue.py" "$EXISTING_DIR/scripts-create-issue.py"
(cd "$EXISTING_DIR" && python3 "scripts-create-issue.py" --dry-run >/dev/null)

MIGRATE_DIR="$WORK_DIR/migrate-chain"
mkdir -p "$MIGRATE_DIR"
printf '{"name":"migrate-test"}\n' > "$MIGRATE_DIR/package.json"
"$ROOT_DIR/bin/0dai" init-existing --target "$MIGRATE_DIR"
printf '0.1.0\n' > "$MIGRATE_DIR/ai/VERSION"
"$ROOT_DIR/bin/0dai" sync --target "$MIGRATE_DIR" > "$MIGRATE_DIR/sync.log" 2>&1
grep -q "running migration" "$MIGRATE_DIR/sync.log"
grep -q "pre-sync backup" "$MIGRATE_DIR/sync.log"
test -d "$MIGRATE_DIR/ai/.backups"
grep -q "1.0.0" "$MIGRATE_DIR/ai/VERSION"
test -f "$MIGRATE_DIR/ai/manifest/commands.yaml"

BULLETIN_DIR="$WORK_DIR/bulletin-test"
mkdir -p "$BULLETIN_DIR"
printf '{"name":"bulletin-demo"}\n' > "$BULLETIN_DIR/package.json"
"$ROOT_DIR/bin/0dai" init-existing --target "$BULLETIN_DIR"
"$ROOT_DIR/bin/0dai" pull-bulletins --target "$BULLETIN_DIR"
test -d "$BULLETIN_DIR/ai/bulletins"
test -f "$BULLETIN_DIR/ai/bulletins/2026-03-mcp-security.yaml"
"$ROOT_DIR/bin/0dai" report --dry-run > "$BULLETIN_DIR/telemetry-dry.txt" 2>&1
grep -q '"schema": 2' "$BULLETIN_DIR/telemetry-dry.txt"

CONFIG_DIR="$WORK_DIR/config-test"
mkdir -p "$CONFIG_DIR"
printf '{"name":"config-demo"}\n' > "$CONFIG_DIR/package.json"
"$ROOT_DIR/bin/0dai" init-existing --target "$CONFIG_DIR"
"$ROOT_DIR/bin/0dai" configure --target "$CONFIG_DIR" --preset standard
test -f "$CONFIG_DIR/ai/config/project-config.json"
grep -q '"preset": "standard"' "$CONFIG_DIR/ai/config/project-config.json"
test -f "$CONFIG_DIR/.mcp.json"

CUSTOM_STACK_DIR="$WORK_DIR/custom-stack-test"
mkdir -p "$CUSTOM_STACK_DIR/ai/stacks"
mkdir -p "$CUSTOM_STACK_DIR/myapp"
printf '{"name":"custom-demo"}\n' > "$CUSTOM_STACK_DIR/package.json"
cat > "$CUSTOM_STACK_DIR/ai/stacks/mystack.yaml" <<'YAML'
name: my-custom-stack
priority: 1
match_primary:
  - myapp/
match_any:
  - package.json
recommended_layout: custom
agents:
  - claude
YAML
detected="$("$ROOT_DIR/bin/0dai" detect --target "$CUSTOM_STACK_DIR" | grep '^stack=' | cut -d= -f2)"
test "$detected" = "my-custom-stack"

FED_A="$WORK_DIR/fed-a"
FED_B="$WORK_DIR/fed-b"
mkdir -p "$FED_A" "$FED_B"
printf '{"name":"fed-a"}\n' > "$FED_A/package.json"
printf '{"name":"fed-b"}\n' > "$FED_B/package.json"
"$ROOT_DIR/bin/0dai" init-existing --target "$FED_A"
"$ROOT_DIR/bin/0dai" init-existing --target "$FED_B"
mkdir -p "$FED_B/ai/experience/accepted/rules"
printf '# shared rule from fed-b\n' > "$FED_B/ai/experience/accepted/rules/shared-rule.md"
mkdir -p ~/.0dai
printf '{"token_id":"tok_test","user":"test@test.com","team":"Test","plan":"team","seats":10,"authenticated_at":"2026-03-29","expires_at":"2099-12-31T23:59:59+00:00"}\n' > ~/.0dai/auth.json
"$ROOT_DIR/bin/0dai" federation --target "$FED_A" --add "$FED_B"
test -f "$FED_A/ai/federation.yaml"
"$ROOT_DIR/bin/0dai" federation --target "$FED_A" --sync
test -f "$FED_A/ai/experience/federated/fed-b/rules/shared-rule.md"

POLICY_DIR="$WORK_DIR/policy-test"
REG_DIR="$WORK_DIR/registry-test"
mkdir -p "$REG_DIR"
printf '{"name":"reg-demo"}\n' > "$REG_DIR/package.json"
"$ROOT_DIR/bin/0dai" init-existing --target "$REG_DIR"
"$ROOT_DIR/bin/0dai" registry --install django --target "$REG_DIR"
test -f "$REG_DIR/ai/stacks/django.yaml"
grep -q "manage.py" "$REG_DIR/ai/stacks/django.yaml"

POLICY_DIR="$WORK_DIR/policy-test"
mkdir -p "$POLICY_DIR"
printf '{"name":"policy-demo"}\n' > "$POLICY_DIR/package.json"
"$ROOT_DIR/bin/0dai" init-existing --target "$POLICY_DIR"
"$ROOT_DIR/bin/0dai" apply-policy --target "$POLICY_DIR" --pack enterprise-default
test -f "$POLICY_DIR/ai/packs/org/enterprise-default/1.0.0/pack.yaml"
test -f "$POLICY_DIR/ai/manifest/org-policy.json"
grep -q "enterprise-default" "$POLICY_DIR/ai/manifest/org-policy.json"

DETECT_FAPI="$WORK_DIR/detect-fastapi"
mkdir -p "$DETECT_FAPI/app/api"
printf '[project]\nname = "demo"\n' > "$DETECT_FAPI/pyproject.toml"
printf 'from fastapi import FastAPI\n' > "$DETECT_FAPI/app/main.py"
detected="$("$ROOT_DIR/bin/0dai" detect --target "$DETECT_FAPI" | grep '^stack=' | cut -d= -f2)"
test "$detected" = "fastapi"

DETECT_GO="$WORK_DIR/detect-go"
mkdir -p "$DETECT_GO/cmd"
printf 'module demo\ngo 1.22\n' > "$DETECT_GO/go.mod"
detected="$("$ROOT_DIR/bin/0dai" detect --target "$DETECT_GO" | grep '^stack=' | cut -d= -f2)"
test "$detected" = "go-service"

"$ROOT_DIR/bin/0dai" init-new --stack nextjs --target "$NEW_NEXT_DIR"
test -f "$NEW_NEXT_DIR/next.config.js"
test -d "$NEW_NEXT_DIR/apps/web/app"
test -f "$NEW_NEXT_DIR/.claude/CLAUDE.md"
test -f "$NEW_NEXT_DIR/ai/manifest/project.yaml"
test -f "$NEW_NEXT_DIR/ai/manifest/applied-lock.json"
test -f "$NEW_NEXT_DIR/ai/manifest/commands.yaml"

"$ROOT_DIR/bin/0dai" init-new --stack python-service --target "$NEW_PY_DIR"
test -f "$NEW_PY_DIR/pyproject.toml"
test -d "$NEW_PY_DIR/services/api/src"

"$ROOT_DIR/bin/0dai" init-new --stack fullstack-monorepo --target "$NEW_MONO_DIR"
test -d "$NEW_MONO_DIR/apps/web/app"
test -d "$NEW_MONO_DIR/services/api/src"

NEW_GO_DIR="$WORK_DIR/new-go"
"$ROOT_DIR/bin/0dai" init-new --stack go-service --target "$NEW_GO_DIR"
test -f "$NEW_GO_DIR/go.mod"
test -f "$NEW_GO_DIR/cmd/server/main.go"
test -d "$NEW_GO_DIR/internal/handler"
test -f "$NEW_GO_DIR/ai/manifest/project.yaml"
test -f "$NEW_GO_DIR/ai/manifest/commands.yaml"

NEW_FAPI_DIR="$WORK_DIR/new-fastapi"
"$ROOT_DIR/bin/0dai" init-new --stack fastapi --target "$NEW_FAPI_DIR"
test -f "$NEW_FAPI_DIR/pyproject.toml"
test -f "$NEW_FAPI_DIR/app/main.py"
test -d "$NEW_FAPI_DIR/app/api/routes"
test -f "$NEW_FAPI_DIR/ai/manifest/project.yaml"

NEW_ML_DIR="$WORK_DIR/new-data-ml"
"$ROOT_DIR/bin/0dai" init-new --stack data-ml --target "$NEW_ML_DIR"
test -d "$NEW_ML_DIR/notebooks"
test -d "$NEW_ML_DIR/src/pipelines"
test -d "$NEW_ML_DIR/data/raw"
test -f "$NEW_ML_DIR/pyproject.toml"
test -f "$NEW_ML_DIR/ai/manifest/project.yaml"

NEW_RN_DIR="$WORK_DIR/new-react-native"
"$ROOT_DIR/bin/0dai" init-new --stack react-native --target "$NEW_RN_DIR"
test -f "$NEW_RN_DIR/app.json"
test -f "$NEW_RN_DIR/metro.config.js"
test -d "$NEW_RN_DIR/src/screens"
test -d "$NEW_RN_DIR/src/navigation"
test -f "$NEW_RN_DIR/ai/manifest/project.yaml"

SPEC_DIR="$WORK_DIR/spec-test"
mkdir -p "$SPEC_DIR"
printf '{"name":"spec-demo"}\n' > "$SPEC_DIR/package.json"
"$ROOT_DIR/bin/0dai" init-existing --target "$SPEC_DIR"
test -d "$SPEC_DIR/ai/specs"
test -f "$SPEC_DIR/ai/specs/README.md"
test -f "$SPEC_DIR/ai/specs/TEMPLATE.md"
python3 "$ROOT_DIR/scripts/manage_specs.py" --target "$SPEC_DIR" --new add-auth --title "Add Authentication" --priority high --agent architect
test -f "$SPEC_DIR/ai/specs/SPEC-001-add-auth.md"
grep -q "SPEC-001" "$SPEC_DIR/ai/specs/SPEC-001-add-auth.md"
grep -q "Add Authentication" "$SPEC_DIR/ai/specs/SPEC-001-add-auth.md"
python3 "$ROOT_DIR/scripts/manage_specs.py" --target "$SPEC_DIR" --list | grep -q "SPEC-001"
python3 "$ROOT_DIR/scripts/manage_specs.py" --target "$SPEC_DIR" --validate
python3 "$ROOT_DIR/scripts/manage_specs.py" --target "$SPEC_DIR" --json | grep -q '"total"'

BACKSTAGE_DIR="$WORK_DIR/backstage-test"
python3 "$ROOT_DIR/scripts/export_backstage.py" --export all --output "$BACKSTAGE_DIR"
test -f "$BACKSTAGE_DIR/fastapi/template.yaml"
test -f "$BACKSTAGE_DIR/nextjs/template.yaml"
test -f "$BACKSTAGE_DIR/go-service/template.yaml"
grep -q "scaffolder.backstage.io" "$BACKSTAGE_DIR/fastapi/template.yaml"
grep -q "0dai-fastapi" "$BACKSTAGE_DIR/fastapi/template.yaml"
python3 "$ROOT_DIR/scripts/export_backstage.py" --list | grep -q "fastapi"
python3 "$ROOT_DIR/scripts/export_backstage.py" --json | grep -q '"count"'

python3 "$ROOT_DIR/scripts/generate_changelog.py" --from v0.3.3 --version test | grep -q "## vtest"
python3 "$ROOT_DIR/scripts/generate_changelog.py" --json --from v0.3.3 | grep -q '"total_commits"'
set +o pipefail
python3 "$ROOT_DIR/scripts/release_auditor.py" --json 2>/dev/null | grep -q '"ready"'
python3 "$ROOT_DIR/scripts/detect_doc_drift.py" --json 2>/dev/null | grep -q '"drift_detected"'
set -o pipefail

python3 "$ROOT_DIR/scripts/generate_orchestration.py" --list | grep -q "architect"
python3 "$ROOT_DIR/scripts/generate_orchestration.py" --json | grep -q '"squad"'
python3 "$ROOT_DIR/scripts/generate_orchestration.py" --json | grep -q '"swarm"'
ORCH_DIR="$WORK_DIR/orch-test"
mkdir -p "$ORCH_DIR"
printf '{"name":"orch-demo"}\n' > "$ORCH_DIR/package.json"
"$ROOT_DIR/bin/0dai" init-existing --target "$ORCH_DIR"
python3 "$ROOT_DIR/scripts/generate_orchestration.py" --target "$ORCH_DIR"
test -f "$ORCH_DIR/ai/orchestration/squad.yaml"
test -f "$ORCH_DIR/ai/orchestration/swarm.yaml"
grep -q "lead" "$ORCH_DIR/ai/orchestration/squad.yaml"
grep -q "orchestrator" "$ORCH_DIR/ai/orchestration/swarm.yaml"

python3 "$ROOT_DIR/scripts/score_experience.py" --target "$EXISTING_DIR" --json | grep -q '"total_candidates"'

python3 "$ROOT_DIR/scripts/generate_observability.py" --list | grep -q "OpenTelemetry"
python3 "$ROOT_DIR/scripts/generate_observability.py" --json | grep -q '"recommended"'
OBS_DIR="$WORK_DIR/obs-test"
mkdir -p "$OBS_DIR"
printf '{"name":"obs-demo"}\n' > "$OBS_DIR/package.json"
"$ROOT_DIR/bin/0dai" init-existing --target "$OBS_DIR"
python3 "$ROOT_DIR/scripts/generate_observability.py" --target "$OBS_DIR"
test -f "$OBS_DIR/ai/observability/.env.observability.template"
test -f "$OBS_DIR/ai/observability/recommendations.json"

python3 "$ROOT_DIR/scripts/prompt_versioning.py" --target "$EXISTING_DIR"
test -f "$EXISTING_DIR/ai/prompts/.history.json"
python3 "$ROOT_DIR/scripts/prompt_versioning.py" --target "$EXISTING_DIR" --status | grep -q "snapshot"
python3 "$ROOT_DIR/scripts/prompt_versioning.py" --target "$EXISTING_DIR" --json | grep -q '"current_prompts"'

python3 "$ROOT_DIR/scripts/wal.py" --target "$EXISTING_DIR" --json | grep -q '"entries"'

# Auth token already set above for team features

KB_DIR="$WORK_DIR/shared-kb"
python3 "$ROOT_DIR/scripts/knowledge_base.py" --target "$EXISTING_DIR" init --kb-path "$KB_DIR"
test -d "$KB_DIR/rules"
test -d "$KB_DIR/skills"
test -f "$KB_DIR/meta/kb.json"
test -f "$EXISTING_DIR/ai/manifest/knowledge-base.json"
python3 "$ROOT_DIR/scripts/knowledge_base.py" --target "$EXISTING_DIR" push
python3 "$ROOT_DIR/scripts/knowledge_base.py" --target "$EXISTING_DIR" --json | grep -q '"connected": true'

python3 "$ROOT_DIR/scripts/activity_feed.py" --target "$EXISTING_DIR" --json | grep -q '"activities"'

python3 "$ROOT_DIR/scripts/role_policy.py" --target "$EXISTING_DIR" init
test -f "$EXISTING_DIR/ai/manifest/role-policy.json"
python3 "$ROOT_DIR/scripts/role_policy.py" --target "$EXISTING_DIR" set testuser developer
python3 "$ROOT_DIR/scripts/role_policy.py" --target "$EXISTING_DIR" check testuser safe
python3 "$ROOT_DIR/scripts/role_policy.py" --target "$EXISTING_DIR" --json | grep -q '"assignments"'

python3 "$ROOT_DIR/scripts/conflict_resolver.py" --target "$EXISTING_DIR" --branch main --json | grep -q '"conflicts"'

python3 "$ROOT_DIR/scripts/landing.py" --help | grep -q "landing"
python3 "$ROOT_DIR/scripts/auth.py" status | grep -q "active"
python3 "$ROOT_DIR/scripts/auth.py" --json | grep -q '"authenticated": true'

POLICY_ENGINE_DIR="$WORK_DIR/org-policies"
python3 "$ROOT_DIR/scripts/policy_push.py" --policy-dir "$POLICY_ENGINE_DIR" init
test -f "$POLICY_ENGINE_DIR/packs/org-default.yaml"
test -f "$POLICY_ENGINE_DIR/rules/no-secrets-in-code.md"
python3 "$ROOT_DIR/scripts/policy_push.py" --policy-dir "$POLICY_ENGINE_DIR" add-repo "$EXISTING_DIR"
python3 "$ROOT_DIR/scripts/policy_push.py" --policy-dir "$POLICY_ENGINE_DIR" push
test -f "$EXISTING_DIR/ai/manifest/org-policy.json"
grep -q "org-default" "$EXISTING_DIR/ai/manifest/org-policy.json"
python3 "$ROOT_DIR/scripts/policy_push.py" --policy-dir "$POLICY_ENGINE_DIR" --json > "$WORK_DIR/policy-out.json"
grep -q '"repos"' "$WORK_DIR/policy-out.json"

python3 "$ROOT_DIR/scripts/compliance_report.py" --target "$EXISTING_DIR" --json > "$WORK_DIR/compliance-soc2.json"
grep -q '"evidenced"' "$WORK_DIR/compliance-soc2.json"
python3 "$ROOT_DIR/scripts/compliance_report.py" --target "$EXISTING_DIR" --framework iso27001 --json > "$WORK_DIR/compliance-iso.json"
grep -q 'ISO 27001' "$WORK_DIR/compliance-iso.json"

python3 "$ROOT_DIR/scripts/session_manager.py" --target "$EXISTING_DIR" save --summary "test session"
test -f "$EXISTING_DIR/ai/sessions/active.json"
python3 "$ROOT_DIR/scripts/session_manager.py" --target "$EXISTING_DIR" --json | grep -q '"has_active": true'
python3 "$ROOT_DIR/scripts/session_manager.py" --target "$EXISTING_DIR" complete
test ! -f "$EXISTING_DIR/ai/sessions/active.json"
test -d "$EXISTING_DIR/ai/sessions/archive"

python3 "$ROOT_DIR/scripts/scan_secrets.py" --target "$EXISTING_DIR" --json > "$WORK_DIR/scan-out.json"
grep -q '"findings"' "$WORK_DIR/scan-out.json"
grep -q '"clean"' "$WORK_DIR/scan-out.json"

python3 "$ROOT_DIR/scripts/approval_workflow.py" --target "$EXISTING_DIR" check --command "deploy"
python3 "$ROOT_DIR/scripts/approval_workflow.py" --target "$EXISTING_DIR" request --command "deploy"
python3 "$ROOT_DIR/scripts/approval_workflow.py" --target "$EXISTING_DIR" --json > "$WORK_DIR/approvals.json"
grep -q '"pending"' "$WORK_DIR/approvals.json"

python3 "$ROOT_DIR/scripts/plugin_manager.py" --target "$EXISTING_DIR" init test-plugin
test -f "$EXISTING_DIR/ai/plugins/test-plugin/plugin.json"
test -f "$EXISTING_DIR/ai/plugins/test-plugin/run.sh"
python3 "$ROOT_DIR/scripts/plugin_manager.py" --target "$EXISTING_DIR" validate
python3 "$ROOT_DIR/scripts/plugin_manager.py" --target "$EXISTING_DIR" --json > "$WORK_DIR/plugins.json"
grep -q '"test-plugin"' "$WORK_DIR/plugins.json"

python3 "$ROOT_DIR/scripts/team_manager.py" members
python3 "$ROOT_DIR/scripts/team_manager.py" --json > "$WORK_DIR/team.json"
grep -q '"members"' "$WORK_DIR/team.json"

python3 "$ROOT_DIR/scripts/billing.py" status
python3 "$ROOT_DIR/scripts/billing.py" create-key --name test-key
python3 "$ROOT_DIR/scripts/billing.py" --json > "$WORK_DIR/billing.json"
grep -q '"api_keys"' "$WORK_DIR/billing.json"

python3 "$ROOT_DIR/scripts/webhooks.py" --target "$EXISTING_DIR" add "https://example.com/hook" --events "init,sync"
python3 "$ROOT_DIR/scripts/webhooks.py" --target "$EXISTING_DIR" --json > "$WORK_DIR/webhooks.json"
grep -q '"hooks"' "$WORK_DIR/webhooks.json"
grep -q 'example.com' "$WORK_DIR/webhooks.json"

printf 'smoke test passed\n'
