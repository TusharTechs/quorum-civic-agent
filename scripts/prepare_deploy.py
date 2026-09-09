"""Vendor the quorum package into the deployment directory.

AgentCore's CodeZip build installs with source distributions disabled, so a
`quorum @ git+https://...` dependency cannot resolve - uv refuses to build it.
The package is therefore copied into the app directory immediately before
packaging.

`src/quorum` remains the single source of truth; the copy is generated, is
gitignored, and is refreshed on every deploy. Run this before `agentcore deploy`.
"""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "quorum"
TARGET = ROOT / "deploy" / "app" / "quorumAgent" / "quorum"

IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".venv")


def main() -> int:
    if not SOURCE.is_dir():
        print(f"source package not found: {SOURCE}", file=sys.stderr)
        return 1

    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(SOURCE, TARGET, ignore=IGNORE)

    # The Cedar policy and household profile ship as package data, and the
    # deployed copy has no repository to fall back to.
    data = TARGET / "_data"
    data.mkdir(exist_ok=True)
    shutil.copy2(ROOT / "policy" / "quorum.cedar", data / "quorum.cedar")
    shutil.copy2(ROOT / "config" / "household.json", data / "household.json")

    modules = sorted(p.name for p in TARGET.glob("*.py"))
    print(f"vendored {len(modules)} modules into {TARGET.relative_to(ROOT)}")
    print(f"  {', '.join(modules)}")
    print(f"  _data: {', '.join(sorted(p.name for p in data.iterdir()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
