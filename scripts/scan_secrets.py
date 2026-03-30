#!/usr/bin/env python3
"""0dai Sensitive Data Scanner — detect secrets, API keys, PII in ai/ layer.

Scans ai/ configs for leaked credentials, tokens, private keys, and
sensitive patterns. Integrates with compliance reporting and policy engine.

Usage:
    0dai scan --target <path>              # scan and report
    0dai scan --target <path> --json       # JSON output
    0dai scan --target <path> --fix        # redact found secrets
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

# --- Detection patterns ---

PATTERNS: list[tuple[str, str, str, re.Pattern]] = [
    # (id, severity, description, compiled regex)
    ("aws-access-key", "critical", "AWS Access Key ID",
     re.compile(r"(?:AKIA|ASIA)[0-9A-Z]{16}")),
    ("aws-secret-key", "critical", "AWS Secret Access Key",
     re.compile(r"""(?:aws_secret_access_key|secret_key)\s*[=:]\s*['"]?([A-Za-z0-9/+=]{40})['"]?""")),
    ("gcp-api-key", "critical", "Google Cloud API Key",
     re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    ("stripe-key", "critical", "Stripe API Key",
     re.compile(r"(?:sk|pk)_(?:live|test)_[0-9a-zA-Z]{24,}")),
    ("openai-key", "critical", "OpenAI API Key",
     re.compile(r"sk-[a-zA-Z0-9]{20,}")),
    ("anthropic-key", "critical", "Anthropic API Key",
     re.compile(r"sk-ant-[a-zA-Z0-9_-]{20,}")),
    ("github-pat", "critical", "GitHub Personal Access Token",
     re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}")),
    ("private-key", "critical", "Private Key",
     re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("jwt-token", "high", "JWT Token",
     re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+")),
    ("bearer-token", "high", "Bearer Token in config",
     re.compile(r"""(?:bearer|authorization)\s*[=:]\s*['"]?Bearer\s+[A-Za-z0-9._-]{20,}['"]?""", re.IGNORECASE)),
    ("password-in-config", "high", "Password in config file",
     re.compile(r"""(?:password|passwd|pwd)\s*[=:]\s*['"]?[^\s'"]{8,}['"]?""", re.IGNORECASE)),
    ("secret-in-config", "high", "Secret/token value in config",
     re.compile(r"""(?:secret|token|api_key|apikey)\s*[=:]\s*['"]?[A-Za-z0-9_/+=.-]{16,}['"]?""", re.IGNORECASE)),
    ("connection-string", "high", "Database connection string",
     re.compile(r"""(?:postgres|mysql|mongodb|redis)://[^\s'"]{10,}""", re.IGNORECASE)),
    ("env-with-value", "medium", ".env variable with hardcoded value",
     re.compile(r"""^[A-Z_]{3,}=(?![\s${\(])[^\s]{8,}""", re.MULTILINE)),
]

# Files to skip
SKIP_EXTENSIONS = {".pyc", ".pyo", ".so", ".dll", ".exe", ".bin", ".png", ".jpg", ".gif", ".ico", ".woff", ".woff2"}
SKIP_NAMES = {"applied-lock.json", ".history.json", "wal.jsonl", "audit.jsonl"}


def scan_file(path: pathlib.Path, rel: str) -> list[dict]:
    """Scan a single file for sensitive patterns."""
    findings = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings

    for pat_id, severity, description, regex in PATTERNS:
        for match in regex.finditer(text):
            # Get line number
            line_num = text[:match.start()].count("\n") + 1
            # Get matched text (truncated for safety)
            matched = match.group(0)
            redacted = matched[:8] + "..." + matched[-4:] if len(matched) > 16 else "***"

            findings.append({
                "file": rel,
                "line": line_num,
                "pattern": pat_id,
                "severity": severity,
                "description": description,
                "match_preview": redacted,
            })

    return findings


def scan_target(target: pathlib.Path) -> dict:
    """Scan all files in ai/ directory."""
    ai_dir = target / "ai"
    findings: list[dict] = []
    files_scanned = 0

    # Also scan root config files
    scan_dirs = [ai_dir]
    scan_files = [
        target / ".env", target / ".env.local",
        target / ".env.ai", target / ".env.observability",
    ]

    for scan_dir in scan_dirs:
        if not scan_dir.is_dir():
            continue
        for path in scan_dir.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix in SKIP_EXTENSIONS:
                continue
            if path.name in SKIP_NAMES:
                continue
            if path.stat().st_size > 1_000_000:  # Skip files > 1MB
                continue

            rel = str(path.relative_to(target))
            file_findings = scan_file(path, rel)
            findings.extend(file_findings)
            files_scanned += 1

    for scan_file_path in scan_files:
        if scan_file_path.is_file():
            rel = str(scan_file_path.relative_to(target))
            file_findings = scan_file(scan_file_path, rel)
            findings.extend(file_findings)
            files_scanned += 1

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda f: (severity_order.get(f["severity"], 9), f["file"], f["line"]))

    by_severity: dict[str, int] = {}
    for f in findings:
        by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1

    return {
        "files_scanned": files_scanned,
        "total_findings": len(findings),
        "by_severity": by_severity,
        "clean": len(findings) == 0,
        "findings": findings,
    }


def fix_secrets(target: pathlib.Path) -> dict:
    """Redact found secrets in files."""
    result = scan_target(target)
    if result["clean"]:
        return {"fixed": 0, "message": "No secrets found"}

    fixed_files: set[str] = set()
    for finding in result["findings"]:
        file_path = target / finding["file"]
        if not file_path.is_file():
            continue
        try:
            text = file_path.read_text(encoding="utf-8")
        except OSError:
            continue

        pat_id = finding["pattern"]
        for _, _, _, regex in PATTERNS:
            text = regex.sub("<REDACTED>", text)

        file_path.write_text(text, encoding="utf-8")
        fixed_files.add(finding["file"])

    return {"fixed": len(fixed_files), "files": sorted(fixed_files)}


def cmd_scan(target: pathlib.Path) -> None:
    result = scan_target(target)

    if result["clean"]:
        print(f"[0dai] scan clean: {result['files_scanned']} files, no secrets found")
        return

    print(f"[0dai] SECRETS DETECTED: {result['total_findings']} finding(s) in {result['files_scanned']} files")
    print()

    for sev in ["critical", "high", "medium"]:
        count = result["by_severity"].get(sev, 0)
        if count:
            marker = "!!!" if sev == "critical" else "!" if sev == "high" else "."
            print(f"  {marker} {sev}: {count}")

    print()
    print(f"{'Severity':<10} {'File':<40} {'Line':<6} {'Pattern':<22} Preview")
    print("-" * 100)
    for f in result["findings"]:
        print(f"{f['severity']:<10} {f['file']:<40} {f['line']:<6} {f['pattern']:<22} {f['match_preview']}")

    print(f"\nRun '0dai scan --target <path> --fix' to redact found secrets.")


def cmd_json(target: pathlib.Path) -> None:
    print(json.dumps(scan_target(target), indent=2, ensure_ascii=False))


def cmd_fix(target: pathlib.Path) -> None:
    result = fix_secrets(target)
    if result["fixed"] == 0:
        print("[0dai] no secrets to fix")
    else:
        print(f"[0dai] redacted secrets in {result['fixed']} file(s):")
        for f in result.get("files", []):
            print(f"  {f}")


def main() -> None:
    target = pathlib.Path(".")
    json_mode = False
    fix_mode = False
    args = sys.argv[1:]

    i = 0
    while i < len(args):
        if args[i] == "--target" and i + 1 < len(args):
            target = pathlib.Path(args[i + 1]).resolve()
            i += 2
        elif args[i] == "--json":
            json_mode = True
            i += 1
        elif args[i] == "--fix":
            fix_mode = True
            i += 1
        else:
            i += 1

    if json_mode:
        cmd_json(target)
    elif fix_mode:
        cmd_fix(target)
    else:
        cmd_scan(target)


if __name__ == "__main__":
    main()
