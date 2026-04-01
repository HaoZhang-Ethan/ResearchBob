import os
import json

from pathlib import Path

import pytest

from auto_research.cli import main
from auto_research.models import RegistryEntry
from auto_research.registry import write_registry
from auto_research.report import compose_report
from auto_research.workspace import ensure_workspace


def _valid_artifact_text(
    *,
    paper_id: str,
    title: str,
    confidence: str = "high",
    relevance_band: str = "high-match",
    opportunity_label: str = "follow-up",
) -> str:
    return (
        "---\n"
        f'paper_id: "{paper_id}"\n'
        f'title: "{title}"\n'
        f'confidence: "{confidence}"\n'
        f'relevance_band: "{relevance_band}"\n'
        f'opportunity_label: "{opportunity_label}"\n'
        "---\n\n"
        "# One-Sentence Summary\nA serving scheduler for tail latency.\n\n"
        "# Problem\nTail latency instability.\n\n"
        "# Proposed Solution\nQueue-aware scheduling.\n\n"
        "# Claimed Contributions\n- New scheduler\n\n"
        "# Evidence Basis\n- Abstract\n\n"
        "# Limitations\n- Narrow evaluation\n\n"
        "# Relevance to Profile\nDirectly relevant.\n\n"
        "# Analyst Notes\nPromising problem, incomplete validation.\n"
    )


def test_compose_daily_report_groups_entries_by_opportunity(tmp_path) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")
    registry_path = workspace / "papers" / "registry.jsonl"
    write_registry(
        registry_path,
        [
            RegistryEntry(
                arxiv_id="2501.00001v1",
                title="Efficient Tail Latency Control for Serving Clusters",
                summary="Tail latency scheduler.",
                pdf_url="https://arxiv.org/pdf/2501.00001v1",
                published_at="2026-01-01T00:00:00Z",
                updated_at="2026-01-03T00:00:00Z",
                relevance_band="high-match",
                source="arxiv",
            )
        ],
    )

    paper_dir = workspace / "papers" / "2501.00001v1"
    paper_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "problem-solution.md").write_text(
        _valid_artifact_text(
            paper_id="2501.00001v1",
            title="Efficient Tail Latency Control for Serving Clusters",
            opportunity_label="follow-up",
        ),
        encoding="utf-8",
    )

    report_path = compose_report(workspace, mode="daily", label="2026-03-31")
    report_text = report_path.read_text(encoding="utf-8")

    assert report_path == workspace / "reports" / "daily" / "2026-03-31.md"
    assert "Top Papers to Read Now" in report_text
    assert "Promising Problems, Weak Solutions" in report_text
    assert "Efficient Tail Latency Control for Serving Clusters" in report_text


def test_compose_daily_report_keeps_versioned_directories_out_of_manual_review(
    tmp_path,
) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")

    paper_dir = workspace / "papers" / "2501.00001v1"
    paper_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "problem-solution.md").write_text(
        _valid_artifact_text(
            paper_id="2501.00001v1",
            title="Efficient Tail Latency Control for Serving Clusters",
            opportunity_label="follow-up",
        ),
        encoding="utf-8",
    )

    report_text = compose_report(workspace, mode="daily", label="2026-03-31").read_text(
        encoding="utf-8"
    )

    follow_up_section = report_text.split("## Promising Problems, Weak Solutions", 1)[1].split(
        "## Papers Likely Safe to Skip", 1
    )[0]
    manual_review_section = report_text.split("## Papers Requiring Manual Verification", 1)[1]

    assert "Efficient Tail Latency Control for Serving Clusters" in follow_up_section
    assert "Efficient Tail Latency Control for Serving Clusters" not in manual_review_section


def test_compose_daily_report_routes_invalid_artifacts_to_manual_review(
    tmp_path,
) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")

    valid_dir = workspace / "papers" / "2501.00001v1"
    valid_dir.mkdir(parents=True, exist_ok=True)
    (valid_dir / "problem-solution.md").write_text(
        _valid_artifact_text(
            paper_id="2501.00001v1",
            title="Efficient Tail Latency Control for Serving Clusters",
            opportunity_label="read-now",
        ),
        encoding="utf-8",
    )

    invalid_dir = workspace / "papers" / "2501.00002v1"
    invalid_dir.mkdir(parents=True, exist_ok=True)
    (invalid_dir / "problem-solution.md").write_text(
        "---\n"
        'paper_id: "2501.00002v1"\n'
        'title: "Do Not Trust This Title"\n'
        'confidence: "high"\n'
        'relevance_band: "high-match"\n'
        'opportunity_label: "read-now"\n'
        "---\n\n"
        "# One-Sentence Summary\nBroken artifact.\n",
        encoding="utf-8",
    )

    malformed_dir = workspace / "papers" / "2501.00003v1"
    malformed_dir.mkdir(parents=True, exist_ok=True)
    (malformed_dir / "problem-solution.md").write_text(
        "# Not a valid extraction artifact\n",
        encoding="utf-8",
    )

    report_text = compose_report(
        workspace,
        mode="daily",
        label="2026-03-31",
    ).read_text(encoding="utf-8")

    assert "Efficient Tail Latency Control for Serving Clusters" in report_text
    assert "Papers Requiring Manual Verification" in report_text
    assert "2501.00002v1" in report_text
    assert "2501.00003v1" in report_text
    assert "Do Not Trust This Title" not in report_text
    assert "Missing heading: Problem" in report_text
    assert "Missing YAML frontmatter" in report_text


