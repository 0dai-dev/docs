#!/usr/bin/env python3
"""0dai Backstage Export — generate Backstage Software Templates from project layouts.

Exports project_layouts/ as Backstage-compatible template.yaml files
for use with Spotify Backstage developer portal.

Usage:
    python3 scripts/export_backstage.py --list
    python3 scripts/export_backstage.py --export <stack|all> [--output <dir>]
    python3 scripts/export_backstage.py --json
    0dai backstage-export --list|--export|--json
"""
from __future__ import annotations

import json
import pathlib
import sys
import textwrap

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
LAYOUTS_DIR = ROOT_DIR / "project_layouts"

STACK_META: dict[str, dict] = {
    "backend-api": {
        "title": "Backend API Service",
        "description": "Node.js or Python backend API with services, packages, and infrastructure",
        "tags": ["backend", "api", "node", "python"],
        "language": "typescript",
    },
    "data-ml": {
        "title": "Data & ML Pipeline",
        "description": "Data science and machine learning project with notebooks, pipelines, and model storage",
        "tags": ["python", "data-science", "ml", "jupyter"],
        "language": "python",
    },
    "fastapi": {
        "title": "FastAPI Service",
        "description": "Python FastAPI microservice with routes, models, schemas, and migrations",
        "tags": ["python", "fastapi", "api", "microservice"],
        "language": "python",
    },
    "flutter": {
        "title": "Flutter Application",
        "description": "Cross-platform Flutter app with packages and infrastructure",
        "tags": ["dart", "flutter", "mobile", "cross-platform"],
        "language": "dart",
    },
    "fullstack-monorepo": {
        "title": "Fullstack Monorepo",
        "description": "Monorepo with web frontend, API backend, shared packages, and infrastructure",
        "tags": ["typescript", "monorepo", "fullstack", "web"],
        "language": "typescript",
    },
    "go-service": {
        "title": "Go Service",
        "description": "Go backend service with cmd, internal packages, and migrations",
        "tags": ["go", "backend", "microservice"],
        "language": "go",
    },
    "nextjs": {
        "title": "Next.js Application",
        "description": "Next.js web application with app router, shared packages, and infrastructure",
        "tags": ["typescript", "nextjs", "react", "web"],
        "language": "typescript",
    },
    "python-service": {
        "title": "Python Service",
        "description": "Python backend service with API, packages, and infrastructure",
        "tags": ["python", "backend", "api"],
        "language": "python",
    },
    "react-native": {
        "title": "React Native Application",
        "description": "React Native mobile app with screens, navigation, and native modules",
        "tags": ["typescript", "react-native", "mobile"],
        "language": "typescript",
    },
}


def _generate_template(stack: str) -> str:
    """Generate a Backstage template.yaml for a given stack."""
    meta = STACK_META.get(stack, {
        "title": stack.replace("-", " ").title(),
        "description": f"{stack} project scaffold",
        "tags": [stack],
        "language": "unknown",
    })

    tags_yaml = "".join(f"    - {t}\n" for t in meta["tags"])

    return (
        "apiVersion: scaffolder.backstage.io/v1beta3\n"
        "kind: Template\n"
        "metadata:\n"
        f"  name: 0dai-{stack}\n"
        f'  title: "{meta["title"]} (0dai)"\n'
        f'  description: "{meta["description"]}"\n'
        "  tags:\n"
        f"{tags_yaml}"
        "    - 0dai\n"
        "  annotations:\n"
        "    backstage.io/techdocs-ref: dir:.\n"
        "spec:\n"
        "  owner: platform-team\n"
        "  type: service\n"
        "  parameters:\n"
        "    - title: Project Details\n"
        "      required:\n"
        "        - name\n"
        "        - owner\n"
        "      properties:\n"
        "        name:\n"
        "          title: Project Name\n"
        "          type: string\n"
        "          description: Unique name for the project\n"
        '          pattern: "^[a-z][a-z0-9-]{0,62}$"\n'
        "        owner:\n"
        "          title: Owner\n"
        "          type: string\n"
        "          description: Team or user that owns the project\n"
        "          ui:field: OwnerPicker\n"
        "        description:\n"
        "          title: Description\n"
        "          type: string\n"
        "          description: Brief description of the project\n"
        "    - title: AI Layer Configuration\n"
        "      properties:\n"
        "        ai_agents:\n"
        "          title: AI Agents\n"
        "          type: string\n"
        '          default: "codex,claude,opencode,gemini"\n'
        "          description: Comma-separated list of AI agent CLIs to configure\n"
        "        ai_preset:\n"
        "          title: Configuration Preset\n"
        "          type: string\n"
        "          default: standard\n"
        "          enum:\n"
        "            - minimal\n"
        "            - standard\n"
        "            - enterprise\n"
        "          description: 0dai configuration preset\n"
        "  steps:\n"
        "    - id: scaffold\n"
        "      name: Scaffold project\n"
        "      action: 0dai:init-new\n"
        "      input:\n"
        f"        stack: {stack}\n"
        "        name: ${{parameters.name}}\n"
        "        agents: ${{parameters.ai_agents}}\n"
        "    - id: configure\n"
        "      name: Configure AI layer\n"
        "      action: 0dai:configure\n"
        "      input:\n"
        "        preset: ${{parameters.ai_preset}}\n"
        "    - id: publish\n"
        "      name: Publish to GitHub\n"
        "      action: publish:github\n"
        "      input:\n"
        "        repoUrl: github.com?owner=${{parameters.owner}}&repo=${{parameters.name}}\n"
        "        description: ${{parameters.description}}\n"
        "        defaultBranch: main\n"
        "    - id: register\n"
        "      name: Register in catalog\n"
        "      action: catalog:register\n"
        "      input:\n"
        "        repoContentsUrl: ${{steps.publish.output.repoContentsUrl}}\n"
        "        catalogInfoPath: /catalog-info.yaml\n"
        "  output:\n"
        "    links:\n"
        "      - title: Repository\n"
        "        url: ${{steps.publish.output.remoteUrl}}\n"
        "      - title: Open in catalog\n"
        "        icon: catalog\n"
        "        entityRef: ${{steps.register.output.entityRef}}\n"
    )


