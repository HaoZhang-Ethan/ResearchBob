from __future__ import annotations

import sys
from pathlib import Path


def _load_cli_main():
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "src"))
    from auto_research.cli import main as cli_main

    return cli_main


def main() -> int:
    cli_main = _load_cli_main()
    return cli_main(["validate-profile", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
