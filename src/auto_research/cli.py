from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Sequence

import httpx

from auto_research.extraction import validate_extraction_document
from auto_research.intake import run_intake
from auto_research.profile import (
    parse_interest_profile_text,
    validate_interest_profile_text,
)
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
    intake.add_argument("--profile")
    intake.add_argument("--max-results", type=int, default=25)

    validate_extraction = subparsers.add_parser("validate-extraction")
    validate_extraction.add_argument("path")

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
        try:
            text = profile_path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Unable to read profile: {exc}", file=sys.stderr)
            return 1
        errors = validate_interest_profile_text(text)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print("interest profile is valid")
        return 0

    if args.command == "intake":
        workspace = Path(args.workspace)
        profile_path = (
            Path(args.profile)
            if args.profile is not None
            else workspace / "profile" / "interest-profile.md"
        )
        try:
            profile_text = profile_path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Unable to read intake profile: {exc}", file=sys.stderr)
            return 1
        try:
            parse_interest_profile_text(profile_text)
        except ValueError as exc:
            print(f"Invalid intake profile: {exc}", file=sys.stderr)
            return 1
        try:
            entries = run_intake(
                workspace=workspace,
                profile_path=profile_path,
                max_results=args.max_results,
            )
        except httpx.HTTPError as exc:
            print(f"Unable to fetch arXiv papers: {exc}", file=sys.stderr)
            return 1
        except ET.ParseError as exc:
            print(f"Unable to parse arXiv feed: {exc}", file=sys.stderr)
            return 1
        except OSError as exc:
            print(f"Intake failed: {exc}", file=sys.stderr)
            return 1
        print(f"ingested {len(entries)} papers")
        return 0

    if args.command == "validate-extraction":
        extraction_path = Path(args.path)
        if not extraction_path.exists():
            print(f"Problem-solution path does not exist: {args.path}", file=sys.stderr)
            return 1
        if not extraction_path.is_file():
            print(f"Problem-solution path is not a file: {args.path}", file=sys.stderr)
            return 1
        try:
            text = extraction_path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Unable to read extraction path: {exc}", file=sys.stderr)
            return 1
        errors = validate_extraction_document(text)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print("problem-solution artifact is valid")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
