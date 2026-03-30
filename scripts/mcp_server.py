#!/usr/bin/env python3
"""0dai MCP Server — expose project AI layer as MCP tools.

Agents can query manifests, codebase maps, org policies, experience,
and command tiers through the Model Context Protocol.

Usage:
    python3 scripts/mcp_server.py                        # stdio (default)
    python3 scripts/mcp_server.py --target /path          # specific project
    python3 scripts/mcp_server.py --http                  # Streamable HTTP on 127.0.0.1:8421
    python3 scripts/mcp_server.py --multi /a /b /c        # multi-tenant: serve multiple projects
    0dai mcp --target /path                               # via CLI (stdio)
    0dai mcp --target /path --http                        # via CLI (HTTP)
"""
from __future__ import annotations

import json
import pathlib
import sys

from fastmcp import FastMCP

TARGET_DIR = pathlib.Path(".")
HTTP_MODE = False
HTTP_HOST = "127.0.0.1"
HTTP_PORT = 8421
MULTI_TENANT = False
TENANT_DIRS: dict[str, pathlib.Path] = {}

for i, arg in enumerate(sys.argv):
    if arg == "--target" and i + 1 < len(sys.argv):
        TARGET_DIR = pathlib.Path(sys.argv[i + 1])
    elif arg == "--http":
        HTTP_MODE = True
    elif arg == "--host" and i + 1 < len(sys.argv):
        HTTP_HOST = sys.argv[i + 1]
    elif arg == "--port" and i + 1 < len(sys.argv):
        HTTP_PORT = int(sys.argv[i + 1])
    elif arg == "--multi":
        MULTI_TENANT = True
        # Collect all remaining non-flag args as project paths
        for j in range(i + 1, len(sys.argv)):
            if sys.argv[j].startswith("-"):
                break
            p = pathlib.Path(sys.argv[j]).resolve()
            TENANT_DIRS[p.name] = p
        if not TARGET_DIR.resolve().name in TENANT_DIRS and TARGET_DIR != pathlib.Path("."):
            TENANT_DIRS[TARGET_DIR.resolve().name] = TARGET_DIR.resolve()

mcp = FastMCP(
    "0dai",
    instructions="Project AI layer knowledge server. Provides manifests, codebase structure, org policies, experience data, and command tiers."
    + (" Multi-tenant mode: use list_projects to see available projects, then pass project= to tools." if MULTI_TENANT else ""),
)


def _resolve_target(project: str = "") -> pathlib.Path:
    """Resolve target directory. In multi-tenant mode, maps project name to path."""
    if not MULTI_TENANT or not project:
        return TARGET_DIR
    # Security: only allow registered project names, no path traversal
    clean = project.replace("/", "").replace("\\", "").replace("..", "")
    return TENANT_DIRS.get(clean, TARGET_DIR)


def _safe_read(base: pathlib.Path, rel: str) -> str | None:
    """Read file with path traversal protection."""
    full = (base / rel).resolve()
    if not str(full).startswith(str(base.resolve())):
        return None  # Path traversal attempt
    if not full.is_file():
        return None
    try:
        return full.read_text(encoding="utf-8")
    except OSError:
        return None


def _read_json(rel_path: str) -> dict | list | None:
    path = TARGET_DIR / rel_path
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _read_yaml_text(rel_path: str) -> str | None:
    path = TARGET_DIR / rel_path
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _read_text(rel_path: str) -> str | None:
    path = TARGET_DIR / rel_path
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


# --- Tools ---


@mcp.tool
def get_project_manifest() -> dict:
    """Get the canonical project manifest with stack, agents, commands, and paths.

    Returns the ai/manifest/project.yaml content as structured data.
    Use this to understand what kind of project this is, which agents are configured,
    and what commands are available.
    """
    text = _read_yaml_text("ai/manifest/project.yaml")
    if text is None:
        return {"error": "no ai/manifest/project.yaml found — run 0dai init-existing first"}
    return {"content": text, "format": "yaml"}


@mcp.tool
def get_codebase_map() -> dict:
    """Get the structural map of the codebase: entry points, dependencies, directory roles, file types.

    Returns ai/manifest/codebase-map.json with:
    - repo_mode: "monorepo" or "polyrepo"
    - entry_points: main files (main.py, index.ts, etc.)
    - dependency_managers: detected package managers
    - directory_roles: what each directory does (source, tests, docs, etc.)
    - file_type_distribution: count by language
    - import_graph: module dependency graph with external deps ranking
    - metrics: total files, directories, import edges
    """
    data = _read_json("ai/manifest/codebase-map.json")
    if data is None:
        return {"error": "no ai/manifest/codebase-map.json found — run 0dai sync first"}
    return data


@mcp.tool
def get_org_policy() -> dict:
    """Get the active organization policy: permissions, MCP restrictions, hooks, and constraints.

    Returns ai/manifest/org-policy.json with:
    - packs_applied: which org packs are active
    - permissions: protected paths, denied commands
    - mcp: allowed/denied servers
    - hooks: policy-enforced hooks
    - constraints: max file size, review requirements, etc.
    """
    data = _read_json("ai/manifest/org-policy.json")
    if data is None:
        return {"status": "no org policy applied", "packs_applied": []}
    return data