def cmd_list() -> None:
    """List available layouts for Backstage export."""
    print(f"{'Stack':<25} {'Language':<12} Description")
    print("-" * 80)
    for stack in sorted(LAYOUTS_DIR.iterdir()):
        if not stack.is_dir():
            continue
        name = stack.name
        meta = STACK_META.get(name, {})
        lang = meta.get("language", "?")
        desc = meta.get("description", "")
        print(f"{name:<25} {lang:<12} {desc}")
    print(f"\n{len(list(LAYOUTS_DIR.iterdir()))} layout(s) available for export.")


def cmd_export(stack: str, output_dir: pathlib.Path) -> None:
    """Export one or all stacks as Backstage templates."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if stack == "all":
        stacks = [d.name for d in sorted(LAYOUTS_DIR.iterdir()) if d.is_dir()]
    else:
        if not (LAYOUTS_DIR / stack).is_dir():
            print(f"Stack '{stack}' not found in project_layouts/", file=sys.stderr)
            sys.exit(1)
        stacks = [stack]

    for s in stacks:
        template = _generate_template(s)
        stack_dir = output_dir / s
        stack_dir.mkdir(parents=True, exist_ok=True)
        (stack_dir / "template.yaml").write_text(template, encoding="utf-8")
        print(f"  Exported {s} → {stack_dir}/template.yaml")

    print(f"\n{len(stacks)} template(s) exported to {output_dir}/")


def cmd_json() -> None:
    """Output available templates as JSON."""
    templates = []
    for stack in sorted(LAYOUTS_DIR.iterdir()):
        if not stack.is_dir():
            continue
        meta = STACK_META.get(stack.name, {})
        templates.append({
            "stack": stack.name,
            "title": meta.get("title", stack.name),
            "description": meta.get("description", ""),
            "language": meta.get("language", "unknown"),
            "tags": meta.get("tags", []),
            "has_scaffold": (stack / "scaffold.sh").is_file(),
            "has_structure": (stack / "structure.md").is_file(),
        })

    print(json.dumps({"templates": templates, "count": len(templates)}, indent=2, ensure_ascii=False))


def main() -> None:
    subcmd = ""
    stack = "all"
    output_dir = ROOT_DIR / "backstage"
    args = sys.argv[1:]

    i = 0
    while i < len(args):
        if args[i] == "--list":
            subcmd = "list"
            i += 1
        elif args[i] == "--export" and i + 1 < len(args):
            subcmd = "export"
            stack = args[i + 1]
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_dir = pathlib.Path(args[i + 1]).resolve()
            i += 2
        elif args[i] == "--json":
            subcmd = "json"
            i += 1
        else:
            i += 1

    if subcmd == "list":
        cmd_list()
    elif subcmd == "export":
        cmd_export(stack, output_dir)
    elif subcmd == "json":
        cmd_json()
    else:
        print("Backstage Software Template export for 0dai project layouts.")
        print("  --list                 List available layouts")
        print("  --export <stack|all>   Export as Backstage templates")
        print("  --output <dir>         Output directory (default: backstage/)")
        print("  --json                 Output metadata as JSON")


if __name__ == "__main__":
    main()
