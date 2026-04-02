from __future__ import annotations

import xml.etree.ElementTree as ET

import httpx

from auto_research.models import RegistryEntry, validate_arxiv_id

ATOM_NAMESPACE = {"atom": "http://www.w3.org/2005/Atom"}


def _extract_arxiv_id(raw_id_url: str) -> str:
    if "/abs/" in raw_id_url:
        return raw_id_url.split("/abs/", 1)[1]
    return raw_id_url.rsplit("/", 1)[-1]


class ArxivClient:
    def __init__(self, client: httpx.Client | None = None, endpoint: str | None = None) -> None:
        if client is None:
            try:
                self._client = httpx.Client(timeout=30.0)
            except (ImportError, ModuleNotFoundError) as exc:
                # httpx can raise import-style errors at client initialization time when proxy
                # configuration implies optional dependencies (e.g. SOCKS support).
                raise OSError(
                    f"Unable to initialize httpx client (check proxy settings / optional dependencies): {exc}"
                ) from None
        else:
            self._client = client
        self._endpoint = endpoint or "https://export.arxiv.org/api/query"
        self._max_retries = 3

    def fetch_recent(self, query: str, max_results: int = 25) -> list[RegistryEntry]:
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        last_error: Exception | None = None
        for _ in range(self._max_retries):
            try:
                response = self._client.get(self._endpoint, params=params)
                response.raise_for_status()
                break
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError, httpx.RemoteProtocolError) as exc:
                last_error = exc
                continue
        else:
            assert last_error is not None
            raise last_error
        return self._parse_feed(response.text)

    def _parse_feed(self, xml_text: str) -> list[RegistryEntry]:
        root = ET.fromstring(xml_text)
        entries: list[RegistryEntry] = []

        for entry in root.findall("atom:entry", ATOM_NAMESPACE):
            raw_id = _extract_arxiv_id(
                entry.findtext("atom:id", default="", namespaces=ATOM_NAMESPACE)
            )
            raw_id = validate_arxiv_id(raw_id)
            title = " ".join(entry.findtext("atom:title", default="", namespaces=ATOM_NAMESPACE).split())
            summary = " ".join(entry.findtext("atom:summary", default="", namespaces=ATOM_NAMESPACE).split())
            published_at = entry.findtext("atom:published", default="", namespaces=ATOM_NAMESPACE)
            updated_at = entry.findtext("atom:updated", default="", namespaces=ATOM_NAMESPACE)
            pdf_url = ""

            for link in entry.findall("atom:link", ATOM_NAMESPACE):
                if link.attrib.get("title") == "pdf":
                    pdf_url = link.attrib.get("href", "")
                    break

            entries.append(
                RegistryEntry(
                    arxiv_id=raw_id,
                    title=title,
                    summary=summary,
                    pdf_url=pdf_url,
                    published_at=published_at,
                    updated_at=updated_at,
                    relevance_band="adjacent",
                    source="arxiv",
                )
            )

        return entries