@mcp.tool
def get_commands() -> dict:
    """Get the project command tier classification: which commands are safe, workspace, or ops tier.

    Returns ai/manifest/commands.yaml content showing:
    - safe: low-risk commands (lint, format, test)
    - workspace: commands that mutate the project (build, install)
    - ops: commands with infrastructure impact (deploy, migrate)
    """
    text = _read_yaml_text("ai/manifest/commands.yaml")
    if text is None:
        return {"error": "no ai/manifest/commands.yaml found"}
    return {"content": text, "format": "yaml"}


@mcp.tool
def get_environment() -> dict:
    """Get the execution environment manifest: runtime kind, available CLIs, capabilities.

    Returns ai/manifest/environment.yaml showing what tools and constraints
    apply in the current execution context.
    """
    text = _read_yaml_text("ai/manifest/environment.yaml")
    if text is None:
        return {"error": "no ai/manifest/environment.yaml found"}
    return {"content": text, "format": "yaml"}


@mcp.tool
def get_discovery() -> dict:
    """Get the project discovery data: detected stack, native configs, and command heuristics.

    Returns ai/manifest/discovery.json with what 0dai detected about this project
    during initialization or last sync.
    """
    data = _read_json("ai/manifest/discovery.json")
    if data is None:
        return {"error": "no ai/manifest/discovery.json found"}
    return data


@mcp.tool
def get_applied_lock() -> dict:
    """Get the applied lock manifest: which packs, versions, and checksums are installed.

    Returns ai/manifest/applied-lock.json showing the exact state of the AI layer.
    """
    data = _read_json("ai/manifest/applied-lock.json")
    if data is None:
        return {"error": "no ai/manifest/applied-lock.json found"}
    return data


@mcp.tool
def get_ai_version() -> dict:
    """Get the installed AI layer version and schema version.

    Returns the version from ai/VERSION and ai/VERSION_SCHEMA.
    """
    version = _read_text("ai/VERSION")
    schema = _read_text("ai/VERSION_SCHEMA")
    return {
        "version": version.strip() if version else "not installed",
        "schema_version": schema.strip() if schema else "unknown",
    }


@mcp.tool
def get_project_health() -> dict:
    """Get a comprehensive health check of the AI layer in this project.

    Combines version, manifests, org policy, and experience stats into
    a single health overview. Use this as the first tool call to understand
    the project's AI configuration state.
    """
    version = _read_text("ai/VERSION")
    codebase = _read_json("ai/manifest/codebase-map.json")
    policy = _read_json("ai/manifest/org-policy.json")
    discovery = _read_json("ai/manifest/discovery.json")
    lock = _read_json("ai/manifest/applied-lock.json")

    # Count experience events
    events_dir = TARGET_DIR / "ai" / "experience" / "events"
    candidates_dir = TARGET_DIR / "ai" / "experience" / "candidates"
    accepted_dir = TARGET_DIR / "ai" / "experience" / "accepted"

    events_count = len(list(events_dir.glob("*.json"))) if events_dir.is_dir() else 0
    candidates_count = len(list(candidates_dir.glob("*.md"))) if candidates_dir.is_dir() else 0
    accepted_count = sum(1 for _ in accepted_dir.rglob("*.md")) if accepted_dir.is_dir() else 0

    health = {
        "ai_layer_installed": version is not None,
        "version": version.strip() if version else None,
        "stack": discovery.get("stack") if discovery else None,
        "repo_mode": codebase.get("repo_mode") if codebase else None,
        "manifests_present": {
            "project.yaml": (TARGET_DIR / "ai/manifest/project.yaml").is_file(),
            "codebase-map.json": codebase is not None,
            "commands.yaml": (TARGET_DIR / "ai/manifest/commands.yaml").is_file(),
            "environment.yaml": (TARGET_DIR / "ai/manifest/environment.yaml").is_file(),
            "discovery.json": discovery is not None,
            "applied-lock.json": lock is not None,
            "org-policy.json": policy is not None,
        },
        "org_policy_active": policy is not None and len(policy.get("packs_applied", [])) > 0,
        "experience": {
            "events": events_count,
            "candidates": candidates_count,
            "accepted": accepted_count,
        },
        "entry_points": codebase.get("entry_points", []) if codebase else [],
        "dependency_managers": codebase.get("dependency_managers", {}) if codebase else {},
    }
    return health


@mcp.tool
def search_experience(query: str) -> dict:
    """Search the experience knowledge base using TF-IDF relevance ranking.

    Args:
        query: Search terms to find in experience events, candidates, and accepted knowledge.

    Returns results ranked by relevance score, not just substring match.
    Higher scores mean more relevant matches.
    """
    import math
    import re
    from collections import Counter

    def tokenize(text: str) -> list[str]:
        return re.findall(r"[a-z0-9_]+", text.lower())

    docs: list[dict] = []
    token_counts: list[Counter] = []

    for subdir in ["events", "candidates", "accepted", "outbox"]:
        base = TARGET_DIR / "ai" / "experience" / subdir
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            tokens = tokenize(text)
            if not tokens:
                continue
            docs.append({
                "path": str(path.relative_to(TARGET_DIR)),
                "category": subdir,
                "preview": text[:300].strip(),
            })
            token_counts.append(Counter(tokens))

    query_tokens = tokenize(query)
    if not query_tokens or not docs:
        return {"query": query, "indexed_documents": len(docs), "matches": 0, "results": []}

    n = len(docs)
    df: dict[str, int] = {}
    for token in query_tokens:
        df[token] = sum(1 for tc in token_counts if token in tc)

    scored: list[tuple[float, int]] = []
    for idx, tc in enumerate(token_counts):
        score = 0.0
        doc_len = sum(tc.values()) or 1
        for token in query_tokens:
            tf = tc.get(token, 0) / doc_len
            idf = math.log((n + 1) / (df.get(token, 0) + 1)) + 1
            score += tf * idf
        if score > 0:
            scored.append((score, idx))

    scored.sort(key=lambda x: -x[0])

    results = []
    for score, idx in scored[:10]:
        entry = dict(docs[idx])
        entry["score"] = round(score, 4)
        results.append(entry)

    return {
        "query": query,
        "indexed_documents": len(docs),
        "matches": len(results),
        "results": results,
    }


