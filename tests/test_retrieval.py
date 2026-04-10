from auto_research.retrieval import RetrievedCandidate, merge_retrieved_candidates


def test_merge_retrieved_candidates_dedupes_by_arxiv_id_and_preserves_sources() -> None:
    arxiv_candidates = [
        RetrievedCandidate(
            paper_id="2501.00001v1",
            title="Federated Learning Systems at Scale",
            summary="Systems paper.",
            pdf_url="https://arxiv.org/pdf/2501.00001v1",
            landing_page_url="https://arxiv.org/abs/2501.00001v1",
            source_family="arxiv",
            discovery_sources=["arxiv_api"],
        )
    ]
    web_candidates = [
        RetrievedCandidate(
            paper_id="2501.00001v1",
            title="Federated Learning Systems at Scale",
            summary="Systems paper from the web.",
            pdf_url="",
            landing_page_url="https://example.test/paper",
            source_family="semantic_scholar",
            discovery_sources=["agent_web"],
        )
    ]

    merged = merge_retrieved_candidates(
        arxiv_candidates=arxiv_candidates, web_candidates=web_candidates
    )

    assert len(merged) == 1
    assert sorted(merged[0].discovery_sources) == ["agent_web", "arxiv_api"]
    assert merged[0].landing_page_url == "https://arxiv.org/abs/2501.00001v1"


def test_merge_retrieved_candidates_dedupes_by_normalized_title_when_arxiv_missing() -> None:
    arxiv_candidates = []
    web_candidates = [
        RetrievedCandidate(
            paper_id="",
            title="Client Orchestration in Federated Learning",
            summary="First copy.",
            pdf_url="",
            landing_page_url="https://example.test/a",
            source_family="semantic_scholar",
            discovery_sources=["semantic_scholar"],
        ),
        RetrievedCandidate(
            paper_id="",
            title="Client   Orchestration in Federated Learning",
            summary="Second copy.",
            pdf_url="",
            landing_page_url="https://example.test/b",
            source_family="openalex",
            discovery_sources=["openalex"],
        ),
    ]

    merged = merge_retrieved_candidates(
        arxiv_candidates=arxiv_candidates, web_candidates=web_candidates
    )

    assert len(merged) == 1
    assert sorted(merged[0].discovery_sources) == ["openalex", "semantic_scholar"]


def test_merge_retrieved_candidates_merges_later_identified_paper_into_title_only_candidate() -> None:
    arxiv_candidates: list[RetrievedCandidate] = []
    web_candidates = [
        RetrievedCandidate(
            paper_id="",
            title="Federated Learning Systems at Scale",
            summary="Discovered without an ID.",
            pdf_url="",
            landing_page_url="https://example.test/a",
            source_family="openalex",
            discovery_sources=["openalex"],
        ),
        RetrievedCandidate(
            paper_id="2501.00001v1",
            title="Federated Learning Systems at Scale",
            summary="Same paper, later discovered with an ID.",
            pdf_url="https://arxiv.org/pdf/2501.00001v1",
            landing_page_url="https://arxiv.org/abs/2501.00001v1",
            source_family="semantic_scholar",
            discovery_sources=["semantic_scholar"],
        ),
    ]

    merged = merge_retrieved_candidates(
        arxiv_candidates=arxiv_candidates, web_candidates=web_candidates
    )

    assert len(merged) == 1
    assert sorted(merged[0].discovery_sources) == ["openalex", "semantic_scholar"]


def test_merge_retrieved_candidates_dedupes_across_arxiv_versions() -> None:
    arxiv_candidates = [
        RetrievedCandidate(
            paper_id="2501.00001v1",
            title="Federated Learning Systems at Scale",
            summary="First version.",
            pdf_url="https://arxiv.org/pdf/2501.00001v1",
            landing_page_url="https://arxiv.org/abs/2501.00001v1",
            source_family="arxiv",
            discovery_sources=["arxiv_api"],
        )
    ]
    web_candidates = [
        RetrievedCandidate(
            paper_id="2501.00001v2",
            title="Federated Learning Systems at Scale",
            summary="Second version.",
            pdf_url="https://arxiv.org/pdf/2501.00001v2",
            landing_page_url="https://arxiv.org/abs/2501.00001v2",
            source_family="semantic_scholar",
            discovery_sources=["semantic_scholar"],
        )
    ]

    merged = merge_retrieved_candidates(
        arxiv_candidates=arxiv_candidates, web_candidates=web_candidates
    )

    assert len(merged) == 1
    assert sorted(merged[0].discovery_sources) == ["arxiv_api", "semantic_scholar"]
