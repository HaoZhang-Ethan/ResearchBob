from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from auto_research.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["validate-profile", *sys.argv[1:]]))
