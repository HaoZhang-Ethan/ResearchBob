from auto_research.models import RegistryEntry
from auto_research.registry import write_registry
from auto_research.report import compose_report
from auto_research.workspace import ensure_workspace


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
        "---\n"
        'paper_id: "2501.00001v1"\n'
        'title: "Efficient Tail Latency Control for Serving Clusters"\n'
        'confidence: "high"\n'
        'relevance_band: "high-match"\n'
        'opportunity_label: "follow-up"\n'
        "---\n\n"
        "# One-Sentence Summary\nA serving scheduler for tail latency.\n\n"
        "# Problem\nTail latency instability.\n\n"
        "# Proposed Solution\nQueue-aware scheduling.\n\n"
        "# Claimed Contributions\n- New scheduler\n\n"
        "# Evidence Basis\n- Abstract\n\n"
        "# Limitations\n- Narrow evaluation\n\n"
        "# Relevance to Profile\nDirectly relevant.\n\n"
        "# Analyst Notes\nPromising problem, incomplete validation.\n",
        encoding="utf-8",
    )

    report_path = compose_report(workspace, mode="daily", label="2026-03-31")
    report_text = report_path.read_text(encoding="utf-8")

    assert report_path == workspace / "reports" / "daily" / "2026-03-31.md"
    assert "Top Papers to Read Now" in report_text
    assert "Promising Problems, Weak Solutions" in report_text
    assert "Efficient Tail Latency Control for Serving Clusters" in report_text


def test_compose_manual_report_writes_to_manual_directory(tmp_path) -> None:
    workspace = ensure_workspace(tmp_path / "research-workspace")
    report_path = compose_report(workspace, mode="manual", label="ml-serving-scan")
    assert report_path == workspace / "reports" / "manual" / "ml-serving-scan.md"
