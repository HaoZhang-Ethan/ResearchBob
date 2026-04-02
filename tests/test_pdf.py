from __future__ import annotations

import httpx
import pytest

from auto_research.pdf import download_pdf, extract_text_from_pdf


def test_download_pdf_writes_response_content(tmp_path) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "application/pdf"},
            content=b"%PDF-1.4 fake-pdf",
        )
    )
    client = httpx.Client(transport=transport)

    output = download_pdf(
        client=client,
        url="https://example.test/paper.pdf",
        destination=tmp_path / "paper.pdf",
    )

    assert output.read_bytes() == b"%PDF-1.4 fake-pdf"


def test_download_pdf_rejects_non_pdf_response(tmp_path) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"<html></html>",
        )
    )
    client = httpx.Client(transport=transport)

    with pytest.raises(ValueError, match="PDF-like"):
        download_pdf(
            client=client,
            url="https://example.test/page",
            destination=tmp_path / "paper.pdf",
        )


def test_download_pdf_retries_on_transient_timeout(tmp_path) -> None:
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise httpx.ReadTimeout("slow")
        return httpx.Response(
            200,
            headers={"content-type": "application/pdf"},
            content=b"%PDF-1.4 retry-success",
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    output = download_pdf(
        client=client,
        url="https://example.test/retry.pdf",
        destination=tmp_path / "retry.pdf",
    )
    assert attempts["count"] == 3
    assert output.read_bytes() == b"%PDF-1.4 retry-success"


def test_extract_text_from_pdf_best_effort(tmp_path) -> None:
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nExample PDF text stream\nBT /F1 12 Tf (Hello World) Tj ET\n")

    text = extract_text_from_pdf(pdf_path)

    assert "Hello World" in text or "Example PDF text stream" in text
