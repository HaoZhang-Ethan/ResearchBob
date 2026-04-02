from __future__ import annotations

import json
import os
from dataclasses import dataclass

import httpx

from auto_research.models import InterestProfile, RegistryEntry
from auto_research.selection import RankedCandidate


class OpenAIClientError(RuntimeError):
    """Raised when the OpenAI API returns an unusable response."""


@dataclass(slots=True)
class SummaryArtifact:
    paper_id: str
    title: str
    confidence: str
    relevance_band: str
    opportunity_label: str
    one_sentence_summary: str
    problem: str
    proposed_solution: str
    claimed_contributions: list[str]
    evidence_basis: list[str]
    limitations: list[str]
    relevance_to_profile: str
    analyst_notes: str


def _extract_text(response_json: dict) -> str:
    parts: list[str] = []
    for item in response_json.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                parts.append(content["text"])
    text = "".join(parts).strip()
    if not text:
        raise OpenAIClientError("OpenAI response did not contain output text")
    return text


def _extract_text_from_sse(response_text: str) -> str:
    deltas: list[str] = []

    for raw_line in response_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("data: "):
            continue
        payload_text = line[6:].strip()
        if not payload_text or payload_text == "[DONE]":
            continue
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError:
            continue
        if payload.get("type") == "response.output_text.delta":
            delta = payload.get("delta")
            if isinstance(delta, str):
                deltas.append(delta)

    text = "".join(deltas).strip()
    if not text:
        raise OpenAIClientError("OpenAI SSE response did not contain output text deltas")
    return text


def _normalize_base_url(value: str) -> str:
    stripped = value.rstrip("/")
    if stripped.endswith("/responses"):
        return stripped
    return f"{stripped}/responses"


class OpenAIResponsesClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise OpenAIClientError("OPENAI_API_KEY is not set")
        self._model = model or os.environ.get("AUTO_RESEARCH_MODEL", "gpt-5.2")
        configured_base_url = (
            base_url
            or os.environ.get("OPENAI_BASE_URL")
            or os.environ.get("OPENAI_API_BASE")
            or "https://api.openai.com/v1/responses"
        )
        self._base_url = _normalize_base_url(configured_base_url)
        self._client = client or httpx.Client(timeout=60.0)

    def _request(self, *, instructions: str, input_payload: str, schema: dict) -> dict:
        response = self._client.post(
            self._base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "instructions": instructions,
                "input": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": input_payload,
                            }
                        ],
                    }
                ],
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": schema["name"],
                        "schema": schema["schema"],
                        "strict": True,
                    }
                },
            },
        )
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "text/event-stream" in content_type or response.text.lstrip().startswith("event:"):
            text = _extract_text_from_sse(response.text)
        else:
            text = _extract_text(response.json())
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise OpenAIClientError(f"OpenAI returned invalid JSON: {exc}") from exc

    def rank_candidates(
        self,
        *,
        profile: InterestProfile,
        candidates: list[RegistryEntry],
        top_k: int,
    ) -> list[RankedCandidate]:
        schema = {
            "name": "candidate_ranking",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "selected": {
                        "type": "array",
                        "maxItems": top_k,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "paper_id": {"type": "string"},
                                "priority_score": {"type": "integer"},
                                "reason": {"type": "string"},
                            },
                            "required": ["paper_id", "priority_score", "reason"],
                        },
                    }
                },
                "required": ["selected"],
            },
        }
        payload = json.dumps(
            {
                "profile": {
                    "core_interests": profile.core_interests,
                    "soft_boundaries": profile.soft_boundaries,
                    "current_phase_bias": profile.current_phase_bias,
                    "evaluation_heuristics": profile.evaluation_heuristics,
                },
                "task": (
                    "Select the top papers most worth deeper thought. Prioritize papers with strong problems, "
                    "clear relevance to the profile, and possible gaps or weak solutions."
                ),
                "candidates": [
                    {
                        "paper_id": entry.arxiv_id,
                        "title": entry.title,
                        "summary": entry.summary,
                        "relevance_band": entry.relevance_band,
                        "updated_at": entry.updated_at,
                    }
                    for entry in candidates
                ],
                "top_k": top_k,
            },
            ensure_ascii=False,
        )
        data = self._request(
            instructions=(
                "You rank arXiv candidates for idea discovery. Select only the most promising papers. "
                "Prefer good problems, solution gaps, and strong relevance to the user's interests."
            ),
            input_payload=payload,
            schema=schema,
        )
        return [
            RankedCandidate(
                paper_id=item["paper_id"],
                priority_score=item["priority_score"],
                reason=item["reason"],
            )
            for item in data["selected"]
        ]

    def summarize_paper(
        self,
        *,
        profile: InterestProfile,
        entry: RegistryEntry,
    ) -> SummaryArtifact:
        schema = {
            "name": "problem_solution_summary",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "paper_id": {"type": "string"},
                    "title": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    "relevance_band": {"type": "string", "enum": ["high-match", "adjacent", "low-priority"]},
                    "opportunity_label": {"type": "string", "enum": ["read-now", "follow-up", "skip", "manual-review"]},
                    "one_sentence_summary": {"type": "string"},
                    "problem": {"type": "string"},
                    "proposed_solution": {"type": "string"},
                    "claimed_contributions": {"type": "array", "items": {"type": "string"}},
                    "evidence_basis": {"type": "array", "items": {"type": "string"}},
                    "limitations": {"type": "array", "items": {"type": "string"}},
                    "relevance_to_profile": {"type": "string"},
                    "analyst_notes": {"type": "string"},
                },
                "required": [
                    "paper_id",
                    "title",
                    "confidence",
                    "relevance_band",
                    "opportunity_label",
                    "one_sentence_summary",
                    "problem",
                    "proposed_solution",
                    "claimed_contributions",
                    "evidence_basis",
                    "limitations",
                    "relevance_to_profile",
                    "analyst_notes",
                ],
            },
        }
        payload = json.dumps(
            {
                "profile": {
                    "core_interests": profile.core_interests,
                    "soft_boundaries": profile.soft_boundaries,
                    "current_phase_bias": profile.current_phase_bias,
                    "evaluation_heuristics": profile.evaluation_heuristics,
                },
                "paper": {
                    "paper_id": entry.arxiv_id,
                    "title": entry.title,
                    "summary": entry.summary,
                    "relevance_band": entry.relevance_band,
                    "pdf_url": entry.pdf_url,
                },
                "task": (
                    "Generate a concise abstract-level problem-solution artifact. "
                    "Do not pretend you have read the full PDF if you only have title and abstract. "
                    "Use medium or low confidence when evidence is limited."
                ),
            },
            ensure_ascii=False,
        )
        data = self._request(
            instructions=(
                "You produce short structured research summaries for idea discovery. "
                "Be concrete, cautious, and concise. Separate problem, solution, and limitations."
            ),
            input_payload=payload,
            schema=schema,
        )
        return SummaryArtifact(**data)
