from __future__ import annotations

import sys
from pathlib import Path

def _main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "src"))

    from auto_research.cli import main

    return main(["intake", *argv])


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