@mcp.tool
def get_bulletins() -> dict:
    """Get active knowledge bulletins: security advisories, best practices, and pattern warnings.

    Bulletins are pushed from 0dai upstream to projects during sync.
    They contain cross-project learnings, security notices, and operational guidance.
    Agents should check bulletins to stay current with ecosystem knowledge.
    """
    bulletins_dir = TARGET_DIR / "ai" / "bulletins"
    if not bulletins_dir.is_dir():
        return {"bulletins": [], "count": 0}

    bulletins: list[dict] = []
    for path in sorted(bulletins_dir.glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        entry: dict = {"file": path.name}
        for line in text.splitlines():
            for key in ("id", "severity", "title", "action", "published", "expires"):
                if line.startswith(f"{key}:"):
                    entry[key] = line.split(":", 1)[1].strip()
        # Extract body
        in_body = False
        body_lines: list[str] = []
        for line in text.splitlines():
            if in_body:
                if line.startswith("action:"):
                    break
                body_lines.append(line)
            if line.startswith("body:"):
                in_body = True
        entry["body"] = "\n".join(body_lines).strip()
        bulletins.append(entry)

    return {"bulletins": bulletins, "count": len(bulletins)}


@mcp.tool
def get_telemetry_summary() -> dict:
    """Get the latest telemetry report summarizing project experience metrics.

    Shows aggregated, anonymized operational data: event counts, CI pass rates,
    tool usage, task types, and accepted knowledge counts.
    """
    telemetry_dir = TARGET_DIR / "ai" / "telemetry" / "reports"
    if not telemetry_dir.is_dir():
        return {"status": "no telemetry reports yet — run 0dai report first"}

    reports = sorted(telemetry_dir.glob("*.json"), reverse=True)
    if not reports:
        return {"status": "no telemetry reports yet — run 0dai report first"}

    try:
        return json.loads(reports[0].read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"error": f"failed to read {reports[0].name}"}


@mcp.tool
def get_personas() -> dict:
    """Get available agent personas with their roles, prompts, and review checklists.

    Personas define different operating modes for agents:
    - architect: system design, module boundaries, ADRs
    - qa: test coverage, edge cases, regression prevention
    - devops: CI/CD, deployment, infrastructure
    - security: vulnerability detection, access control, secure coding

    Use this to understand what personas are available and select
    the right one for the current task.
    """
    personas_dir = TARGET_DIR / "ai" / "personas"
    if not personas_dir.is_dir():
        return {"personas": [], "count": 0}

    personas: list[dict] = []
    for path in sorted(personas_dir.glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        entry: dict = {"file": path.name}
        current_key = None
        list_items: list[str] = []

        for line in text.splitlines():
            for key in ("name", "display_name", "description"):
                if line.startswith(f"{key}:"):
                    entry[key] = line.split(":", 1)[1].strip()
            if line.startswith("review_checklist:"):
                current_key = "review_checklist"
                list_items = []
            elif current_key and line.strip().startswith("- "):
                list_items.append(line.strip()[2:])
            elif current_key and not line.strip().startswith("- ") and line.strip():
                entry[current_key] = list_items
                current_key = None
                list_items = []

        if current_key and list_items:
            entry[current_key] = list_items

        # Extract system prompt
        in_prompt = False
        prompt_lines: list[str] = []
        for line in text.splitlines():
            if in_prompt:
                if not line.startswith(" ") and not line.startswith("\t") and line.strip():
                    break
                prompt_lines.append(line)
            if line.startswith("system_prompt_addition:"):
                in_prompt = True
        entry["system_prompt"] = "\n".join(prompt_lines).strip()

        personas.append(entry)

    return {"personas": personas, "count": len(personas)}


@mcp.tool
def get_custom_stacks() -> dict:
    """Get project-local custom stack definitions from ai/stacks/.

    Custom stacks extend 0dai's built-in detection with project-specific
    or organization-specific stack patterns. They take priority over
    upstream detectors.
    """
    stacks_dir = TARGET_DIR / "ai" / "stacks"
    if not stacks_dir.is_dir():
        return {"stacks": [], "count": 0}

    stacks: list[dict] = []
    for path in sorted(stacks_dir.glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        entry: dict = {"file": path.name}
        for line in text.splitlines():
            for key in ("name", "priority", "recommended_layout"):
                if line.startswith(f"{key}:"):
                    val = line.split(":", 1)[1].strip()
                    try:
                        val = int(val)
                    except ValueError:
                        pass
                    entry[key] = val
        stacks.append(entry)

    return {"stacks": stacks, "count": len(stacks)}


@mcp.tool
def get_audit_log(limit: int = 20) -> dict:
    """Get the most recent audit log entries for this project.

    Args:
        limit: Maximum number of entries to return (default 20, most recent first).

    Shows what 0dai operations were performed: init, sync, apply-policy, etc.
    Useful for understanding change history and compliance tracking.
    """
    audit_path = TARGET_DIR / "ai" / "manifest" / "audit.jsonl"
    if not audit_path.is_file():
        return {"entries": [], "count": 0}

    entries: list[dict] = []
    try:
        for line in audit_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return {"entries": [], "count": 0, "error": "failed to read audit log"}

    entries.reverse()
    return {"entries": entries[:limit], "count": len(entries)}


@mcp.tool
def get_federation() -> dict:
    """Get cross-repo knowledge federation status.

    Shows linked peer repositories, their reachability, last sync time,
    and synced knowledge counts. Federation allows micro-service repos
    to share accepted experience (rules, skills, anti-patterns).
    """
    fed_path = TARGET_DIR / "ai" / "federation.yaml"
    if not fed_path.is_file():
        return {"configured": False, "peers": []}

    peers: list[dict] = []
    current: dict | None = None
    for line in fed_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- name:") or stripped.startswith("- path:"):
            if current:
                peers.append(current)
            current = {}
            key, val = stripped[2:].split(":", 1)
            current[key.strip()] = val.strip()
        elif current and ":" in stripped and not stripped.startswith("#"):
            key, val = stripped.split(":", 1)
            current[key.strip()] = val.strip()
    if current:
        peers.append(current)

    # Check reachability and count synced items
    for peer in peers:
        p = pathlib.Path(peer.get("path", ""))
        peer["reachable"] = p.is_dir()
        fed_dir = TARGET_DIR / "ai" / "experience" / "federated" / peer.get("name", "")
        peer["synced_items"] = sum(1 for _ in fed_dir.rglob("*.md")) if fed_dir.is_dir() else 0

    return {"configured": True, "peers": peers, "count": len(peers)}


@mcp.tool
def get_registry(search: str = "") -> dict:
    """Browse the community stack registry.

    Args:
        search: Optional search term to filter by name, description, or tags.

    Returns available community stacks that can be installed via
    `0dai registry --install <name> --target <path>`.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "registry", str(pathlib.Path(__file__).parent / "registry.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    stacks = mod.load_registry()
    if search:
        stacks = mod.search_stacks(stacks, search)

    return {
        "stacks": [{"name": s["name"], "description": s.get("description", ""), "tags": s.get("tags", [])} for s in stacks],
        "count": len(stacks),
    }


@mcp.tool
def get_maturity_score() -> dict:
    """Get the AI layer maturity scorecard for this project.

    Evaluates completeness across manifests, experience lifecycle,
    personas, org policy, IDE configs, bulletins, federation, and audit.
    Returns a 0-100 score with letter grade (A-F) and badge URL.

    Use this to assess how well-configured the AI layer is and what's missing.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "maturity_score", str(pathlib.Path(__file__).parent / "maturity_score.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.score_project(TARGET_DIR)


@mcp.tool
def get_mcp_catalog(stack: str = "") -> dict:
    """Get recommended MCP servers for a given stack.

    Args:
        stack: Stack name (e.g., "fastapi", "nextjs"). If empty, uses detected stack.

    Returns common servers and stack-specific recommendations from the MCP catalog.
    """
    catalog_path = pathlib.Path(__file__).parent.parent / "templates" / "layer" / "ai" / "registry" / "mcp-catalog.json"
    if not catalog_path.is_file():
        return {"error": "MCP catalog not found"}

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    if not stack:
        discovery = _read_json("ai/manifest/discovery.json")
        stack = discovery.get("stack", "generic") if discovery else "generic"

    common = {k: v.get("description", "") for k, v in catalog.get("common", {}).items()}
    stack_servers = {}
    stack_entry = catalog.get("stacks", {}).get(stack, {})
    for k, v in stack_entry.get("servers", {}).items():
        stack_servers[k] = v.get("description", "")

    return {
        "stack": stack,
        "common_servers": common,
        "stack_servers": stack_servers,
        "available_stacks": sorted(catalog.get("stacks", {}).keys()),
    }


@mcp.tool
def get_agent_teams() -> dict:
    """Get available and installed Agent Teams for this project.

    Returns agent team members that can operate as specialized sub-agents
    in Claude Code: planner, reviewer, architect, qa, devops, security.
    Each agent has a defined role, focus paths, and review checklist.

    Use this to understand what specialized agents are configured
    and their capabilities before delegating tasks.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "generate_agent_teams", str(pathlib.Path(__file__).parent / "generate_agent_teams.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    templates = mod.get_agent_templates()
    installed = mod.get_installed_agents(TARGET_DIR)
    personas = mod.get_personas(TARGET_DIR)

    return {
        "available_agents": [
            {"name": t["name"], "description": t.get("description", "")}
            for t in templates
        ],
        "installed_agents": [
            {"name": a["name"], "description": a.get("description", ""), "managed": a.get("managed", False)}
            for a in installed
        ],
        "personas": [
            {"name": p.get("name", ""), "display_name": p.get("display_name", "")}
            for p in personas
        ],
        "counts": {
            "available": len(templates),
            "installed": len(installed),
            "personas": len(personas),
        },
    }


@mcp.tool
def get_specs(status: str = "") -> dict:
    """Get structured development specifications from ai/specs/.

    Args:
        status: Filter by status (draft, ready, in-progress, done, cancelled).
                Leave empty to return all specs.

    Specs define what needs to be built with structured context, requirements,
    and acceptance criteria. Read relevant specs before starting work to
    understand the full intent and constraints.
    """
    import importlib.util
    spec_mod = importlib.util.spec_from_file_location(
        "manage_specs", str(pathlib.Path(__file__).parent / "manage_specs.py"),
    )
    mod = importlib.util.module_from_spec(spec_mod)
    spec_mod.loader.exec_module(mod)

    specs = mod._list_specs(TARGET_DIR)
    if status:
        specs = [s for s in specs if s.get("status") == status]

    return {
        "specs": [
            {
                "id": s.get("id"),
                "title": s.get("title"),
                "status": s.get("status"),
                "priority": s.get("priority"),
                "agent": s.get("agent"),
                "tags": s.get("tags", []),
                "criteria_total": s.get("criteria_total", 0),
                "criteria_done": s.get("criteria_done", 0),
                "body": s.get("body", ""),
            }
            for s in specs
        ],
        "count": len(specs),
        "filter": status or None,
    }


# --- Write Tools ---


def _wal_record(action: str, file_rel: str) -> None:
    """Record a WAL entry before mutating a file."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "wal", str(pathlib.Path(__file__).parent / "wal.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    file_path = TARGET_DIR / file_rel
    before = file_path.read_text(encoding="utf-8") if file_path.is_file() else None
    mod.record(TARGET_DIR, action, file_rel, before, None)


def _write_audit_entry(action: str, detail: str) -> None:
    """Append an audit log entry for write operations."""
    import time
    audit_path = TARGET_DIR / "ai" / "manifest" / "audit.jsonl"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    entry = json.dumps({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
        "action": f"mcp-write:{action}",
        "detail": detail,
    }, ensure_ascii=False)
    with audit_path.open("a", encoding="utf-8") as f:
        f.write(entry + "\n")


@mcp.tool
def create_spec(title: str, goal: str, requirements: str, priority: str = "medium", agent: str = "") -> dict:
    """Create a new development specification in ai/specs/.

    Args:
        title: Short title for the spec (e.g., "Add user authentication").
        goal: One sentence describing what success looks like.
        requirements: Numbered requirements, one per line.
        priority: Priority level: critical, high, medium, low. Defaults to medium.
        agent: Agent role to assign (planner, architect, etc.). Optional.

    Creates a structured spec with auto-incremented ID. The spec starts
    in 'draft' status. Set to 'ready' when it's complete and reviewed.
    """
    import re
    import time

    specs_dir = TARGET_DIR / "ai" / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

    # Auto-increment ID
    existing_ids: list[int] = []
    for f in specs_dir.glob("SPEC-*.md"):
        m = re.match(r"SPEC-(\d+)", f.name)
        if m:
            existing_ids.append(int(m.group(1)))
    next_id = max(existing_ids, default=0) + 1
    spec_id = f"SPEC-{next_id:03d}"

    # Sanitize title for filename
    safe = re.sub(r"[^a-z0-9-]", "-", title.lower())
    safe = re.sub(r"-+", "-", safe).strip("-")[:50]
    filename = f"{spec_id}-{safe}.md"

    today = time.strftime("%Y-%m-%d", time.gmtime())

    # Format requirements as numbered list if not already
    req_lines = []
    for i, line in enumerate(requirements.strip().splitlines(), 1):
        line = line.strip().lstrip("0123456789.-) ")
        if line:
            req_lines.append(f"{i}. {line}")

    content = f"""---
id: {spec_id}
title: {title}
status: draft
priority: {priority}
author: mcp-agent
created: {today}
updated: {today}
tags: []
agent: {agent}
---

## Context

(To be filled — why is this work needed?)

## Goal

{goal}

## Requirements

{chr(10).join(req_lines) if req_lines else "1. (To be defined)"}

## Acceptance Criteria

- [ ] (To be defined)

## Out of Scope

- (To be defined)

## Technical Notes

(To be filled)
"""

    _wal_record("create_spec", f"ai/specs/{filename}")
    (specs_dir / filename).write_text(content, encoding="utf-8")
    _write_audit_entry("create_spec", f"{spec_id}: {title}")

    return {
        "created": True,
        "id": spec_id,
        "file": f"ai/specs/{filename}",
        "status": "draft",
        "message": f"Spec {spec_id} created. Edit to fill Context/Acceptance Criteria, then set status to 'ready'.",
    }


@mcp.tool
def record_experience(event_type: str, tool: str, task_type: str, summary: str, paths: list[str] | None = None, ci_passed: bool = True) -> dict:
    """Record an experience event in ai/experience/events/.

    Args:
        event_type: Type of event (e.g., "task_complete", "bug_found", "pattern_detected").
        tool: Which agent CLI was used (claude, codex, opencode, gemini).
        task_type: Category (bugfix, feature, refactor, migration, review).
        summary: Brief description of what happened and what was learned.
        paths: List of file paths that were involved. Optional.
        ci_passed: Whether CI passed after this change. Defaults to True.

    Records a structured experience event for later harvesting and promotion.
    Events are the raw input to the experience flywheel.
    """
    import time
    import hashlib

    events_dir = TARGET_DIR / "ai" / "experience" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    event_id = hashlib.sha256(f"{timestamp}:{summary}".encode()).hexdigest()[:12]

    event = {
        "schema": 1,
        "event_id": event_id,
        "timestamp": timestamp,
        "event_type": event_type,
        "tool": tool,
        "task_type": task_type,
        "summary": summary,
        "paths": paths or [],
        "ci_passed": ci_passed,
        "source": "mcp-agent",
    }

    filename = f"{time.strftime('%Y%m%d-%H%M%S', time.gmtime())}-{event_id}.json"
    _wal_record("record_experience", f"ai/experience/events/{filename}")
    (events_dir / filename).write_text(
        json.dumps(event, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    _write_audit_entry("record_experience", f"{event_type}: {summary[:80]}")

    return {
        "recorded": True,
        "event_id": event_id,
        "file": f"ai/experience/events/{filename}",
        "message": "Experience event recorded. Run '0dai harvest' to process into candidates.",
    }


@mcp.tool
def update_decision(title: str, context: str, decision: str, consequences: str) -> dict:
    """Append an Architecture Decision Record to ai/docs/decisions.md.

    Args:
        title: Short title (e.g., "Use PostgreSQL for user data").
        context: What situation prompted this decision.
        decision: What was decided and why.
        consequences: Tradeoffs accepted, what this enables/prevents.

    Decisions are append-only — each call adds a new ADR entry.
    """
    import time

    decisions_path = TARGET_DIR / "ai" / "docs" / "decisions.md"
    decisions_path.parent.mkdir(parents=True, exist_ok=True)

    today = time.strftime("%Y-%m-%d", time.gmtime())

    entry = f"""
### {title}

**Date:** {today}
**Status:** Accepted

**Context:** {context}

**Decision:** {decision}

**Consequences:** {consequences}

---
"""

    _wal_record("update_decision", "ai/docs/decisions.md")
    if decisions_path.is_file():
        existing = decisions_path.read_text(encoding="utf-8")
        decisions_path.write_text(existing.rstrip() + "\n" + entry, encoding="utf-8")
    else:
        decisions_path.write_text(f"# Architectural Decisions\n{entry}", encoding="utf-8")

    _write_audit_entry("update_decision", title)

    return {
        "recorded": True,
        "file": "ai/docs/decisions.md",
        "title": title,
        "message": "ADR appended to decisions.md.",
    }


@mcp.tool
def get_plugins() -> dict:
    """List installed plugins and their capabilities.

    Plugins extend 0dai with custom commands, checks, and generators.
    Each plugin lives in ai/plugins/<name>/ with a plugin.json manifest.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "plugin_manager", str(pathlib.Path(__file__).parent / "plugin_manager.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    plugins = mod.list_plugins(TARGET_DIR)
    for p in plugins:
        p.pop("_path", None)
        p.pop("_dir", None)
    return {"plugins": plugins, "count": len(plugins)}


@mcp.tool
def check_approval(command: str) -> dict:
    """Check if a command requires approval and request it if needed.

    Args:
        command: The command to check (e.g. "deploy", "migrate").

    Ops-tier commands (deploy, migrate, rollback, destroy) require human
    approval before execution. Returns whether approval is needed and
    the request ID if created.
    """
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "approval_workflow", str(pathlib.Path(__file__).parent / "approval_workflow.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except (FileNotFoundError, AttributeError):
        return {"error": "Team feature — upgrade to 0dai Team plan at https://0dai.dev", "available": False}

    required = mod.needs_approval(TARGET_DIR, command)
    result = {"command": command, "approval_required": required}
    if required:
        req = mod.request_approval(TARGET_DIR, command, "Requested by agent via MCP")
        result["request_id"] = req["id"]
        result["status"] = "pending"
        result["message"] = f"Approval required. Request {req['id']} created. Waiting for human approval."
    return result


@mcp.tool
def list_projects() -> dict:
    """List all projects available in this MCP server.

    In multi-tenant mode, returns all registered projects with their paths
    and ai/ layer status. Pass a project name to other tools to query
    a specific project.

    In single-tenant mode, returns the current target project.
    """
    if not MULTI_TENANT:
        ver = _read_text("ai/VERSION")
        return {
            "mode": "single",
            "projects": [{
                "name": TARGET_DIR.resolve().name,
                "path": str(TARGET_DIR.resolve()),
                "ai_installed": ver is not None,
                "version": ver.strip() if ver else None,
            }],
        }

    projects = []
    for name, path in sorted(TENANT_DIRS.items()):
        v_path = path / "ai" / "VERSION"
        ver = v_path.read_text("utf-8").strip() if v_path.is_file() else None
        projects.append({
            "name": name,
            "path": str(path),
            "ai_installed": ver is not None,
            "version": ver,
        })
    return {"mode": "multi-tenant", "projects": projects, "count": len(projects)}


@mcp.tool
def get_project_health_multi(project: str = "") -> dict:
    """Get project health for a specific project in multi-tenant mode.

    Args:
        project: Project name from list_projects. Empty = default project.

    Returns comprehensive health check: version, stack, manifests, experience stats.
    """
    target = _resolve_target(project)
    # Reuse existing health logic with overridden target
    orig = globals().get("TARGET_DIR")
    try:
        globals()["TARGET_DIR"] = target
        ver = _read_text("ai/VERSION")
        discovery = _read_json("ai/manifest/discovery.json")
        codebase = _read_json("ai/manifest/codebase-map.json")
        return {
            "project": project or target.resolve().name,
            "ai_installed": ver is not None,
            "version": ver.strip() if ver else None,
            "stack": discovery.get("stack") if discovery else None,
            "repo_mode": codebase.get("repo_mode") if codebase else None,
        }
    finally:
        globals()["TARGET_DIR"] = orig


@mcp.tool
def scan_secrets() -> dict:
    """Scan ai/ layer for leaked secrets, API keys, tokens, and PII.

    Detects: AWS/GCP/Stripe/OpenAI/Anthropic keys, GitHub PATs, JWT tokens,
    private keys, passwords in configs, connection strings, .env values.

    Returns findings sorted by severity (critical → high → medium).
    Use before commits or deployments to prevent credential leaks.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "scan_secrets", str(pathlib.Path(__file__).parent / "scan_secrets.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.scan_target(TARGET_DIR)


@mcp.tool
def get_session() -> dict:
    """Get the active roaming session — what task is in progress, which agent started it, handoff notes.

    Session roaming lets you start a task in Claude Code, continue in Codex,
    finish in Gemini. The active session in ai/sessions/active.json carries
    context between agents: goal, plan, files touched, decisions, and handoff notes.

    Always check this at session start to pick up where another agent left off.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "session_manager", str(pathlib.Path(__file__).parent / "session_manager.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    active = mod.load_active(TARGET_DIR)
    return active if active else {"active": False, "message": "No active session. Use 0dai session save to start one."}


@mcp.tool
def save_session(summary: str, goal: str = "") -> dict:
    """Save or update the active roaming session with current progress.

    Args:
        summary: What you did and where to pick up (handoff notes for the next agent).
        goal: Overall task goal (only needed when starting a new session).

    Call this before handing off to another agent so they have full context.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "session_manager", str(pathlib.Path(__file__).parent / "session_manager.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    mod.cmd_save(TARGET_DIR, summary, goal, "")
    return {"saved": True, "summary": summary, "session": mod.load_active(TARGET_DIR)}


@mcp.tool
def get_compliance_report(framework: str = "soc2") -> dict:
    """Generate compliance evidence report mapped to SOC 2 or ISO 27001 controls.

    Args:
        framework: "soc2" or "iso27001" (default: soc2).

    Collects evidence from audit logs, WAL, role policies, org policies,
    experience pipeline, version control, and prompt versioning. Maps each
    evidence source to framework controls with pass/gap status.
    """
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "compliance_report", str(pathlib.Path(__file__).parent / "compliance_report.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except (FileNotFoundError, AttributeError):
        return {"error": "Team feature — upgrade to 0dai Team plan at https://0dai.dev", "available": False}

    evidence = mod.generate_evidence(TARGET_DIR)
    mappings = mod.map_to_framework(evidence, framework)
    fw = mod.FRAMEWORKS.get(framework, mod.FRAMEWORKS["soc2"])
    return {
        "framework": fw["name"],
        "evidence": evidence,
        "control_mappings": mappings,
        "summary": {
            "total": len(mappings),
            "evidenced": sum(1 for m in mappings if m["status"] == "evidenced"),
            "gaps": sum(1 for m in mappings if m["status"] == "gap"),
        },
    }


@mcp.tool
def check_conflicts(branch: str = "main") -> dict:
    """Check for ai/ layer conflicts between current branch and target branch.

    Args:
        branch: Target branch to compare against (default: main).

    Detects files changed in both branches since their merge base.
    Managed files can be auto-resolved (upstream wins).
    Custom files are flagged for manual review.
    """
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "conflict_resolver", str(pathlib.Path(__file__).parent / "conflict_resolver.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except (FileNotFoundError, AttributeError):
        return {"error": "Team feature — upgrade to 0dai Team plan at https://0dai.dev", "available": False}
    return mod.detect_conflicts(TARGET_DIR, branch)


@mcp.tool
def get_role_policy(user: str = "") -> dict:
    """Get role-based command policy and optionally check a user's access.

    Args:
        user: If provided, returns this user's role and allowed tiers.
              If empty, returns the full policy with all roles and assignments.

    Roles: viewer (safe only), developer (safe+workspace), lead (+promote),
    admin (all tiers + deploy). Agents should check policy before running
    ops-tier commands.
    """
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "role_policy", str(pathlib.Path(__file__).parent / "role_policy.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except (FileNotFoundError, AttributeError):
        return {"error": "Team feature — upgrade to 0dai Team plan at https://0dai.dev", "available": False}

    policy = mod._load_policy(TARGET_DIR)
    if user:
        roles = policy.get("roles", mod.DEFAULT_ROLES)
        assignments = policy.get("assignments", {})
        user_role = assignments.get(user, "developer")
        role_def = roles.get(user_role, mod.DEFAULT_ROLES["developer"])
        return {"user": user, "role": user_role, **role_def}
    return policy


@mcp.tool
def get_activity_feed(limit: int = 20, source: str = "") -> dict:
    """Get team activity feed: who changed what in the ai/ layer, when, with which agent.

    Args:
        limit: Max entries (default 20).
        source: Filter by source: audit, mcp, experience, git. Empty for all.

    Aggregates audit log, WAL mutations, experience events, and git commits
    into a unified timeline. Use this to understand recent changes and who made them.
    """
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "activity_feed", str(pathlib.Path(__file__).parent / "activity_feed.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except (FileNotFoundError, AttributeError):
        return {"error": "Team feature — upgrade to 0dai Team plan at https://0dai.dev", "available": False}
    return mod.build_feed(TARGET_DIR, limit, source)


@mcp.tool
def get_knowledge_base(query: str = "") -> dict:
    """Get shared knowledge base status and optionally search it.

    Args:
        query: Optional search term. Leave empty for status overview.

    Returns team-level knowledge aggregated from all connected projects:
    rules, skills, playbooks, anti-patterns, and contributor info.
    """
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "knowledge_base", str(pathlib.Path(__file__).parent / "knowledge_base.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except (FileNotFoundError, AttributeError):
        return {"error": "Team feature — upgrade to 0dai Team plan at https://0dai.dev", "available": False}

    config = mod._load_config(TARGET_DIR)
    if not config:
        return {"connected": False, "message": "Not connected to a knowledge base"}

    kb_dir = pathlib.Path(config["kb_path"])
    items: dict[str, int] = {}
    if kb_dir.is_dir():
        for cat in ["rules", "skills", "playbooks", "anti-patterns"]:
            d = kb_dir / cat
            items[cat] = len(list(d.glob("*.md"))) if d.is_dir() else 0

    result = {
        "connected": True,
        "kb_path": config["kb_path"],
        "reachable": kb_dir.is_dir(),
        "items": items,
        "total_items": sum(items.values()),
        "last_push": config.get("last_push"),
        "last_pull": config.get("last_pull"),
    }

    if query and kb_dir.is_dir():
        q = query.lower()
        matches = []
        for cat in ["rules", "skills", "playbooks", "anti-patterns"]:
            d = kb_dir / cat
            if not d.is_dir():
                continue
            for p in d.glob("*.md"):
                try:
                    text = p.read_text(encoding="utf-8")
                except OSError:
                    continue
                if q in text.lower():
                    matches.append({"file": p.name, "category": cat, "preview": text[:200]})
        result["search"] = {"query": query, "matches": len(matches), "results": matches[:10]}

    return result


@mcp.tool
def get_wal(limit: int = 20) -> dict:
    """Get write-ahead log entries for MCP mutations.

    Args:
        limit: Maximum entries to return (default 20, most recent first).

    Shows what MCP write operations were performed and their undo status.
    Each entry records the file state before mutation, enabling rollback.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "wal", str(pathlib.Path(__file__).parent / "wal.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    entries = mod.load_entries(TARGET_DIR, limit)
    return {"entries": entries, "count": len(entries)}


@mcp.tool
def undo_mutation(entry_id: str = "") -> dict:
    """Undo a specific MCP write mutation by restoring the previous file state.

    Args:
        entry_id: WAL entry ID to undo. Leave empty to undo the most recent mutation.

    Restores the file to its state before the mutation was applied.
    Only works on entries that haven't already been undone.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "wal", str(pathlib.Path(__file__).parent / "wal.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    return mod.undo(TARGET_DIR, entry_id if entry_id else None)


@mcp.tool
def get_prompt_history() -> dict:
    """Get prompt versioning status and change history.

    Tracks changes to system prompts, agent definitions, and task templates
    across ai/prompts/, .claude/agents/, .gemini/agents/, .aider/agents/.
    Shows which prompts changed since last snapshot, version history,
    and current file hashes for drift detection.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "prompt_versioning", str(pathlib.Path(__file__).parent / "prompt_versioning.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    return {
        "status": mod.status(TARGET_DIR),
        "history": mod.get_history(TARGET_DIR),
    }


@mcp.tool
def get_observability(provider: str = "") -> dict:
    """Get observability and tracing recommendations for this project's stack.

    Args:
        provider: Filter to a specific provider (langfuse, opentelemetry, langsmith).
                  Leave empty for all recommended providers.

    Returns stack-aware tracing configurations including required packages,
    environment variables, and setup documentation links.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "generate_observability", str(pathlib.Path(__file__).parent / "generate_observability.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    rec = mod.get_recommendations(TARGET_DIR)
    if provider:
        rec["recommended"] = [r for r in rec["recommended"] if r["provider"] == provider]
    return rec


@mcp.tool
def score_candidates() -> dict:
    """Score experience candidates by impact, frequency, and quality signals.

    Evaluates each candidate in ai/experience/candidates/ across 6 dimensions:
    recurrence (0-10), CI signal (0-5), stability (0-3), scope clarity (0-2),
    review quality (0-3), and type weight (0-2). Max score: 25.

    Recommendations: promote (>=18), review (>=10), defer (<10).
    Use this to prioritize which candidates to promote to accepted knowledge.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "score_experience", str(pathlib.Path(__file__).parent / "score_experience.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.score_all(TARGET_DIR)


@mcp.tool
def get_orchestration() -> dict:
    """Get agent orchestration configs: squad and swarm workspace definitions.

    Returns team structures for multi-agent coordination:
    - Squad: lead (architect) + specialists (qa, devops) + gate (security)
    - Swarm: orchestrator + parallel agents + reviewer

    Each structure includes workflows, handoff rules, and task routing patterns
    derived from the project's personas and playbooks.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "generate_orchestration", str(pathlib.Path(__file__).parent / "generate_orchestration.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    return {
        "squad": mod.generate_squad(TARGET_DIR),
        "swarm": mod.generate_swarm(TARGET_DIR),
    }


if __name__ == "__main__":
    if HTTP_MODE:
        print(f"[0dai-mcp] starting Streamable HTTP server on {HTTP_HOST}:{HTTP_PORT}", file=sys.stderr)
        print(f"[0dai-mcp] target: {TARGET_DIR.resolve()}", file=sys.stderr)
        print(f"[0dai-mcp] MCP endpoint: http://{HTTP_HOST}:{HTTP_PORT}/mcp", file=sys.stderr)
        mcp.run(transport="streamable-http", host=HTTP_HOST, port=HTTP_PORT)
    else:
        mcp.run()
