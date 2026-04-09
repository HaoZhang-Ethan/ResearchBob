from __future__ import annotations

import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Sequence

import httpx

from auto_research.env import load_env_file
from auto_research.extraction import validate_extraction_document
from auto_research.github_intake import IssueSyncConfig, sync_issues
from auto_research.intake import IntakeDataError, IntakeProfileError, run_intake
from auto_research.profile import validate_interest_profile_text
from auto_research.registry import RegistryCorruptionError
from auto_research.report import compose_report
from auto_research.workspace import ensure_workspace
from auto_research.automation import PipelineConfig, finalize_github, run_daily_pipeline


def _raw_argv(argv: Sequence[str] | None) -> list[str]:
    return list(sys.argv[1:] if argv is None else argv)


def _profile_path_was_overridden(argv: Sequence[str]) -> bool:
    return any(argument == "--profile" or argument.startswith("--profile=") for argument in argv)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auto-research")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_workspace = subparsers.add_parser("init-workspace")
    init_workspace.add_argument("--workspace", default="research-workspace")

    validate_profile = subparsers.add_parser("validate-profile")
    validate_profile.add_argument("path")

    intake = subparsers.add_parser("intake")
    intake.add_argument("--workspace", default="research-workspace")
    intake.add_argument(
        "--profile",
        default="research-workspace/profile/interest-profile.md",
    )
    intake.add_argument("--max-results", type=int, default=25)

    validate_extraction = subparsers.add_parser("validate-extraction")
    validate_extraction.add_argument("path")

    compose = subparsers.add_parser("compose-report")
    compose.add_argument("--workspace", default="research-workspace")
    compose.add_argument("--direction")
    compose.add_argument("--mode", choices=("daily", "manual"), default="daily")
    compose.add_argument("--label", required=True)

    pipeline = subparsers.add_parser("daily-pipeline")
    pipeline.add_argument("--workspace", default="research-workspace")
    pipeline.add_argument("--direction")
    pipeline.add_argument("--profile", default="research-workspace/profile/interest-profile.md")
    pipeline.add_argument("--max-results", type=int, default=20)
    pipeline.add_argument("--prefilter-limit", type=int, default=15)
    pipeline.add_argument("--top-k", type=int, default=10)
    pipeline.add_argument("--label")
    pipeline.add_argument("--model")
    pipeline.add_argument("--overwrite-summaries", action="store_true")
    pipeline.add_argument("--push", action="store_true")

    sync_issues_parser = subparsers.add_parser("sync-issues")
    sync_issues_parser.add_argument("--workspace", default="research-workspace")
    sync_issues_parser.add_argument("--repo")
    sync_issues_parser.add_argument("--state", choices=("open", "all"), default="open")
    sync_issues_parser.add_argument("--limit", type=int, default=100)
    sync_issues_parser.add_argument("--push", action="store_true")

    finalize_parser = subparsers.add_parser("finalize-github")
    finalize_parser.add_argument("--workspace", default="research-workspace")
    finalize_parser.add_argument("--direction")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    load_env_file(Path.cwd() / ".env.local")
    raw_argv = _raw_argv(argv)
    parser = build_parser()
    args = parser.parse_args(raw_argv)

    if args.command == "init-workspace":
        try:
            ensure_workspace(Path(args.workspace))
        except OSError as exc:
            print(f"Unable to initialize workspace: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.command == "validate-profile":
        profile_path = Path(args.path)
        if profile_path.is_symlink():
            print(f"Profile path is a symlink: {args.path}", file=sys.stderr)
            return 1
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
        except UnicodeError:
            print(f"Profile is not valid UTF-8: {args.path}", file=sys.stderr)
            return 1
        errors = validate_interest_profile_text(text)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print("interest profile is valid")
        return 0

    if args.command == "intake":
        if args.max_results <= 0:
            print("Invalid --max-results: must be a positive integer", file=sys.stderr)
            return 1
        workspace = Path(args.workspace)
        profile_path = (
            Path(args.profile)
            if _profile_path_was_overridden(raw_argv)
            else workspace / "profile" / "interest-profile.md"
        )
        if profile_path.is_symlink():
            print(f"Unable to read intake profile: symlinked file: {profile_path}", file=sys.stderr)
            return 1
        if not profile_path.exists():
            print(f"Unable to read intake profile: {profile_path}", file=sys.stderr)
            return 1
        if not profile_path.is_file():
            print(f"Unable to read intake profile: {profile_path}", file=sys.stderr)
            return 1
        try:
            entries = run_intake(
                workspace=workspace,
                profile_path=profile_path,
                max_results=args.max_results,
            )
        except RegistryCorruptionError as exc:
            print(f"Registry is corrupted: {exc}", file=sys.stderr)
            return 1
        except OSError as exc:
            print(f"Intake failed: {exc}", file=sys.stderr)
            return 1
        except IntakeProfileError as exc:
            print(f"Invalid intake profile: {exc}", file=sys.stderr)
            return 1
        except IntakeDataError as exc:
            print(f"Invalid intake data: {exc}", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(f"Intake failed: {exc}", file=sys.stderr)
            return 1
        except httpx.HTTPError as exc:
            print(f"Unable to fetch arXiv papers: {exc}", file=sys.stderr)
            return 1
        except ET.ParseError as exc:
            print(f"arXiv feed parse failed: {exc}", file=sys.stderr)
            return 1
        print(f"ingested {len(entries)} papers")
        return 0

    if args.command == "validate-extraction":
        extraction_path = Path(args.path)
        if extraction_path.is_symlink():
            print(f"Extraction artifact path is a symlink: {args.path}", file=sys.stderr)
            return 1
        if not extraction_path.exists():
            print(f"Extraction artifact path does not exist: {args.path}", file=sys.stderr)
            return 1
        if not extraction_path.is_file():
            print(f"Extraction artifact path is not a file: {args.path}", file=sys.stderr)
            return 1
        try:
            text = extraction_path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Unable to read extraction artifact: {exc}", file=sys.stderr)
            return 1
        except UnicodeError:
            print(f"Extraction artifact is not valid UTF-8: {args.path}", file=sys.stderr)
            return 1
        errors = validate_extraction_document(text)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print("problem-solution artifact is valid")
        return 0

    if args.command == "compose-report":
        try:
            workspace = Path(args.workspace)
            if args.direction:
                workspace = workspace / "directions" / args.direction
            report_path = compose_report(
                workspace=workspace,
                mode=args.mode,
                label=args.label,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        except OSError as exc:
            print(f"Unable to write report: {exc}", file=sys.stderr)
            return 1
        print(report_path)
        return 0

    if args.command == "daily-pipeline":
        try:
            result = run_daily_pipeline(
                PipelineConfig(
                    workspace=Path(args.workspace),
                    direction=args.direction,
                    profile_path=(
                        Path(args.profile)
                        if _profile_path_was_overridden(raw_argv)
                        else None
                    ),
                    max_results=args.max_results,
                    prefilter_limit=args.prefilter_limit,
                    top_k=args.top_k,
                    label=args.label,
                    model=args.model,
                    overwrite_summaries=args.overwrite_summaries,
                    push=args.push,
                )
            )
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"Daily pipeline failed: {exc}", file=sys.stderr)
            return 1
        print(result.report_path)
        print(result.ris_path)
        return 0

    if args.command == "sync-issues":
        if args.limit <= 0:
            print("Invalid --limit: must be a positive integer", file=sys.stderr)
            return 1
        try:
            result = sync_issues(
                IssueSyncConfig(
                    workspace=Path(args.workspace),
                    repo=args.repo,
                    state=args.state,
                    limit=args.limit,
                    push=args.push,
                )
            )
        except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
            print(f"Issue sync failed: {exc}", file=sys.stderr)
            return 1
        print(
            " ".join(
                [
                    f"inspected_issues={result.inspected_issue_count}",
                    f"parsed_issues={result.parsed_issue_count}",
                    f"changed_requests={result.changed_request_count}",
                ]
            )
        )
        for summary_path in result.refreshed_summaries:
            print(summary_path)
        return 0

    if args.command == "finalize-github":
        try:
            result = finalize_github(Path(args.workspace), direction=args.direction)
        except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
            print(f"GitHub finalize failed: {exc}", file=sys.stderr)
            return 1
        print(
            " ".join(
                [
                    f"status={result.get('status', '')}",
                    f"label={result.get('label', '')}",
                    f"consumed_issues={len(result.get('consumed_issue_numbers', []))}",
                ]
            )
        )
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