def test_compose_report_ignores_symlinked_paper_directories(tmp_path) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")

    outside_dir = tmp_path / "outside-paper"
    outside_dir.mkdir(parents=True, exist_ok=True)
    (outside_dir / "problem-solution.md").write_text(
        _valid_artifact_text(
            paper_id="2501.99999v1",
            title="Outside Workspace Paper",
            opportunity_label="read-now",
        ),
        encoding="utf-8",
    )

    symlink_dir = workspace / "papers" / "2501.99999v1"
    os.symlink(outside_dir, symlink_dir)

    report_text = compose_report(workspace, mode="daily", label="2026-03-31").read_text(
        encoding="utf-8"
    )

    assert "Outside Workspace Paper" not in report_text


def test_compose_daily_report_surfaces_migrated_conflict_artifacts(tmp_path) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")

    stable_dir = workspace / "papers" / "2501.00001"
    stable_dir.mkdir(parents=True, exist_ok=True)
    (stable_dir / "problem-solution.md").write_text(
        _valid_artifact_text(
            paper_id="2501.00001v2",
            title="Efficient Tail Latency Control for Serving Clusters",
            opportunity_label="read-now",
        ),
        encoding="utf-8",
    )
    (stable_dir / "problem-solution.migrated-from-2501.00001v1.md").write_text(
        "legacy artifact",
        encoding="utf-8",
    )

    report_text = compose_report(
        workspace,
        mode="daily",
        label="2026-03-31",
    ).read_text(encoding="utf-8")

    assert "Top Papers to Read Now" in report_text
    assert "Efficient Tail Latency Control for Serving Clusters" in report_text
    assert "Papers Requiring Manual Verification" in report_text
    assert "problem-solution.migrated-from-2501.00001v1.md" in report_text
    assert "Missing YAML frontmatter" in report_text


def test_compose_daily_report_routes_low_priority_artifacts_to_manual_review(
    tmp_path,
) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")
    paper_dir = workspace / "papers" / "2501.00001"
    paper_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "problem-solution.md").write_text(
        _valid_artifact_text(
            paper_id="2501.00001v2",
            title="Peripheral Benchmark Sweep",
            relevance_band="low-priority",
            opportunity_label="read-now",
        ),
        encoding="utf-8",
    )

    report_text = compose_report(
        workspace,
        mode="daily",
        label="2026-03-31",
    ).read_text(encoding="utf-8")

    assert "## Top Papers to Read Now\n- None" in report_text
    assert "Papers Requiring Manual Verification" in report_text
    assert "Peripheral Benchmark Sweep" in report_text
    assert "low-priority relevance" in report_text


def test_compose_daily_report_routes_low_confidence_artifacts_to_manual_review(
    tmp_path,
) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")
    paper_dir = workspace / "papers" / "2501.00001v1"
    paper_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "problem-solution.md").write_text(
        _valid_artifact_text(
            paper_id="2501.00001v1",
            title="Low Confidence Artifact",
            confidence="low",
            relevance_band="high-match",
            opportunity_label="read-now",
        ),
        encoding="utf-8",
    )

    report_text = compose_report(
        workspace,
        mode="daily",
        label="2026-03-31",
    ).read_text(encoding="utf-8")

    assert "## Top Papers to Read Now\n- None" in report_text
    manual_review_section = report_text.split("## Papers Requiring Manual Verification", 1)[1]
    assert "Low Confidence Artifact" in manual_review_section
    assert "low confidence" in manual_review_section.lower()


def test_compose_report_routes_symlinked_primary_artifact_to_manual_review(tmp_path) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")

    paper_dir = workspace / "papers" / "2501.00001v1"
    paper_dir.mkdir(parents=True, exist_ok=True)

    missing_target = tmp_path / "missing-artifact.md"
    os.symlink(missing_target, paper_dir / "problem-solution.md")

    report_text = compose_report(workspace, mode="daily", label="2026-03-31").read_text(
        encoding="utf-8"
    )

    manual_review_section = report_text.split("## Papers Requiring Manual Verification", 1)[1]

    assert "2501.00001v1" in manual_review_section
    assert "symlink" in manual_review_section.lower()


