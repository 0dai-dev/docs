"""Core SDK functions for reading and querying the ai/ layer."""
from __future__ import annotations

import json
import pathlib
from typing import Any


def _read_json(root: pathlib.Path, rel: str) -> dict | list | None:
    path = root / rel
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _read_text(root: pathlib.Path, rel: str) -> str | None:
    path = root / rel
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def version(target: str | pathlib.Path = ".") -> dict[str, str | None]:
    """Get installed AI layer version.

    >>> zerodayai.version("/path/to/project")
    {"version": "0.2.5", "schema_version": "1"}
    """
    root = pathlib.Path(target)
    v = _read_text(root, "ai/VERSION")
    s = _read_text(root, "ai/VERSION_SCHEMA")
    return {
        "version": v.strip() if v else None,
        "schema_version": s.strip() if s else None,
    }


def detect(target: str | pathlib.Path = ".") -> dict[str, Any]:
    """Detect project stack from ai/manifest/discovery.json.

    >>> zerodayai.detect("/path/to/project")
    {"stack": "fastapi", "native_configs": [...]}
    """
    root = pathlib.Path(target)
    data = _read_json(root, "ai/manifest/discovery.json")
    if data is None:
        return {"stack": "unknown", "error": "no discovery.json — run 0dai init-existing first"}
    return data


def health(target: str | pathlib.Path = ".") -> dict[str, Any]:
    """Get comprehensive AI layer health check.

    >>> h = zerodayai.health("/path/to/project")
    >>> h["ai_layer_installed"]
    True
    """
    root = pathlib.Path(target)
    v = _read_text(root, "ai/VERSION")
    codebase = _read_json(root, "ai/manifest/codebase-map.json")
    policy = _read_json(root, "ai/manifest/org-policy.json")
    discovery = _read_json(root, "ai/manifest/discovery.json")
    lock = _read_json(root, "ai/manifest/applied-lock.json")

    events_dir = root / "ai" / "experience" / "events"
    candidates_dir = root / "ai" / "experience" / "candidates"
    accepted_dir = root / "ai" / "experience" / "accepted"

    return {
        "ai_layer_installed": v is not None,
        "version": v.strip() if v else None,
        "stack": discovery.get("stack") if discovery else None,
        "repo_mode": codebase.get("repo_mode") if codebase else None,
        "manifests_present": {
            "project.yaml": (root / "ai/manifest/project.yaml").is_file(),
            "codebase-map.json": codebase is not None,
            "commands.yaml": (root / "ai/manifest/commands.yaml").is_file(),
            "discovery.json": discovery is not None,
            "applied-lock.json": lock is not None,
            "org-policy.json": policy is not None,
        },
        "org_policy_active": policy is not None and len(policy.get("packs_applied", [])) > 0,
        "experience": {
            "events": len(list(events_dir.glob("*.json"))) if events_dir.is_dir() else 0,
            "candidates": len(list(candidates_dir.glob("*.md"))) if candidates_dir.is_dir() else 0,
            "accepted": sum(1 for _ in accepted_dir.rglob("*.md")) if accepted_dir.is_dir() else 0,
        },
    }


def manifests(target: str | pathlib.Path = ".") -> dict[str, Any]:
    """Get all manifest data in one call.

    >>> m = zerodayai.manifests("/path/to/project")
    >>> m["project"] is not None
    True
    """
    root = pathlib.Path(target)
    return {
        "project": _read_text(root, "ai/manifest/project.yaml"),
        "discovery": _read_json(root, "ai/manifest/discovery.json"),
        "commands": _read_text(root, "ai/manifest/commands.yaml"),
        "environment": _read_text(root, "ai/manifest/environment.yaml"),
        "applied_lock": _read_json(root, "ai/manifest/applied-lock.json"),
        "org_policy": _read_json(root, "ai/manifest/org-policy.json"),
    }


def codebase_map(target: str | pathlib.Path = ".") -> dict[str, Any]:
    """Get codebase structural map.

    >>> m = zerodayai.codebase_map("/path/to/project")
    >>> m["repo_mode"]
    "polyrepo"
    """
    root = pathlib.Path(target)
    data = _read_json(root, "ai/manifest/codebase-map.json")
    if data is None:
        return {"error": "no codebase-map.json — run 0dai sync first"}
    return data


