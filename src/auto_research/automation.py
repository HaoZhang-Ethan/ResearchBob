from __future__ import annotations
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import httpx

from auto_research.analysis import build_detailed_analysis, render_detailed_analysis_markdown
from auto_research.extraction import validate_extraction_document
from auto_research.intake import run_intake
from auto_research.models import InterestProfile, RegistryEntry
from auto_research.openai_client import OpenAIResponsesClient, SummaryArtifact
from auto_research.pdf import download_pdf
from auto_research.profile import load_interest_profile
from auto_research.report import compose_report
from auto_research.ris import export_ris
from auto_research.selection import RankedCandidate, prefilter_candidates
from auto_research.state import PaperState, update_paper_state
from auto_research.workspace import ensure_workspace
from auto_research.longterm import update_longterm_summary


@dataclass(slots=True)
class PipelineConfig:
    workspace: Path
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
    ris_path: Path
    longterm_summary_path: Path


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
        update_paper_state(state_path, status="pdf_downloaded", last_error="")
        return output_path

    try:
        with httpx.Client(timeout=60.0, follow_redirects=True, trust_env=False) as client:
            download_pdf(client=client, url=entry.pdf_url, destination=output_path)
    except Exception as exc:
        update_paper_state(
            state_path,
            status="pdf_failed",
            last_error=str(exc),
        )
        return None

    update_paper_state(state_path, status="pdf_downloaded", last_error="")
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
        update_paper_state(state_path, status="analysis_done", last_error="")
        return output_path

    if not pdf_path.exists():
        update_paper_state(state_path, status="needs_retry", last_error="PDF missing")
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
            last_error=str(exc),
        )
        return None

    summary_markdown = summary_path.read_text(encoding="utf-8")
    markdown = render_detailed_analysis_markdown(
        entry=entry,
        summary_markdown=summary_markdown,
        detailed_sections=sections,
    )
    output_path.write_text(markdown, encoding="utf-8")
    update_paper_state(state_path, status="analysis_done", last_error="")
    return output_path


def _stage_commit_push(workspace: Path, label: str) -> None:
    repo_root = workspace.parent if workspace.name == "research-workspace" else Path.cwd()
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


def run_daily_pipeline(
    config: PipelineConfig,
    *,
    llm_client: OpenAIResponsesClient | None = None,
) -> PipelineResult:
    workspace = ensure_workspace(config.workspace)
    label = config.label or _default_label()
    profile_path = config.profile_path or workspace / "profile" / "interest-profile.md"
    profile = load_interest_profile(profile_path)

    intake_entries = run_intake(workspace=workspace, profile_path=profile_path, max_results=config.max_results)
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
                workspace=workspace,
                profile=profile,
                entry=entry,
                client=client,
                overwrite=config.overwrite_summaries,
            )
            pdf_path = _download_pdf_if_needed(workspace=workspace, entry=entry)
            if pdf_path is not None:
                _write_detailed_analysis_if_needed(
                    workspace=workspace,
                    profile=profile,
                    entry=entry,
                    client=client,
                    summary_path=summary_path,
                )

    report_path = compose_report(workspace=workspace, mode="daily", label=label)
    longterm_summary_path = update_longterm_summary(
        path=workspace / "reports" / "longterm" / "longterm-summary.md",
        daily_report_path=report_path,
        selected_titles=[entry.title for entry in selected_entries],
        selected_summaries=[entry.summary for entry in selected_entries],
    )
    ris_path = export_ris(selected_entries, workspace / "exports" / "zotero" / f"{label}.ris")

    if config.push:
        _stage_commit_push(workspace, label)

    return PipelineResult(
        selected_entries=selected_entries,
        report_path=report_path,
        ris_path=ris_path,
        longterm_summary_path=longterm_summary_path,
    )
