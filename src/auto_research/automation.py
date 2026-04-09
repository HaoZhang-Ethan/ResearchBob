from __future__ import annotations
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import httpx

from auto_research.analysis import build_detailed_analysis, render_detailed_analysis_markdown
from auto_research.extraction import validate_extraction_document
from auto_research.github_intake import (
    build_fallback_profile_from_issue_intake,
    close_issue,
    comment_on_issue,
    discover_issue_directions,
    discover_github_repo,
)
from auto_research.intake import run_intake
from auto_research.models import InterestProfile, RegistryEntry
from auto_research.openai_client import OpenAIResponsesClient, SummaryArtifact
from auto_research.pdf import download_pdf
from auto_research.profile import load_interest_profile, validate_interest_profile_text
from auto_research.report import compose_report
from auto_research.ris import export_ris
from auto_research.selection import RankedCandidate, prefilter_candidates
from auto_research.summary import load_detailed_analysis_texts, write_daily_summary
from auto_research.state import PaperState, load_paper_state, update_paper_state, utc_now_iso
from auto_research.workspace import ensure_direction_workspace, ensure_workspace
from auto_research.longterm import update_longterm_summary


@dataclass(slots=True)
class PipelineConfig:
    workspace: Path
    direction: str | None = None
    profile_path: Path | None = None
    max_results: int = 20
    prefilter_limit: int = 15
    top_k: int = 10
    label: str | None = None
    model: str | None = None
    overwrite_summaries: bool = False
    push: bool = False


@dataclass(slots=True)
class PipelineResult:
    selected_entries: list[RegistryEntry]
    report_path: Path
    daily_summary_path: Path
    bundle_path: Path
    ris_path: Path
    longterm_summary_path: Path
    history_path: Path


def _default_label() -> str:
    return date.today().isoformat()


def _problem_solution_path(workspace: Path, entry: RegistryEntry) -> Path:
    return workspace / "papers" / entry.stable_id.replace("/", "_") / "problem-solution.md"


def _detailed_analysis_path(workspace: Path, entry: RegistryEntry) -> Path:
    return workspace / "papers" / entry.stable_id.replace("/", "_") / "detailed-analysis.md"


def _pdf_path(workspace: Path, entry: RegistryEntry) -> Path:
    return workspace / "papers" / entry.stable_id.replace("/", "_") / "source.pdf"


def _state_path(workspace: Path, entry: RegistryEntry) -> Path:
    return workspace / "papers" / entry.stable_id.replace("/", "_") / "state.json"


def _render_summary_markdown(summary: SummaryArtifact) -> str:
    lines = [
        "---",
        f'paper_id: "{summary.paper_id}"',
        f'title: "{summary.title}"',
        f'confidence: "{summary.confidence}"',
        f'relevance_band: "{summary.relevance_band}"',
        f'opportunity_label: "{summary.opportunity_label}"',
        "---",
        "",
        "# One-Sentence Summary",
        summary.one_sentence_summary,
        "",
        "# Problem",
        summary.problem,
        "",
        "# Proposed Solution",
        summary.proposed_solution,
        "",
        "# Claimed Contributions",
    ]
    lines.extend(f"- {item}" for item in summary.claimed_contributions)
    lines.extend(["", "# Evidence Basis"])
    lines.extend(f"- {item}" for item in summary.evidence_basis)
    lines.extend(["", "# Limitations"])
    lines.extend(f"- {item}" for item in summary.limitations)
    lines.extend(
        [
            "",
            "# Relevance to Profile",
            summary.relevance_to_profile,
            "",
            "# Analyst Notes",
            summary.analyst_notes,
            "",
        ]
    )
    return "\n".join(lines)


def _selected_entries_from_ranking(
    *,
    ranked: list[RankedCandidate],
    entries: list[RegistryEntry],
) -> list[RegistryEntry]:
    by_id = {entry.arxiv_id: entry for entry in entries}
    selected: list[RegistryEntry] = []
    for item in ranked:
        entry = by_id.get(item.paper_id)
        if entry is not None:
            selected.append(entry)
    return selected


