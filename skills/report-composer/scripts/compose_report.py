from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def run() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from auto_research.cli import main as cli_main

    return cli_main(["compose-report", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(run())
