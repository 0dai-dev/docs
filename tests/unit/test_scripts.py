#!/usr/bin/env python3
"""Unit tests for 0dai Python scripts."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "scripts"


def run_script(name: str, *args: str, cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / name), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def make_experience_tree(root: pathlib.Path) -> None:
    """Create minimal ai/experience structure for testing."""
    (root / "ai" / "experience" / "outbox").mkdir(parents=True, exist_ok=True)
    (root / "ai" / "experience" / "events").mkdir(parents=True, exist_ok=True)
    (root / "ai" / "experience" / "reports").mkdir(parents=True, exist_ok=True)


# --- analyze_codebase tests ---

def test_analyze_codebase_creates_manifest():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / "src").mkdir()
        (root / "tests").mkdir()
        (root / "main.py").write_text("print('hi')\n")
        (root / "package.json").write_text('{"name":"demo"}\n')

        result = run_script("analyze_codebase.py", tmp)
        assert result.returncode == 0, result.stderr

        manifest = root / "ai" / "manifest" / "codebase-map.json"
        assert manifest.exists()

        data = json.loads(manifest.read_text())
        assert data["managed"] is True
        assert "main.py" in data["entry_points"]
        assert "package.json" in data["dependency_managers"]
        assert data["directory_roles"]["src"] == "source"
        assert data["directory_roles"]["tests"] == "tests"
        assert data["metrics"]["total_files"] >= 2


def test_analyze_codebase_detects_monorepo():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / "apps" / "web").mkdir(parents=True)
        (root / "packages" / "ui").mkdir(parents=True)
        (root / "services" / "api").mkdir(parents=True)

        result = run_script("analyze_codebase.py", tmp)
        assert result.returncode == 0

        data = json.loads((root / "ai" / "manifest" / "codebase-map.json").read_text())
        assert data["repo_mode"] == "monorepo"


def test_analyze_codebase_detects_polyrepo():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / "src").mkdir()

        result = run_script("analyze_codebase.py", tmp)
        assert result.returncode == 0

        data = json.loads((root / "ai" / "manifest" / "codebase-map.json").read_text())
        assert data["repo_mode"] == "polyrepo"


def test_analyze_codebase_missing_dir():
    result = run_script("analyze_codebase.py", "/nonexistent/path")
    assert result.returncode != 0


# --- aggregate_experience tests ---

def test_aggregate_empty_experience():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        make_experience_tree(root)

        result = run_script("aggregate_experience.py", cwd=tmp)
        assert result.returncode == 0

        report = root / "ai" / "experience" / "reports" / "0dai-experience-report.json"
        assert report.exists()
        data = json.loads(report.read_text())
        assert data["events_total"] == 0


def test_aggregate_with_events():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        make_experience_tree(root)

        event = {"tool": "claude", "task_type": "bugfix", "candidate_type": "skill", "ci_passed": True}
        (root / "ai" / "experience" / "events" / "e1.json").write_text(json.dumps(event))

        result = run_script("aggregate_experience.py", cwd=tmp)
        assert result.returncode == 0

        data = json.loads((root / "ai" / "experience" / "reports" / "0dai-experience-report.json").read_text())
        assert data["events_total"] == 1
        assert data["by_tool"]["claude"] == 1
        assert data["ci_success_count"] == 1


# --- score_knowledge_intake tests ---

def test_score_intake():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        make_experience_tree(root)

        intake = {
            "events_total": 5,
            "candidate_types": {"skill": 2, "rule": 1},
            "repo": "test",
            "recommended_issue_type": "ai_lesson",
            "recommend_open_issue": True,
        }
        reports = root / "ai" / "experience" / "reports"
        (reports / "0dai-knowledge-intake.json").write_text(json.dumps(intake))

        result = run_script("score_knowledge_intake.py", cwd=tmp)
        assert result.returncode == 0

        scored = json.loads((reports / "0dai-knowledge-intake-scored.json").read_text())
        assert scored["score"] == 5 + 4 + 3  # min(5,10) + 2*2 + 1*3 = 12
        assert scored["confidence"] == "high"
        assert scored["recommend_open_issue"] is True


def test_score_intake_low_confidence():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        make_experience_tree(root)

        intake = {
            "events_total": 1,
            "candidate_types": {},
            "repo": "test",
            "recommended_issue_type": "ai_lesson",
            "recommend_open_issue": True,
        }
        reports = root / "ai" / "experience" / "reports"
        (reports / "0dai-knowledge-intake.json").write_text(json.dumps(intake))

        result = run_script("score_knowledge_intake.py", cwd=tmp)
        assert result.returncode == 0

        scored = json.loads((reports / "0dai-knowledge-intake-scored.json").read_text())
        assert scored["confidence"] == "low"
        assert scored["recommend_open_issue"] is False


def test_score_missing_intake():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        make_experience_tree(root)

        result = run_script("score_knowledge_intake.py", cwd=tmp)
        assert result.returncode != 0


# --- roadmap_guardian tests ---

def test_guardian_passes():
    result = run_script("roadmap_guardian.py")
    assert result.returncode == 0
    assert "guardian=pass" in result.stdout


# --- validate_templates tests ---

def test_validate_templates_passes():
    result = run_script("validate_templates.py")
    assert result.returncode == 0
    assert "template validation passed" in result.stdout


# --- malformed JSON handling ---

def test_aggregate_malformed_json():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        make_experience_tree(root)
        (root / "ai" / "experience" / "events" / "bad.json").write_text("{invalid json")

        result = run_script("aggregate_experience.py", cwd=tmp)
        # Should skip bad file gracefully with warning
        assert result.returncode == 0
        assert "warning" in result.stdout.lower() or "skipping" in result.stdout.lower()


# --- MCP server tests ---

def test_mcp_server_tools_on_initialized_project():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        # Initialize a project using bash
        bin_dir = SCRIPTS_DIR.parent / "bin"
        result = subprocess.run(
            [str(bin_dir / "0dai-repo"), "init-existing", "--target", tmp],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr

        # Test MCP tools by importing the module
        import importlib.util
        import asyncio

        old_argv = sys.argv[:]
        sys.argv = ["mcp_server.py", "--target", tmp]
        try:
            spec = importlib.util.spec_from_file_location(
                "mcp_server_test",
                str(SCRIPTS_DIR / "mcp_server.py"),
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            async def run_tools():
                r = mod.get_ai_version()
                if asyncio.iscoroutine(r): r = await r
                assert r["version"] == "0.3.3", f"unexpected version: {r}"

                r = mod.get_project_health()
                if asyncio.iscoroutine(r): r = await r
                assert r["ai_layer_installed"] is True
                assert r["manifests_present"]["project.yaml"] is True

                r = mod.get_codebase_map()
                if asyncio.iscoroutine(r): r = await r
                assert "error" not in r, f"codebase map error: {r}"
                assert "repo_mode" in r

                r = mod.search_experience("test")
                if asyncio.iscoroutine(r): r = await r
                assert "matches" in r

            asyncio.run(run_tools())
        finally:
            sys.argv = old_argv


# --- SDK tests ---

def test_sdk_on_initialized_project():
    with tempfile.TemporaryDirectory() as tmp:
        bin_dir = SCRIPTS_DIR.parent / "bin"
        subprocess.run([str(bin_dir / "0dai-repo"), "init-existing", "--target", tmp],
                       capture_output=True, text=True, check=True)

        sdk_path = SCRIPTS_DIR.parent / "sdk"
        old_path = sys.path[:]
        sys.path.insert(0, str(sdk_path))
        try:
            # Force reimport
            for mod_name in list(sys.modules):
                if mod_name.startswith("zerodayai"):
                    del sys.modules[mod_name]

            import zerodayai

            v = zerodayai.version(tmp)
            assert v["version"] is not None, f"version is None: {v}"

            h = zerodayai.health(tmp)
            assert h["ai_layer_installed"] is True
            assert h["manifests_present"]["project.yaml"] is True

            d = zerodayai.detect(tmp)
            assert "stack" in d

            m = zerodayai.codebase_map(tmp)
            assert "repo_mode" in m

            e = zerodayai.experience(tmp)
            assert "events" in e
        finally:
            sys.path[:] = old_path


def main() -> None:
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    passed = 0
    failed = 0
    for test in tests:
        name = test.__name__
        try:
            test()
            print(f"  PASS  {name}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {name}: {e}")
            failed += 1

    print(f"\n{passed + failed} tests: {passed} passed, {failed} failed")
    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