def test_compose_report_routes_symlinked_metadata_to_manual_review(tmp_path) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")

    paper_dir = workspace / "papers" / "2501.00001v1"
    paper_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "problem-solution.md").write_text(
        _valid_artifact_text(
            paper_id="2501.00001v1",
            title="Symlinked Metadata Paper",
            opportunity_label="follow-up",
        ),
        encoding="utf-8",
    )

    missing_target = tmp_path / "missing-metadata.json"
    os.symlink(missing_target, paper_dir / "metadata.json")

    report_text = compose_report(workspace, mode="daily", label="2026-03-31").read_text(
        encoding="utf-8"
    )

    follow_up_section = report_text.split("## Promising Problems, Weak Solutions", 1)[1].split(
        "## Papers Likely Safe to Skip", 1
    )[0]
    manual_review_section = report_text.split("## Papers Requiring Manual Verification", 1)[1]

    assert "Symlinked Metadata Paper" not in follow_up_section
    assert "Symlinked Metadata Paper" in manual_review_section
    assert "symlink" in manual_review_section.lower()


def test_compose_report_rejects_symlinked_report_path(tmp_path) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")

    outside_target = tmp_path / "outside-report.md"
    outside_target.write_text("do not touch\n", encoding="utf-8")

    report_path = workspace / "reports" / "daily" / "2026-03-31.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(outside_target, report_path)

    with pytest.raises(OSError, match="symlink"):
        compose_report(workspace, mode="daily", label="2026-03-31")

    assert outside_target.read_text(encoding="utf-8") == "do not touch\n"


def test_compose_daily_report_routes_identity_mismatches_to_manual_review(
    tmp_path,
) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")
    paper_dir = workspace / "papers" / "2501.00001"
    paper_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "problem-solution.md").write_text(
        _valid_artifact_text(
            paper_id="2501.99999v1",
            title="Mismatched Identity Artifact",
            opportunity_label="read-now",
        ),
        encoding="utf-8",
    )
    (paper_dir / "metadata.json").write_text(
        json.dumps(
            {
                "arxiv_id": "2501.00001v2",
                "title": "Canonical Metadata Title",
                "summary": "summary",
                "pdf_url": "https://arxiv.org/pdf/2501.00001v2",
                "published_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-03T00:00:00Z",
                "relevance_band": "high-match",
                "source": "arxiv",
            }
        ),
        encoding="utf-8",
    )

    report_text = compose_report(
        workspace,
        mode="daily",
        label="2026-03-31",
    ).read_text(encoding="utf-8")

    assert "## Top Papers to Read Now\n- None" in report_text
    assert "Papers Requiring Manual Verification" in report_text
    assert "Mismatched Identity Artifact" in report_text
    assert "does not match containing directory" in report_text
    assert "does not match metadata arxiv_id" in report_text


def test_compose_manual_report_writes_to_manual_directory(tmp_path) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")
    report_path = compose_report(workspace, mode="manual", label="ml-serving-scan")
    assert report_path == workspace / "reports" / "manual" / "ml-serving-scan.md"


def test_compose_report_rejects_labels_that_escape_workspace(tmp_path) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")

    with pytest.raises(ValueError, match="Invalid report label"):
        compose_report(workspace, mode="daily", label="../outside")


def test_compose_report_cli_writes_report_and_prints_path(tmp_path, capsys) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")
    paper_dir = workspace / "papers" / "2501.00001v1"
    paper_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "problem-solution.md").write_text(
        _valid_artifact_text(
            paper_id="2501.00001v1",
            title="Efficient Tail Latency Control for Serving Clusters",
            opportunity_label="follow-up",
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "compose-report",
            "--workspace",
            str(workspace),
            "--mode",
            "daily",
            "--label",
            "2026-03-31",
        ]
    )

    assert result == 0
    captured = capsys.readouterr()
    assert str(workspace / "reports" / "daily" / "2026-03-31.md") in captured.out


def test_compose_report_cli_rejects_invalid_label(tmp_path, capsys) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")

    result = main(
        [
            "compose-report",
            "--workspace",
            str(workspace),
            "--mode",
            "daily",
            "--label",
            "../outside",
        ]
    )

    assert result == 1
    captured = capsys.readouterr()
    assert "Invalid report label" in captured.err
    assert not (workspace.parent / "outside.md").exists()


def test_intake_cli_accepts_profile_equals_override(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "research-workspace"
    profile_path = tmp_path / "interest-profile.md"
    profile_path.write_text(
        Path("tests/fixtures/interest_profile.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    calls: list[dict[str, object]] = []

    def fake_run_intake(
        workspace: Path,
        profile_path: Path,
        max_results: int,
    ) -> list[RegistryEntry]:
        calls.append(
            {
                "workspace": workspace,
                "profile_path": profile_path,
                "max_results": max_results,
            }
        )
        return []

    monkeypatch.setattr("auto_research.cli.run_intake", fake_run_intake)

    result = main(
        [
            "intake",
            "--workspace",
            str(workspace),
            f"--profile={profile_path}",
            "--max-results",
            "3",
        ]
    )

    assert result == 0
    assert calls == [
        {
            "workspace": workspace,
            "profile_path": profile_path,
            "max_results": 3,
        }
    ]
