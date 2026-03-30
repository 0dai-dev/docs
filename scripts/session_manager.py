#!/usr/bin/env python3
"""0dai Session Roaming — transfer context between AI agent CLIs.

Start a task in Claude Code, continue in Codex, finish in Gemini.
Session state persisted in ai/sessions/active.json.

Usage:
    0dai session --target <path> save --summary "half done"    # save session
    0dai session --target <path> status                         # show active session
    0dai session --target <path> complete                       # archive session
    0dai session --target <path> history                        # past sessions
    0dai session --target <path> --json                         # JSON output
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time


def _sessions_dir(target: pathlib.Path) -> pathlib.Path:
    return target / "ai" / "sessions"


def _active_path(target: pathlib.Path) -> pathlib.Path:
    return _sessions_dir(target) / "active.json"


def _archive_dir(target: pathlib.Path) -> pathlib.Path:
    return _sessions_dir(target) / "archive"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())


def _today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _user() -> str:
    return os.environ.get("USER", os.environ.get("USERNAME", "unknown"))


def _detect_agent() -> str:
    """Best-effort detection of which agent CLI invoked us."""
    parent = os.environ.get("CLAUDE_CODE", "")
    if parent:
        return "claude"
    if os.environ.get("CODEX_CLI"):
        return "codex"
    if os.environ.get("GEMINI_CLI"):
        return "gemini"
    # Fallback: check parent process name
    try:
        ppid = os.getppid()
        cmdline = pathlib.Path(f"/proc/{ppid}/cmdline").read_text().replace("\x00", " ").lower()
        for agent in ("claude", "codex", "opencode", "gemini", "aider"):
            if agent in cmdline:
                return agent
    except (OSError, FileNotFoundError):
        pass
    return "cli"


def _git_changed_files(target: pathlib.Path) -> list[str]:
    """Get recently modified files from git."""
    try:
        r = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~3", "HEAD"],
            capture_output=True, text=True, cwd=str(target), timeout=5,
        )
        if r.returncode == 0:
            return [f for f in r.stdout.strip().splitlines() if f][:20]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def load_active(target: pathlib.Path) -> dict | None:
    path = _active_path(target)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_active(target: pathlib.Path, session: dict) -> None:
    path = _active_path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(session, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def cmd_save(target: pathlib.Path, summary: str, goal: str, plan: str) -> None:
    """Save or update active session."""
    agent = _detect_agent()
    existing = load_active(target)

    if existing:
        # Update existing session
        existing["current_agent"] = agent
        existing["updated"] = _now()
        if summary:
            existing["handoff_notes"] = summary
        existing.setdefault("history", []).append({
            "agent": agent,
            "action": f"session updated: {summary[:60]}" if summary else "session updated",
            "time": _now(),
            "user": _user(),
        })
        if goal:
            existing.setdefault("task", {})["goal"] = goal
        # Refresh files
        existing.setdefault("context", {})["files_touched"] = _git_changed_files(target)
        save_active(target, existing)
        print(f"[0dai] session updated (agent: {agent})")
        if summary:
            print(f"[0dai] handoff: {summary}")
    else:
        # Create new session
        session = {
            "id": f"sess-{int(time.time())}",
            "started": _now(),
            "started_by": agent,
            "current_agent": agent,
            "updated": _now(),
            "user": _user(),
            "task": {
                "goal": goal or summary or "Active development session",
                "status": "in_progress",
                "plan": [s.strip() for s in plan.split(",") if s.strip()] if plan else [],
                "completed_steps": [],
            },
            "context": {
                "files_touched": _git_changed_files(target),
                "key_decisions": [],
                "blockers": [],
            },
            "handoff_notes": summary or "",
            "history": [{
                "agent": agent,
                "action": "session started",
                "time": _now(),
                "user": _user(),
            }],
        }
        save_active(target, session)
        print(f"[0dai] session started (agent: {agent}, id: {session['id']})")
        if summary:
            print(f"[0dai] goal: {summary}")


def cmd_status(target: pathlib.Path) -> None:
    """Show active session."""
    session = load_active(target)
    if not session:
        print("[0dai] no active session")
        print("  Start one: 0dai session --target . save --summary 'what you are doing'")
        return

    task = session.get("task", {})
    ctx = session.get("context", {})
    history = session.get("history", [])

    print(f"Active Session: {session.get('id', '?')}")
    print(f"  Started: {session.get('started', '?')[:16]} by {session.get('started_by', '?')}")
    print(f"  Current agent: {session.get('current_agent', '?')}")
    print(f"  User: {session.get('user', '?')}")
    print(f"\n  Goal: {task.get('goal', '—')}")
    print(f"  Status: {task.get('status', '?')}")

    plan = task.get("plan", [])
    if plan:
        print(f"  Plan:")
        completed = task.get("completed_steps", [])
        for i, step in enumerate(plan):
            mark = "x" if i in completed else " "
            print(f"    [{mark}] {step}")

    files = ctx.get("files_touched", [])
    if files:
        print(f"\n  Files touched ({len(files)}):")
        for f in files[:10]:
            print(f"    {f}")

    notes = session.get("handoff_notes")
    if notes:
        print(f"\n  Handoff notes: {notes}")

    if history:
        print(f"\n  History ({len(history)}):")
        for h in history[-5:]:
            print(f"    [{h.get('agent', '?')}] {h.get('action', '')} — {h.get('time', '')[:16]}")


def cmd_complete(target: pathlib.Path) -> None:
    """Archive active session."""
    session = load_active(target)
    if not session:
        print("[0dai] no active session to complete")
        return

    session["completed"] = _now()
    session["task"]["status"] = "done"
    session.setdefault("history", []).append({
        "agent": _detect_agent(),
        "action": "session completed",
        "time": _now(),
        "user": _user(),
    })

    # Archive
    archive = _archive_dir(target)
    archive.mkdir(parents=True, exist_ok=True)
    archive_name = f"{session.get('id', 'session')}.json"
    (archive / archive_name).write_text(
        json.dumps(session, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Remove active
    _active_path(target).unlink()
    print(f"[0dai] session {session.get('id', '?')} completed and archived")


def cmd_history(target: pathlib.Path) -> None:
    """List past sessions."""
    archive = _archive_dir(target)
    if not archive.is_dir():
        print("[0dai] no session history")
        return

    files = sorted(archive.glob("*.json"), reverse=True)
    if not files:
        print("[0dai] no session history")
        return

    print(f"{'ID':<22} {'Goal':<40} {'Agents':<20} Duration")
    print("-" * 95)
    for f in files[:15]:
        try:
            s = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        goal = s.get("task", {}).get("goal", "—")[:38]
        agents_used = sorted({h.get("agent", "?") for h in s.get("history", [])})
        agents_str = ", ".join(agents_used)
        sid = s.get("id", f.stem)
        print(f"{sid:<22} {goal:<40} {agents_str:<20}")

    print(f"\n{len(files)} session(s) total")


def cmd_json(target: pathlib.Path) -> None:
    """JSON output of active session + history summary."""
    active = load_active(target)
    archive = _archive_dir(target)
    archived = []
    if archive.is_dir():
        for f in sorted(archive.glob("*.json"), reverse=True)[:10]:
            try:
                s = json.loads(f.read_text(encoding="utf-8"))
                archived.append({
                    "id": s.get("id"),
                    "goal": s.get("task", {}).get("goal"),
                    "agents": sorted({h.get("agent") for h in s.get("history", [])}),
                    "started": s.get("started"),
                    "completed": s.get("completed"),
                })
            except (json.JSONDecodeError, OSError):
                continue
    print(json.dumps({
        "active": active,
        "archived": archived,
        "has_active": active is not None,
    }, indent=2, ensure_ascii=False))


def main() -> None:
    target = pathlib.Path(".")
    subcmd = "status"
    summary = ""
    goal = ""
    plan = ""
    json_mode = False
    args = sys.argv[1:]

    i = 0
    while i < len(args):
        if args[i] == "--target" and i + 1 < len(args):
            target = pathlib.Path(args[i + 1]).resolve()
            i += 2
        elif args[i] == "--summary" and i + 1 < len(args):
            summary = args[i + 1]
            i += 2
        elif args[i] == "--goal" and i + 1 < len(args):
            goal = args[i + 1]
            i += 2
        elif args[i] == "--plan" and i + 1 < len(args):
            plan = args[i + 1]
            i += 2
        elif args[i] == "--json":
            json_mode = True
            i += 1
        elif args[i] in ("save", "status", "complete", "history"):
            subcmd = args[i]
            i += 1
        else:
            i += 1

    if json_mode:
        cmd_json(target)
    elif subcmd == "save":
        cmd_save(target, summary, goal, plan)
    elif subcmd == "complete":
        cmd_complete(target)
    elif subcmd == "history":
        cmd_history(target)
    else:
        cmd_status(target)


if __name__ == "__main__":
    main()
