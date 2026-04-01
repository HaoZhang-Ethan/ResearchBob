from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from auto_research.workspace import ensure_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auto-research")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_workspace = subparsers.add_parser("init-workspace")
    init_workspace.add_argument("--workspace", default="research-workspace")

    subparsers.add_parser("validate-profile")
    subparsers.add_parser("intake")
    subparsers.add_parser("validate-extraction")
    subparsers.add_parser("compose-report")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-workspace":
        ensure_workspace(Path(args.workspace))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
