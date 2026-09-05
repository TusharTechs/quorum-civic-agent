"""Where the package finds its data, in a repo checkout and when installed.

Modules used to resolve paths relative to the source tree, which works from a
checkout and breaks the moment the package is installed into site-packages or
zipped into a runtime. Each location is resolved in the same order:

    1. an explicit environment variable  (deployment wins)
    2. data bundled inside the package   (installed wheel)
    3. the repository checkout           (local development)

The cache falls back to a temp directory, because a read-only or unwritable
deployment must still run.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
BUNDLED = PACKAGE_DIR / "_data"

# .../src/quorum/paths.py -> repository root. Only meaningful in a checkout.
REPO_ROOT = PACKAGE_DIR.parents[1]


def _first_existing(*candidates: Path | None) -> Path | None:
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate
    return None


def _from_env(name: str) -> Path | None:
    value = os.environ.get(name)
    return Path(value) if value else None


def cache_dir() -> Path:
    """Where parsed packets are cached. Created if missing.

    Parsing is expensive and packets never change once published, so the cache
    is load-bearing rather than an optimisation.
    """
    target = _from_env("QUORUM_CACHE_DIR") or (REPO_ROOT / "data" / "cache")
    try:
        target.mkdir(parents=True, exist_ok=True)
        probe = target / ".writable"
        probe.touch()
        probe.unlink()
        return target
    except OSError:
        fallback = Path(tempfile.gettempdir()) / "quorum-cache"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def profile_path() -> Path:
    """The household profile."""
    found = _first_existing(
        _from_env("QUORUM_PROFILE"),
        BUNDLED / "household.json",
        REPO_ROOT / "config" / "household.json",
    )
    if found is None:
        raise FileNotFoundError(
            "No household profile found. Set QUORUM_PROFILE to a JSON file."
        )
    return found


def policy_file() -> Path:
    """The Cedar policy that governs whether an action may be taken."""
    found = _first_existing(
        _from_env("QUORUM_POLICY"),
        BUNDLED / "quorum.cedar",
        REPO_ROOT / "policy" / "quorum.cedar",
    )
    if found is None:
        raise FileNotFoundError(
            "No Cedar policy found. Set QUORUM_POLICY to a .cedar file. "
            "Refusing to run without one: an action gate that cannot load its "
            "policy must fail closed, not open."
        )
    return found
