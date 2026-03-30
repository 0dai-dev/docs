#!/usr/bin/env python3
"""0dai Webhooks — trigger external systems on init/sync/audit events.

Register webhook URLs that receive POST notifications when 0dai operations happen.
Webhooks configured in ai/manifest/webhooks.json.

Usage:
    0dai webhook --target <path> add <url> [--events init,sync,audit]
    0dai webhook --target <path> list
    0dai webhook --target <path> remove <url>
    0dai webhook --target <path> test <url>
    0dai webhook --target <path> --json
"""
from __future__ import annotations

import json
import pathlib
import sys
import time
import urllib.request
import urllib.error


def _webhooks_path(target: pathlib.Path) -> pathlib.Path:
    return target / "ai" / "manifest" / "webhooks.json"


def _load(target: pathlib.Path) -> dict:
    p = _webhooks_path(target)
    if not p.is_file():
        return {"managed": True, "hooks": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"managed": True, "hooks": []}


def _save(target: pathlib.Path, data: dict) -> None:
    p = _webhooks_path(target)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())


ALL_EVENTS = ["init", "sync", "audit", "harvest", "promote", "deploy", "scan", "session"]


def fire_webhook(url: str, event: str, payload: dict, timeout: int = 10) -> dict:
    """Send POST to webhook URL."""
    body = json.dumps({
        "event": event,
        "timestamp": _now(),
        "payload": payload,
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json", "User-Agent": "0dai-webhook/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"status": resp.status, "ok": 200 <= resp.status < 300}
    except urllib.error.URLError as e:
        return {"status": 0, "ok": False, "error": str(e)}
    except Exception as e:
        return {"status": 0, "ok": False, "error": str(e)}


def fire_all(target: pathlib.Path, event: str, payload: dict) -> list[dict]:
    """Fire all webhooks registered for an event."""
    data = _load(target)
    results = []
    for hook in data.get("hooks", []):
        events = hook.get("events", ALL_EVENTS)
        if event in events or "all" in events:
            result = fire_webhook(hook["url"], event, payload)
            result["url"] = hook["url"]
            results.append(result)
    return results


def cmd_add(target: pathlib.Path, url: str, events: str) -> None:
    data = _load(target)
    for h in data["hooks"]:
        if h["url"] == url:
            print(f"[0dai] webhook already registered: {url}")
            return
    event_list = [e.strip() for e in events.split(",")] if events else ALL_EVENTS
    data["hooks"].append({
        "url": url,
        "events": event_list,
        "added": _now(),
    })
    _save(target, data)
    print(f"[0dai] webhook added: {url}")
    print(f"  Events: {', '.join(event_list)}")


def cmd_list(target: pathlib.Path) -> None:
    data = _load(target)
    hooks = data.get("hooks", [])
    if not hooks:
        print("[0dai] no webhooks registered")
        return
    print(f"Webhooks ({len(hooks)}):")
    for h in hooks:
        events = ", ".join(h.get("events", []))
        print(f"  {h['url']}")
        print(f"    Events: {events}")


def cmd_remove(target: pathlib.Path, url: str) -> None:
    data = _load(target)
    before = len(data["hooks"])
    data["hooks"] = [h for h in data["hooks"] if h["url"] != url]
    if len(data["hooks"]) < before:
        _save(target, data)
        print(f"[0dai] webhook removed: {url}")
    else:
        print(f"[0dai] webhook not found: {url}")


def cmd_test(target: pathlib.Path, url: str) -> None:
    result = fire_webhook(url, "test", {"message": "0dai webhook test"})
    if result["ok"]:
        print(f"[0dai] webhook OK: {url} (status {result['status']})")
    else:
        print(f"[0dai] webhook FAILED: {url} ({result.get('error', 'unknown')})")


def cmd_json(target: pathlib.Path) -> None:
    print(json.dumps(_load(target), indent=2, ensure_ascii=False))


def main() -> None:
    target = pathlib.Path(".")
    subcmd = "list"
    url = ""
    events = ""
    json_mode = False
    args = sys.argv[1:]

    i = 0
    while i < len(args):
        if args[i] == "--target" and i + 1 < len(args):
            target = pathlib.Path(args[i + 1]).resolve()
            i += 2
        elif args[i] == "--events" and i + 1 < len(args):
            events = args[i + 1]
            i += 2
        elif args[i] == "--json":
            json_mode = True
            i += 1
        elif args[i] in ("add", "list", "remove", "test"):
            subcmd = args[i]
            i += 1
        elif not args[i].startswith("-") and not url:
            url = args[i]
            i += 1
        else:
            i += 1

    if json_mode:
        cmd_json(target)
    elif subcmd == "add" and url:
        cmd_add(target, url, events)
    elif subcmd == "remove" and url:
        cmd_remove(target, url)
    elif subcmd == "test" and url:
        cmd_test(target, url)
    else:
        cmd_list(target)


if __name__ == "__main__":
    main()
