from __future__ import annotations

from pathlib import Path

import httpx


def download_pdf(*, client: httpx.Client, url: str, destination: Path) -> Path:
    response = client.get(url)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "pdf" not in content_type and not url.lower().endswith(".pdf"):
        raise ValueError(f"URL did not return a PDF-like response: {url}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response.content)
    return destination


def extract_text_from_pdf(path: Path) -> str:
    data = path.read_bytes()
    if not data.startswith(b"%PDF"):
        raise ValueError(f"Not a PDF file: {path}")

    # Conservative, dependency-free first pass:
    # extract printable strings from stream-like text and join them.
    parts: list[str] = []
    current = bytearray()

    def flush() -> None:
        if len(current) >= 4:
            try:
                text = current.decode("latin-1")
            except UnicodeDecodeError:
                text = ""
            text = " ".join(text.split())
            if text:
                parts.append(text)
        current.clear()

    for byte in data:
        if 32 <= byte <= 126 or byte in (9, 10, 13):
            current.append(byte)
        else:
            flush()
    flush()

    text = "\n".join(parts).strip()
    if not text:
        raise ValueError(f"Unable to extract text from PDF: {path}")
    return text
