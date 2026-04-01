from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from auto_research.profile import validate_interest_profile_text
from auto_research.workspace import ensure_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auto-research")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_workspace = subparsers.add_parser("init-workspace")
    init_workspace.add_argument("--workspace", default="research-workspace")

    validate_profile = subparsers.add_parser("validate-profile")
    validate_profile.add_argument("path")
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

    if args.command == "validate-profile":
        path = Path(args.path)
        if not path.is_file():
            print(f"Profile path does not exist: {path}", file=sys.stderr)
            return 1

        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Unable to read profile: {exc}", file=sys.stderr)
            return 1

        errors = validate_interest_profile_text(text)
        if errors:
            for error in errors:
                print(error)
            return 1
        print("interest profile is valid")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
