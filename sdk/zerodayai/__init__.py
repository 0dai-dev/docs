"""ZeroDayAI Python SDK — programmatic access to the ai/ operating layer."""

from zerodayai.core import (
    agent_teams,
    detect,
    health,
    manifests,
    codebase_map,
    experience,
    specs,
    version,
)

import pathlib as _pathlib
_ver_file = _pathlib.Path(__file__).resolve().parent.parent.parent / "VERSION"
__version__ = _ver_file.read_text().strip() if _ver_file.is_file() else "1.0.0"
__all__ = ["agent_teams", "detect", "health", "manifests", "codebase_map", "experience", "specs", "version"]