def _write_summary_if_needed(
    *,
    workspace: Path,
    profile: InterestProfile,
    entry: RegistryEntry,
    client: OpenAIResponsesClient,
    overwrite: bool,
) -> Path:
    output_path = _problem_solution_path(workspace, entry)
    if output_path.exists() and not overwrite:
        return output_path

    summary = client.summarize_paper(profile=profile, entry=entry)
    markdown = _render_summary_markdown(summary)
    errors = validate_extraction_document(markdown)
    if errors:
        raise ValueError(f"Generated invalid problem-solution artifact: {'; '.join(errors)}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def _download_pdf_if_needed(*, workspace: Path, entry: RegistryEntry) -> Path | None:
    output_path = _pdf_path(workspace, entry)
    state_path = _state_path(workspace, entry)
    if output_path.exists():
        update_paper_state(
            state_path,
            status="pdf_downloaded",
            last_attempt_at=utc_now_iso(),
            last_error="",
            failure_kind="",
            source_updated_at=entry.updated_at,
        )
        return output_path

    try:
        with httpx.Client(timeout=60.0, follow_redirects=True, trust_env=False) as client:
            download_pdf(client=client, url=entry.pdf_url, destination=output_path)
    except Exception as exc:
        update_paper_state(
            state_path,
            status="pdf_failed",
            last_attempt_at=utc_now_iso(),
            last_error=str(exc),
            failure_kind=type(exc).__name__,
            source_updated_at=entry.updated_at,
        )
        return None

    update_paper_state(
        state_path,
        status="pdf_downloaded",
        last_attempt_at=utc_now_iso(),
        last_error="",
        failure_kind="",
        source_updated_at=entry.updated_at,
    )
    return output_path


def _write_detailed_analysis_if_needed(
    *,
    workspace: Path,
    profile: InterestProfile,
    entry: RegistryEntry,
    client: OpenAIResponsesClient,
    summary_path: Path,
) -> Path | None:
    output_path = _detailed_analysis_path(workspace, entry)
    state_path = _state_path(workspace, entry)
    pdf_path = _pdf_path(workspace, entry)

    if output_path.exists():
        update_paper_state(
            state_path,
            status="analysis_done",
            last_attempt_at=utc_now_iso(),
            last_error="",
            failure_kind="",
            source_updated_at=entry.updated_at,
        )
        return output_path

    if not pdf_path.exists():
        update_paper_state(
            state_path,
            status="needs_retry",
            last_attempt_at=utc_now_iso(),
            last_error="PDF missing",
            failure_kind="missing_pdf",
            source_updated_at=entry.updated_at,
        )
        return None

    try:
        _, sections = build_detailed_analysis(
            client=client,
            profile=profile,
            entry=entry,
            pdf_path=pdf_path,
        )
    except Exception as exc:
        update_paper_state(
            state_path,
            status="analysis_failed",
            last_attempt_at=utc_now_iso(),
            last_error=str(exc),
            failure_kind=type(exc).__name__,
            source_updated_at=entry.updated_at,
        )
        return None

    summary_markdown = summary_path.read_text(encoding="utf-8")
    markdown = render_detailed_analysis_markdown(
        entry=entry,
        summary_markdown=summary_markdown,
        detailed_sections=sections,
    )
    output_path.write_text(markdown, encoding="utf-8")
    update_paper_state(
        state_path,
        status="analysis_done",
        last_attempt_at=utc_now_iso(),
        last_error="",
        failure_kind="",
        source_updated_at=entry.updated_at,
    )
    return output_path


def _stage_commit_push(workspace: Path, label: str) -> None:
    repo_root: Path | None = None
    if workspace.name == "research-workspace":
        repo_root = workspace.parent
    else:
        # When staging a direction workspace (e.g. research-workspace/directions/<dir>),
        # keep using the repository root that contains the shared workspace.
        for parent in workspace.parents:
            if parent.name == "research-workspace":
                repo_root = parent.parent
                break
    if repo_root is None:
        repo_root = Path.cwd()
    subprocess.run(["git", "add", "-f", str(workspace)], cwd=repo_root, check=True)
    status = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=repo_root,
        check=False,
    )
    if status.returncode == 0:
        return
    subprocess.run(
        ["git", "commit", "-m", f"chore: update automation artifacts for {label}"],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(["git", "push"], cwd=repo_root, check=True)


def _failed_items(workspace: Path, selected_entries: list[RegistryEntry]) -> list[str]:
    failed: list[str] = []
    for entry in selected_entries:
        state_path = _state_path(workspace, entry)
        if not state_path.exists():
            continue
        state = load_paper_state(state_path)
        if state.status in {"pdf_failed", "analysis_failed", "needs_retry"}:
            failed.append(f"{entry.title}: {state.status} - {state.last_error}".strip())
    return failed


def _write_daily_bundle(
    *,
    workspace: Path,
    label: str,
    selected_entries: list[RegistryEntry],
    failed_items: list[str],
) -> Path:
    bundle_path = workspace / "reports" / "daily" / f"{label}-bundle.json"
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "label": label,
        "selected_papers": [
            {
                "paper_id": entry.arxiv_id,
                "title": entry.title,
                "paper_dir": str(workspace / "papers" / entry.stable_id.replace("/", "_")),
                "pdf_path": str(_pdf_path(workspace, entry)),
                "summary_path": str(_problem_solution_path(workspace, entry)),
                "analysis_path": str(_detailed_analysis_path(workspace, entry)),
                "state_path": str(_state_path(workspace, entry)),
            }
            for entry in selected_entries
        ],
        "failed_or_retry": failed_items,
    }
    bundle_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return bundle_path


