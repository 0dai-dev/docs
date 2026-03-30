#!/usr/bin/env python3
"""0dai Public Repo Guardian — controls what files go to the public repo.

Ensures only approved files are synced from private to
public (0dai-dev/0dai) repo. Blocks sensitive files from leaking.

Usage:
    python3 scripts/sync_public_repo.py --check         # dry-run: show what would sync
    python3 scripts/sync_public_repo.py --sync           # actually sync to public repo
    python3 scripts/sync_public_repo.py --diff           # show diff between repos
"""
from __future__ import annotations

import pathlib
import shutil
import sys

PRIVATE_ROOT = pathlib.Path(__file__).resolve().parent.parent
PUBLIC_ROOT = pathlib.Path("/tmp/0dai-public")

# ═══ ALLOWLIST: files/dirs that go to public repo ═══
ALLOWED_DIRS = {
    "bin",
    "bootstrap",
    "templates",
    "sdk",
    "tests",
    "docs",
    "project_layouts",
    "docker",
    "release-notes",
    ".github",
}

ALLOWED_SCRIPTS = {
    "mcp_server.py",
    "session_manager.py",
    "score_experience.py",
    "generate_orchestration.py",
    "generate_observability.py",
    "scan_secrets.py",
    "registry.py",
    "generate_agent_teams.py",
    "generate_ide_configs.py",
    "generate_changelog.py",
    "manage_specs.py",
    "prompt_versioning.py",
    "wal.py",
    "search_experience.py",
    "aggregate_experience.py",
    "prepare_knowledge_issue.py",
    "score_knowledge_intake.py",
    "create_knowledge_issue.py",
    "generate_telemetry.py",
    "configure.py",
    "detect_doc_drift.py",
    "test_stack_compat.py",
    "release_auditor.py",
    "export_backstage.py",
    "maturity_score.py",
    "audit.py",
    "validate_templates.py",
    "roadmap_guardian.py",
    "_error_handler.py",
    "plugin_manager.py",
    "webhooks.py",
    "sync_public_repo.py",
}

ALLOWED_ROOT_FILES = {
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "AGENTS.md",
    "VERSION",
    "VERSION_SCHEMA",
    ".gitignore",
    ".mcp.json",
    "docker-compose.ai.yml",
    "LICENSE",
}

# ═══ BLOCKLIST: files that must NEVER go to public repo ═══
BLOCKED_SCRIPTS = {
    "landing.py",
    "install.sh",
    "auth.py",
    "billing.py",
    "team_manager.py",
    "knowledge_base.py",
    "activity_feed.py",
    "role_policy.py",
    "conflict_resolver.py",
    "federation.py",
    "compliance_report.py",
    "policy_push.py",
    "approval_workflow.py",
    "serve.py",
    "license.py",
}

BLOCKED_DIRS = {
    "services",       # Supabase backend
    "memory-bank",    # Internal project memory
}

BLOCKED_PATTERNS = {
    ".env",
    ".env.ai",
    "auth.json",
    "license.json",
    "billing.json",
    "api_keys.json",
    "team.json",
}


def check_file(rel_path: str) -> str:
    """Returns 'allow', 'block', or 'skip' for a given relative path."""
    parts = pathlib.Path(rel_path).parts

    # Root files
    if len(parts) == 1:
        if parts[0] in ALLOWED_ROOT_FILES:
            return "allow"
        if parts[0] in BLOCKED_PATTERNS:
            return "block"
        return "skip"

    # Check blocked dirs first
    if parts[0] in BLOCKED_DIRS:
        return "block"

    # Check allowed dirs
    if parts[0] in ALLOWED_DIRS:
        return "allow"

    # Scripts
    if parts[0] == "scripts":
        fname = parts[-1]
        if fname in BLOCKED_SCRIPTS:
            return "block"
        if fname in ALLOWED_SCRIPTS:
            return "allow"
        return "skip"

    return "skip"


def scan_private_repo() -> dict:
    """Scan private repo and classify all files."""
    results = {"allow": [], "block": [], "skip": []}
    for path in sorted(PRIVATE_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if ".git/" in str(path) or "/.git/" in str(path):
            continue
        rel = str(path.relative_to(PRIVATE_ROOT))
        status = check_file(rel)
        results[status].append(rel)
    return results


def cmd_check() -> None:
    """Dry-run: show what would sync."""
    results = scan_private_repo()
    print(f"Public Repo Guardian — Dry Run")
    print(f"")
    print(f"  ALLOW ({len(results['allow'])} files) — will sync to public repo")
    print(f"  BLOCK ({len(results['block'])} files) — NEVER synced (sensitive)")
    print(f"  SKIP  ({len(results['skip'])} files) — not in allowlist")
    print(f"")

    if results["block"]:
        print(f"  BLOCKED files:")
        for f in results["block"]:
            print(f"    ✗ {f}")
        print()

    if results["skip"]:
        print(f"  SKIPPED files (not in allowlist):")
        for f in results["skip"][:20]:
            print(f"    ? {f}")
        if len(results["skip"]) > 20:
            print(f"    ... and {len(results['skip']) - 20} more")


def cmd_sync() -> None:
    """Sync allowed files to public repo clone."""
    if not PUBLIC_ROOT.is_dir():
        print(f"Error: public repo not found at {PUBLIC_ROOT}")
        print(f"  Clone first: git clone https://github.com/0dai-dev/0dai /tmp/0dai-public")
        sys.exit(1)

    results = scan_private_repo()
    synced = 0

    for rel in results["allow"]:
        src = PRIVATE_ROOT / rel
        dst = PUBLIC_ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        synced += 1

    print(f"[0dai] synced {synced} files to public repo")
    print(f"[0dai] blocked {len(results['block'])} sensitive files")
    print(f"")
    print(f"  Next: cd {PUBLIC_ROOT} && git add -A && git commit && git push")


def cmd_diff() -> None:
    """Show files in private but not in public."""
    if not PUBLIC_ROOT.is_dir():
        print(f"Public repo not at {PUBLIC_ROOT}")
        return

    private_files = set()
    for path in PRIVATE_ROOT.rglob("*"):
        if path.is_file() and ".git/" not in str(path):
            private_files.add(str(path.relative_to(PRIVATE_ROOT)))

    public_files = set()
    for path in PUBLIC_ROOT.rglob("*"):
        if path.is_file() and ".git/" not in str(path):
            public_files.add(str(path.relative_to(PUBLIC_ROOT)))

    only_private = private_files - public_files
    only_public = public_files - private_files

    print(f"Only in private ({len(only_private)}):")
    for f in sorted(only_private)[:30]:
        status = check_file(f)
        marker = "✗" if status == "block" else "?" if status == "skip" else "+"
        print(f"  {marker} {f}")

    if only_public:
        print(f"\nOnly in public ({len(only_public)}):")
        for f in sorted(only_public):
            print(f"  {f}")


def main():
    if "--sync" in sys.argv:
        cmd_sync()
    elif "--diff" in sys.argv:
        cmd_diff()
    else:
        cmd_check()


if __name__ == "__main__":
    main()
