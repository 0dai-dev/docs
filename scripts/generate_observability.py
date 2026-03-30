#!/usr/bin/env python3
"""0dai Observability Template Generator — tracing configs per stack.

Generates agent tracing configurations for Langfuse, OpenTelemetry, and
LangSmith based on the detected project stack.

Usage:
    python3 scripts/generate_observability.py --target <path>
    python3 scripts/generate_observability.py --target <path> --provider langfuse
    python3 scripts/generate_observability.py --target <path> --list
    python3 scripts/generate_observability.py --target <path> --json
    0dai observability --target <path>
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT_DIR / "templates" / "layer" / "ai" / "registry" / "observability-catalog.json"


def _load_catalog() -> dict:
    if not CATALOG_PATH.is_file():
        return {"providers": {}, "stacks": {}}
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _detect_stack(target: pathlib.Path) -> str:
    discovery = target / "ai" / "manifest" / "discovery.json"
    if discovery.is_file():
        try:
            data = json.loads(discovery.read_text(encoding="utf-8"))
            return data.get("stack", "generic")
        except (json.JSONDecodeError, OSError):
            pass
    return "generic"


def get_recommendations(target: pathlib.Path) -> dict:
    """Get observability recommendations for the project's stack."""
    catalog = _load_catalog()
    stack = _detect_stack(target)

    providers = catalog.get("providers", {})
    stack_config = catalog.get("stacks", {}).get(stack, {})

    if not stack_config:
        # Fallback to generic recommendations
        stack_config = {
            "recommended": ["opentelemetry"],
            "packages": {"opentelemetry": "(see provider docs)"},
        }

    recommended = stack_config.get("recommended", [])
    packages = stack_config.get("packages", {})

    results = []
    for name in recommended:
        provider = providers.get(name, {})
        results.append({
            "provider": name,
            "name": provider.get("name", name),
            "description": provider.get("description", ""),
            "env_vars": provider.get("env_vars", []),
            "packages": packages.get(name, ""),
            "docs": provider.get("docs", ""),
        })

    return {
        "stack": stack,
        "recommended": results,
        "all_providers": list(providers.keys()),
    }


def generate_env_template(target: pathlib.Path, provider: str | None = None) -> dict:
    """Generate .env.observability template with required env vars."""
    catalog = _load_catalog()
    providers = catalog.get("providers", {})

    if provider:
        selected = {provider: providers.get(provider, {})}
    else:
        stack = _detect_stack(target)
        stack_config = catalog.get("stacks", {}).get(stack, {})
        recommended = stack_config.get("recommended", ["opentelemetry"])
        selected = {name: providers.get(name, {}) for name in recommended}

    lines = [
        "# managed: true",
        "# 0dai observability environment template",
        f"# Generated: {time.strftime('%Y-%m-%d')}",
        f"# Stack: {_detect_stack(target)}",
        "",
    ]

    for name, prov in selected.items():
        lines.append(f"# --- {prov.get('name', name)} ---")
        lines.append(f"# Docs: {prov.get('docs', '')}")
        for var in prov.get("env_vars", []):
            lines.append(f"# {var}=")
        lines.append("")

    content = "\n".join(lines)

    obs_dir = target / "ai" / "observability"
    obs_dir.mkdir(parents=True, exist_ok=True)
    env_path = obs_dir / ".env.observability.template"
    env_path.write_text(content, encoding="utf-8")

    # Also write provider recommendations
    rec = get_recommendations(target)
    rec_path = obs_dir / "recommendations.json"
    rec_path.write_text(
        json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return {
        "env_template": str(env_path.relative_to(target)),
        "recommendations": str(rec_path.relative_to(target)),
        "providers": list(selected.keys()),
        "stack": _detect_stack(target),
    }


def cmd_list(target: pathlib.Path) -> None:
    """List available observability providers."""
    rec = get_recommendations(target)

    print(f"Stack: {rec['stack']}")
    print(f"\nRecommended providers:")
    for r in rec["recommended"]:
        pkgs = r["packages"] if r["packages"] else "(see docs)"
        print(f"  {r['name']:<20} {r['description'][:55]}")
        print(f"  {'':20} Packages: {pkgs}")
        print(f"  {'':20} Env vars: {', '.join(r['env_vars'])}")
        print()

    other = [p for p in rec["all_providers"] if p not in [r["provider"] for r in rec["recommended"]]]
    if other:
        print(f"Other available: {', '.join(other)}")


def cmd_json(target: pathlib.Path) -> None:
    """Output recommendations as JSON."""
    print(json.dumps(get_recommendations(target), indent=2, ensure_ascii=False))


def cmd_generate(target: pathlib.Path, provider: str | None = None) -> None:
    """Generate observability templates."""
    result = generate_env_template(target, provider)
    print(f"Generated observability configs for stack '{result['stack']}':")
    print(f"  Env template: {result['env_template']}")
    print(f"  Recommendations: {result['recommendations']}")
    print(f"  Providers: {', '.join(result['providers'])}")


def main() -> None:
    target = pathlib.Path(".")
    subcmd = "generate"
    provider = None
    args = sys.argv[1:]

    i = 0
    while i < len(args):
        if args[i] == "--target" and i + 1 < len(args):
            target = pathlib.Path(args[i + 1]).resolve()
            i += 2
        elif args[i] == "--provider" and i + 1 < len(args):
            provider = args[i + 1]
            i += 2
        elif args[i] == "--list":
            subcmd = "list"
            i += 1
        elif args[i] == "--json":
            subcmd = "json"
            i += 1
        else:
            i += 1

    if subcmd == "list":
        cmd_list(target)
    elif subcmd == "json":
        cmd_json(target)
    else:
        cmd_generate(target, provider)


if __name__ == "__main__":
    main()