def experience(target: str | pathlib.Path = ".", query: str | None = None) -> dict[str, Any]:
    """Search or summarize experience knowledge base.

    >>> zerodayai.experience("/path", query="bugfix")
    {"query": "bugfix", "matches": 3, "results": [...]}
    """
    root = pathlib.Path(target)

    if query:
        results: list[dict] = []
        query_lower = query.lower()
        for subdir in ["events", "candidates", "accepted"]:
            base = root / "ai" / "experience" / subdir
            if not base.is_dir():
                continue
            for path in base.rglob("*"):
                if not path.is_file():
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except OSError:
                    continue
                if query_lower in text.lower():
                    results.append({
                        "path": str(path.relative_to(root)),
                        "category": subdir,
                        "preview": text[:500],
                    })
                    if len(results) >= 20:
                        break
        return {"query": query, "matches": len(results), "results": results}

    # Summary mode
    events_dir = root / "ai" / "experience" / "events"
    candidates_dir = root / "ai" / "experience" / "candidates"
    accepted_dir = root / "ai" / "experience" / "accepted"
    return {
        "events": len(list(events_dir.glob("*.json"))) if events_dir.is_dir() else 0,
        "candidates": len(list(candidates_dir.glob("*.md"))) if candidates_dir.is_dir() else 0,
        "accepted": sum(1 for _ in accepted_dir.rglob("*.md")) if accepted_dir.is_dir() else 0,
    }


def agent_teams(target: str | pathlib.Path = ".") -> dict[str, Any]:
    """Get available and installed Agent Teams for a project.

    >>> teams = zerodayai.agent_teams("/path/to/project")
    >>> teams["counts"]["installed"]
    6
    """
    root = pathlib.Path(target)

    installed: list[dict] = []
    agents_dir = root / ".claude" / "agents"
    if agents_dir.is_dir():
        for path in sorted(agents_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            entry: dict = {"name": path.stem, "managed": "managed: true" in text}
            if text.startswith("---"):
                end = text.find("---", 3)
                if end > 0:
                    for line in text[3:end].splitlines():
                        if ":" in line:
                            k, _, v = line.partition(":")
                            entry[k.strip()] = v.strip()
            installed.append(entry)

    personas: list[dict] = []
    personas_dir = root / "ai" / "personas"
    if personas_dir.is_dir():
        for path in sorted(personas_dir.glob("*.yaml")):
            text = path.read_text(encoding="utf-8")
            entry = {"name": path.stem}
            for line in text.splitlines():
                for key in ("display_name", "description"):
                    if line.startswith(f"{key}:"):
                        entry[key] = line.split(":", 1)[1].strip()
            personas.append(entry)

    return {
        "installed_agents": installed,
        "personas": personas,
        "counts": {
            "installed": len(installed),
            "personas": len(personas),
        },
    }


def specs(target: str | pathlib.Path = ".", status: str | None = None) -> dict[str, Any]:
    """Get structured development specifications from ai/specs/.

    >>> s = zerodayai.specs("/path/to/project")
    >>> s["count"]
    3
    >>> zerodayai.specs("/path", status="ready")
    {"specs": [...], "count": 1}
    """
    import re

    root = pathlib.Path(target)
    specs_dir = root / "ai" / "specs"
    if not specs_dir.is_dir():
        return {"specs": [], "count": 0}

    results: list[dict] = []
    for path in sorted(specs_dir.glob("*.md")):
        if path.name in ("README.md", "TEMPLATE.md"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        entry: dict = {"file": path.name}
        if text.startswith("---"):
            end = text.find("---", 3)
            if end > 0:
                for line in text[3:end].splitlines():
                    line = line.strip()
                    if ":" in line:
                        k, _, v = line.partition(":")
                        k, v = k.strip(), v.strip()
                        if v.startswith("[") and v.endswith("]"):
                            v = [t.strip().strip("'\"") for t in v[1:-1].split(",") if t.strip()]
                        entry[k] = v

        if status and entry.get("status") != status:
            continue
        results.append(entry)

    return {"specs": results, "count": len(results)}
