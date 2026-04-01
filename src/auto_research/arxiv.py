from __future__ import annotations

import xml.etree.ElementTree as ET

import httpx

from auto_research.models import RegistryEntry

ATOM_NAMESPACE = {"atom": "http://www.w3.org/2005/Atom"}


class ArxivClient:
    def __init__(self, client: httpx.Client | None = None, endpoint: str | None = None) -> None:
        self._client = client or httpx.Client(timeout=30.0)
        self._endpoint = endpoint or "http://export.arxiv.org/api/query"

    def fetch_recent(self, query: str, max_results: int = 25) -> list[RegistryEntry]:
        response = self._client.get(
            self._endpoint,
            params={"search_query": query, "start": 0, "max_results": max_results},
        )
        response.raise_for_status()
        return self._parse_feed(response.text)

    def _parse_feed(self, xml_text: str) -> list[RegistryEntry]:
        root = ET.fromstring(xml_text)
        entries: list[RegistryEntry] = []

        for entry in root.findall("atom:entry", ATOM_NAMESPACE):
            raw_id = entry.findtext("atom:id", default="", namespaces=ATOM_NAMESPACE).rsplit("/", 1)[-1]
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