def _append_run_history(
    *,
    workspace: Path,
    label: str,
    selected_entries: list[RegistryEntry],
    failed_items: list[str],
    report_path: Path,
    daily_summary_path: Path,
    bundle_path: Path,
    longterm_summary_path: Path,
    ris_path: Path,
) -> Path:
    history_path = workspace / "pipeline" / "run-history.jsonl"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "label": label,
        "created_at": utc_now_iso(),
        "selected_count": len(selected_entries),
        "failed_count": len(failed_items),
        "selected_ids": [entry.arxiv_id for entry in selected_entries],
        "failed_items": failed_items,
        "report_path": str(report_path),
        "daily_summary_path": str(daily_summary_path),
        "bundle_path": str(bundle_path),
        "longterm_summary_path": str(longterm_summary_path),
        "ris_path": str(ris_path),
    }
    existing = ""
    if history_path.exists():
        existing = history_path.read_text(encoding="utf-8")
    history_path.write_text(existing + json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
    return history_path


def _ensure_profile_exists(workspace: Path, direction: str, profile_path: Path) -> Path:
    if profile_path.exists():
        return profile_path

    if profile_path.is_symlink():
        raise OSError(f"Refusing to write symlinked profile file: {profile_path}")

    markdown = build_fallback_profile_from_issue_intake(workspace, direction).markdown
    errors = validate_interest_profile_text(markdown)
    if errors:
        raise ValueError(
            "Generated invalid fallback interest profile: " + "; ".join(errors)
        )
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(markdown, encoding="utf-8")
    return profile_path


def _ensure_profile_exists_with_metadata(
    workspace: Path,
    execution_workspace: Path,
    direction: str,
    profile_path: Path,
) -> tuple[Path, object | None]:
    if profile_path.exists():
        return profile_path, None

    if profile_path.is_symlink():
        raise OSError(f"Refusing to write symlinked profile file: {profile_path}")

    repo = discover_github_repo()
    fallback = build_fallback_profile_from_issue_intake(workspace, direction, repo=repo)
    errors = validate_interest_profile_text(fallback.markdown)
    if errors:
        raise ValueError(
            "Generated invalid fallback interest profile: " + "; ".join(errors)
        )
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(fallback.markdown, encoding="utf-8")
    return profile_path, fallback


def _infer_direction_from_profile_path(workspace: Path, profile_path: Path | None) -> str | None:
    if profile_path is None:
        return None
    candidate = profile_path
    if not candidate.is_absolute():
        # CLI users often pass paths like `research-workspace/directions/<dir>/profile/interest-profile.md`.
        # Treat that as workspace-relative rather than nesting another `research-workspace/` segment.
        parts = candidate.parts
        if len(parts) >= 1 and parts[0] == workspace.name:
            candidate = workspace.parent / candidate
        else:
            candidate = workspace / candidate
    try:
        relative = candidate.relative_to(workspace)
    except ValueError:
        return None
    parts = relative.parts
    if len(parts) == 4 and parts[0] == "directions" and parts[2] == "profile" and parts[3] == "interest-profile.md":
        return parts[1]
    return None


def _discover_direction_profiles(workspace: Path) -> list[str]:
    directions_root = workspace / "directions"
    if not directions_root.exists():
        return []
    directions: list[str] = []
    for direction_dir in sorted(path for path in directions_root.iterdir() if path.is_dir()):
        if (direction_dir / "profile" / "interest-profile.md").exists():
            directions.append(direction_dir.name)
    return directions


def _resolve_profile_path(
    shared_workspace: Path,
    execution_workspace: Path,
    requested_profile_path: Path | None,
) -> Path:
    if requested_profile_path is None:
        return execution_workspace / "profile" / "interest-profile.md"

    if requested_profile_path.is_absolute():
        return requested_profile_path

    # Support CLI-style values like `research-workspace/directions/<dir>/profile/interest-profile.md`.
    parts = requested_profile_path.parts
    if parts and parts[0] == shared_workspace.name:
        return shared_workspace.parent / requested_profile_path

    # Default to workspace-relative paths.
    return shared_workspace / requested_profile_path


def _resolve_run_direction(
    workspace: Path,
    requested_direction: str | None,
    profile_path: Path | None,
) -> str:
    if requested_direction:
        return requested_direction

    inferred = _infer_direction_from_profile_path(workspace, profile_path)
    if inferred:
        return inferred

    directions = discover_issue_directions(workspace)
    if len(directions) == 1:
        return directions[0]
    if len(directions) > 1:
        raise ValueError("Multiple issue directions found; pass --direction")

    profile_directions = _discover_direction_profiles(workspace)
    if len(profile_directions) == 1:
        return profile_directions[0]
    if len(profile_directions) > 1:
        raise ValueError("Multiple direction workspaces found; pass --direction")

    raise ValueError("No usable issue directions found; pass --direction")


def _validate_direction_segment(direction: str) -> None:
    if not direction:
        raise ValueError("Invalid direction: empty value")

    path = Path(direction)
    if path.is_absolute():
        raise ValueError("Invalid direction: absolute paths are not allowed")

    if len(path.parts) != 1 or path.parts[0] in {".", ".."}:
        raise ValueError("Invalid direction: must be a single segment")


def _github_finalize_state_path(execution_workspace: Path) -> Path:
    return execution_workspace / "pipeline" / "github-finalize.json"


def _write_github_finalize_state(
    *,
    execution_workspace: Path,
    fallback,
    label: str,
    report_path: Path,
    daily_summary_path: Path,
) -> Path | None:
    if fallback is None or not getattr(fallback, "issue_numbers", None) or not getattr(fallback, "repo", None):
        return None

    direction = getattr(fallback, "direction", "") or ""
    state_path = _github_finalize_state_path(execution_workspace)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "direction": direction,
                "label": label,
                "repo": fallback.repo,
                "report_path": str(report_path),
                "daily_summary_path": str(daily_summary_path),
                "used_fallback_profile": True,
                "consumed_issue_numbers": list(fallback.issue_numbers),
                "source_keys": list(fallback.source_keys),
                "status": "pending",
                "created_at": utc_now_iso(),
                "finalized_at": "",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return state_path


def finalize_github(workspace: Path, direction: str | None = None) -> dict[str, object]:
    shared_workspace = ensure_workspace(workspace)
    resolved_direction = _resolve_run_direction(shared_workspace, direction, None)
    _validate_direction_segment(resolved_direction)
    # Avoid creating a new direction workspace when the finalize state doesn't exist.
    execution_workspace = shared_workspace / "directions" / resolved_direction
    if execution_workspace.is_symlink():
        raise OSError(f"Refusing to use symlinked workspace directory: {execution_workspace}")
    pipeline_dir = execution_workspace / "pipeline"
    if pipeline_dir.is_symlink():
        raise OSError(f"Refusing to use symlinked workspace directory: {pipeline_dir}")
    state_path = _github_finalize_state_path(execution_workspace)
    if state_path.is_symlink():
        raise OSError(f"Refusing to read symlinked finalize state file: {state_path}")
    if not state_path.exists():
        raise ValueError("No pending GitHub finalize work found")

    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("status") == "completed":
        return state

    repo_root = shared_workspace.parent if shared_workspace.name == "research-workspace" else Path.cwd()
    subprocess.run(["git", "push"], cwd=repo_root, check=True)

    repo = str(state["repo"])
    label = str(state["label"])
    report_path = str(state["report_path"])
    daily_summary_path = str(state["daily_summary_path"])
    for issue_number in state.get("consumed_issue_numbers", []):
        body = (
            f"This request was incorporated into the completed daily paper summary workflow for `{label}`.\n\n"
            f"- Report: `{report_path}`\n"
            f"- Daily Summary: `{daily_summary_path}`"
        )
        try:
            comment_on_issue(repo=repo, issue_number=int(issue_number), body=body)
        except Exception as exc:
            print(
                f"Warning: unable to comment on finalize issue #{issue_number}: {exc}",
                file=sys.stderr,
            )
            continue
        try:
            close_issue(repo=repo, issue_number=int(issue_number))
        except Exception as exc:
            print(
                f"Warning: unable to close finalize issue #{issue_number}: {exc}",
                file=sys.stderr,
            )

    state["status"] = "completed"
    state["finalized_at"] = utc_now_iso()
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return state


def run_daily_pipeline(
    config: PipelineConfig,
    *,
    llm_client: OpenAIResponsesClient | None = None,
) -> PipelineResult:
    shared_workspace = ensure_workspace(config.workspace)
    direction = _resolve_run_direction(shared_workspace, config.direction, config.profile_path)
    execution_workspace = ensure_direction_workspace(shared_workspace, direction)
    label = config.label or _default_label()
    profile_path = _resolve_profile_path(shared_workspace, execution_workspace, config.profile_path)
    profile_path, fallback = _ensure_profile_exists_with_metadata(
        shared_workspace,
        execution_workspace,
        direction,
        profile_path,
    )
    profile = load_interest_profile(profile_path)

    intake_entries = run_intake(
        workspace=execution_workspace, profile_path=profile_path, max_results=config.max_results
    )
    candidates = prefilter_candidates(profile, intake_entries, config.prefilter_limit)

    selected_entries: list[RegistryEntry]
    if not candidates:
        selected_entries = []
    else:
        client = llm_client or OpenAIResponsesClient(model=config.model)
        ranked = client.rank_candidates(profile=profile, candidates=candidates, top_k=config.top_k)
        selected_entries = _selected_entries_from_ranking(ranked=ranked, entries=candidates)

        for entry in selected_entries:
            summary_path = _write_summary_if_needed(
                workspace=execution_workspace,
                profile=profile,
                entry=entry,
                client=client,
                overwrite=config.overwrite_summaries,
            )
            pdf_path = _download_pdf_if_needed(workspace=execution_workspace, entry=entry)
            if pdf_path is not None:
                _write_detailed_analysis_if_needed(
                    workspace=execution_workspace,
                    profile=profile,
                    entry=entry,
                    client=client,
                    summary_path=summary_path,
                )

    report_path = compose_report(workspace=execution_workspace, mode="daily", label=label)
    analyses = load_detailed_analysis_texts(execution_workspace, selected_entries)
    failed_items = _failed_items(execution_workspace, selected_entries)
    client_for_summary = llm_client or OpenAIResponsesClient(model=config.model)
    daily_summary_payload = client_for_summary.summarize_daily_findings(
        profile=profile,
        analyses=analyses,
        failed_items=failed_items,
    )
    daily_summary_path = write_daily_summary(
        path=execution_workspace / "reports" / "daily" / f"{label}-summary.md",
        label=label,
        payload=daily_summary_payload,
    )
    previous_longterm = ""
    longterm_path = execution_workspace / "reports" / "longterm" / "longterm-summary.md"
    if longterm_path.exists():
        previous_longterm = longterm_path.read_text(encoding="utf-8")
    generated_longterm = client_for_summary.update_longterm_findings(
        profile=profile,
        previous_summary=previous_longterm,
        analyses=analyses,
        daily_summary=daily_summary_payload,
    )
    longterm_summary_path = update_longterm_summary(
        path=longterm_path,
        daily_report_path=report_path,
        selected_titles=[entry.title for entry in selected_entries],
        selected_summaries=[entry.summary for entry in selected_entries],
        generated_summary=generated_longterm,
    )
    bundle_path = _write_daily_bundle(
        workspace=execution_workspace,
        label=label,
        selected_entries=selected_entries,
        failed_items=failed_items,
    )
    ris_path = export_ris(
        selected_entries, execution_workspace / "exports" / "zotero" / f"{label}.ris"
    )
    history_path = _append_run_history(
        workspace=execution_workspace,
        label=label,
        selected_entries=selected_entries,
        failed_items=failed_items,
        report_path=report_path,
        daily_summary_path=daily_summary_path,
        bundle_path=bundle_path,
        longterm_summary_path=longterm_summary_path,
        ris_path=ris_path,
    )

    _write_github_finalize_state(
        execution_workspace=execution_workspace,
        fallback=fallback,
        label=label,
        report_path=report_path,
        daily_summary_path=daily_summary_path,
    )

    if config.push:
        _stage_commit_push(execution_workspace, label)

    return PipelineResult(
        selected_entries=selected_entries,
        report_path=report_path,
        daily_summary_path=daily_summary_path,
        bundle_path=bundle_path,
        ris_path=ris_path,
        longterm_summary_path=longterm_summary_path,
        history_path=history_path,
    )
