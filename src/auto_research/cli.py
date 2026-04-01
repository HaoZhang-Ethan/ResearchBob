from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from auto_research.intake import run_intake
from auto_research.profile import validate_interest_profile_text
from auto_research.workspace import ensure_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auto-research")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_workspace = subparsers.add_parser("init-workspace")
    init_workspace.add_argument("--workspace", default="research-workspace")

    validate_profile = subparsers.add_parser("validate-profile")
    validate_profile.add_argument("path")

    intake = subparsers.add_parser("intake")
    intake.add_argument("--workspace", default="research-workspace")
    intake.add_argument("--profile", default="research-workspace/profile/interest-profile.md")
    intake.add_argument("--max-results", type=int, default=25)

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
        profile_path = Path(args.path)
        if not profile_path.exists():
            print(f"Profile path does not exist: {args.path}", file=sys.stderr)
            return 1
        if not profile_path.is_file():
            print(f"Profile path is not a file: {args.path}", file=sys.stderr)
            return 1
        text = profile_path.read_text(encoding="utf-8")
        errors = validate_interest_profile_text(text)
        if errors:
            for error in errors:
                print(error)
            return 1
        print("interest profile is valid")
        return 0

    if args.command == "intake":
        entries = run_intake(
            workspace=Path(args.workspace),
            profile_path=Path(args.profile),
            max_results=args.max_results,
        )
        print(f"ingested {len(entries)} papers")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
