#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def fail(message: str) -> None:
    print(f"validation error: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def validate_json(file_path: pathlib.Path) -> None:
    with file_path.open("r", encoding="utf-8") as handle:
        json.load(handle)


def validate_native_output_map() -> None:
    map_path = ROOT / "bootstrap/native_output_map.json"
    mapping = json.loads(map_path.read_text(encoding="utf-8"))
    required = {
        "shared_agents_md",
        "claude_md",
        "codex_config",
        "claude_settings",
        "opencode_config",
        "shared_rules_dir",
        "codex_agents_dir",
        "claude_agents_dir",
        "claude_hooks_dir",
        "opencode_agents_dir",
        "skills_dir",
        "compatibility_root_dir",
        "compat_gitignore",
        "compat_mcp",
        "compat_ci_workflow",
    }
    require(required.issubset(mapping.keys()), "missing native output map keys")
    for rel_path in mapping.values():
        require((ROOT / rel_path).exists(), f"mapped path does not exist: {rel_path}")


def validate_devcontainer() -> None:
    require(
        (ROOT / "docker/ai-runner/Dockerfile").is_file(), "missing ai-runner Dockerfile"
    )
    require(
        (ROOT / "docker/ai-runner/entrypoint.sh").is_file(),
        "missing ai-runner entrypoint",
    )
    require(
        (ROOT / "docker/ai-runner/check-tools.sh").is_file(),
        "missing ai-runner check-tools script",
    )
    require((ROOT / "docker-compose.ai.yml").is_file(), "missing docker compose file")
    require(
        (ROOT / ".devcontainer/devcontainer.json").is_file(),
        "missing devcontainer config",
    )
    require((ROOT / ".dockerignore").is_file(), "missing dockerignore")
    require((ROOT / ".env.ai.example").is_file(), "missing environment example")
    require(
        (ROOT / "run/secrets/.gitkeep").is_file(), "missing run secrets placeholder"
    )


def validate_harvest() -> None:
    require(
        (ROOT / "bootstrap/harvest_experience.sh").is_file(), "missing harvest script"
    )
    require(
        (ROOT / "bootstrap/promote_experience.sh").is_file(), "missing promote script"
    )
    require((ROOT / "bin/0dai").is_file(), "missing 0dai wrapper")
    require((ROOT / "bin/0dai-repo").is_file(), "missing 0dai-repo wrapper")
    require((ROOT / "bin/0dai-task").is_file(), "missing 0dai-task wrapper")
    require((ROOT / "bin/ai-task").is_file(), "missing ai-task wrapper")
    require((ROOT / "bootstrap/doctor_target.sh").is_file(), "missing doctor script")
    require(
        (ROOT / "scripts/aggregate_experience.py").is_file(),
        "missing experience aggregator",
    )
    require(
        (ROOT / "scripts/prepare_knowledge_issue.py").is_file(),
        "missing knowledge intake preparer",
    )
    require(
        (ROOT / "scripts/score_knowledge_intake.py").is_file(),
        "missing knowledge intake scorer",
    )
    require(
        (ROOT / "scripts/create_knowledge_issue.py").is_file(),
        "missing knowledge issue creator",
    )


def validate_required_markers() -> None:
    managed_files = [
        ROOT / "templates/layer/ai/templates/shared/AGENTS.md.tmpl",
        ROOT / "templates/layer/ai/templates/shared/CLAUDE.md.tmpl",
        ROOT / "templates/layer/ai/templates/codex/config.toml.tmpl",
        ROOT / "templates/layer/ai/templates/claude/settings.json.tmpl",
        ROOT / "templates/layer/ai/templates/opencode/opencode.json.tmpl",
        ROOT / "templates/layer/ai/manifest/applied-lock.json",
        ROOT / "templates/layer/ai/manifest/commands.yaml",
        ROOT / "templates/layer/ai/manifest/project.yaml",
        ROOT / "templates/layer/ai/manifest/discovery.json",
        ROOT / "templates/layer/ai/manifest/init-report.md",
    ]
    for file_path in managed_files:
        text = file_path.read_text(encoding="utf-8")
        require("managed" in text, f"missing managed marker in {file_path}")


def validate_patterns() -> None:
    detector_names = set()
    for file_path in sorted(
        (ROOT / "templates/layer/ai/patterns/detectors").glob("*.yaml")
    ):
        text = file_path.read_text(encoding="utf-8")
        require("name:" in text, f"detector missing name: {file_path}")
        require("recommended_layout:" in text, f"detector missing layout: {file_path}")
        require("agents:" in text, f"detector missing agents: {file_path}")
        for line in text.splitlines():
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip()
                require(name not in detector_names, f"duplicate detector name: {name}")
                detector_names.add(name)

    expected_detectors = {
        "flutter",
        "node",
        "python",
        "nextjs",
        "python-service",
        "fullstack-monorepo",
        "go-service",
        "fastapi",
        "data-ml",
        "ops-dashboard",
        "react-native",
    }
    require(
        expected_detectors.issubset(detector_names),
        "missing expected detector definitions",
    )

    for file_path in sorted(
        (ROOT / "templates/layer/ai/patterns/stacks").glob("*.yaml")
    ):
        text = file_path.read_text(encoding="utf-8")
        require("name:" in text, f"stack missing name: {file_path}")
        require("stack:" in text, f"stack missing stack key: {file_path}")
        require("workflows:" in text, f"stack missing workflows: {file_path}")


def validate_layouts() -> None:
    for layout in [
        "backend-api",
        "flutter",
        "nextjs",
        "python-service",
        "fullstack-monorepo",
        "go-service",
        "fastapi",
        "data-ml",
        "react-native",
    ]:
        require(
            (ROOT / "project_layouts" / layout / "scaffold.sh").is_file(),
            f"missing scaffold for {layout}",
        )
        require(
            (ROOT / "project_layouts" / layout / "structure.md").is_file(),
            f"missing structure doc for {layout}",
        )


def main() -> None:
    validate_json(ROOT / "templates/root/.mcp.json")
    validate_json(ROOT / "bootstrap/native_output_map.json")
    validate_json(ROOT / "templates/layer/ai/templates/claude/settings.json.tmpl")
    validate_json(ROOT / "templates/layer/ai/templates/opencode/opencode.json.tmpl")
    validate_json(ROOT / "templates/layer/ai/templates/gemini/settings.json.tmpl")
    require(
        (ROOT / "templates/layer/ai/templates/aider/aider.conf.yml.tmpl").is_file(),
        "missing aider config template",
    )
    validate_json(ROOT / "templates/layer/ai/manifest/applied-lock.json")
    validate_json(ROOT / "templates/layer/ai/manifest/discovery.json")
    validate_required_markers()
    validate_native_output_map()
    validate_devcontainer()
    validate_harvest()
    validate_patterns()
    validate_layouts()
    require(
        (ROOT / ".github/ISSUE_TEMPLATE/bug_report.md").is_file(),
        "missing bug report template",
    )
    require(
        (ROOT / ".github/ISSUE_TEMPLATE/feature_request.md").is_file(),
        "missing feature request template",
    )
    require(
        (ROOT / ".github/PULL_REQUEST_TEMPLATE.md").is_file(),
        "missing pull request template",
    )
    require(
        (ROOT / ".github/ISSUE_TEMPLATE/ai_incident.yml").is_file(),
        "missing ai incident form",
    )
    require(
        (ROOT / ".github/ISSUE_TEMPLATE/ai_regression.yml").is_file(),
        "missing ai regression form",
    )
    require(
        (ROOT / ".github/ISSUE_TEMPLATE/ai_lesson.yml").is_file(),
        "missing ai lesson form",
    )
    require(
        (ROOT / ".github/ISSUE_TEMPLATE/ai_skill_candidate.yml").is_file(),
        "missing ai skill form",
    )
    require(
        (ROOT / ".github/ISSUE_TEMPLATE/ai_rule_candidate.yml").is_file(),
        "missing ai rule form",
    )
    require(
        (ROOT / "templates/layer/ai/skills-src/repo-review/SKILL.md").is_file(),
        "missing canonical repo-review skill",
    )
    require(
        (ROOT / "templates/layer/ai/agents-src/reviewer.yaml").is_file(),
        "missing canonical reviewer agent source",
    )
    require(
        (ROOT / "templates/layer/ai/agents-src/roadmap-guardian.yaml").is_file(),
        "missing canonical roadmap-guardian agent source",
    )
    require(
        (ROOT / "scripts/roadmap_guardian.py").is_file(),
        "missing roadmap guardian script",
    )
    require(
        (ROOT / "scripts/mcp_server.py").is_file(),
        "missing MCP server script",
    )
    require(
        (ROOT / "scripts/generate_telemetry.py").is_file(),
        "missing telemetry generator script",
    )
    require(
        (ROOT / "scripts/configure.py").is_file(),
        "missing configure wizard script",
    )
    require(
        (ROOT / "scripts/serve.py").is_file(),
        "missing web dashboard script",
    )
    require(
        (ROOT / "scripts/audit.py").is_file(),
        "missing audit logging script",
    )
    require(
        (ROOT / "scripts/search_experience.py").is_file(),
        "missing experience search script",
    )
    require(
        (ROOT / "scripts/federation.py").is_file(),
        "missing federation script",
    )
    require(
        (ROOT / "scripts/registry.py").is_file(),
        "missing registry script",
    )
    require(
        (ROOT / "scripts/generate_ide_configs.py").is_file(),
        "missing IDE config generator",
    )
    require(
        (ROOT / "templates/layer/ai/registry/index.json").is_file(),
        "missing registry index",
    )
    require(
        (ROOT / "scripts/maturity_score.py").is_file(),
        "missing maturity scorecard script",
    )
    require(
        (ROOT / "templates/layer/ai/registry/mcp-catalog.json").is_file(),
        "missing MCP catalog",
    )
    require(
        (ROOT / "sdk/zerodayai/__init__.py").is_file(),
        "missing Python SDK package",
    )
    require(
        (ROOT / "sdk/pyproject.toml").is_file(),
        "missing Python SDK pyproject.toml",
    )
    for persona in ["architect", "qa", "devops", "security"]:
        require(
            (ROOT / f"templates/layer/ai/personas/{persona}.yaml").is_file(),
            f"missing {persona} persona template",
        )
    require(
        (ROOT / "bootstrap/sync_bulletins.sh").is_file(),
        "missing bulletins sync script",
    )
    require(
        (ROOT / "templates/layer/ai/bulletins/2026-03-mcp-security.yaml").is_file(),
        "missing MCP security bulletin",
    )
    require(
        (ROOT / "scripts/analyze_codebase.py").is_file(),
        "missing codebase analyzer script",
    )
    require(
        (ROOT / "bootstrap/apply_org_pack.sh").is_file(),
        "missing org pack applier script",
    )
    require(
        (ROOT / "templates/layer/ai/packs/org/enterprise-default/1.0.0/pack.yaml").is_file(),
        "missing enterprise-default org pack",
    )
    require(
        (ROOT / "templates/layer/ai/VERSION_SCHEMA").is_file(),
        "missing ai schema version file",
    )
    require(
        (ROOT / "templates/layer/ai/manifest/commands.yaml").is_file(),
        "missing commands manifest template",
    )
    require(
        (ROOT / "templates/layer/ai/experience/README.md").is_file(),
        "missing experience readme",
    )
    require(
        (ROOT / "templates/layer/ai/experience/event-schema.json").is_file(),
        "missing experience event schema",
    )
    print("template validation passed")


if __name__ == "__main__":
    main()
