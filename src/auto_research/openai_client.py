from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass

import httpx

from auto_research.models import InterestProfile, RegistryEntry
from auto_research.search_profile import SearchProfile
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


@dataclass(slots=True)
class IssueProfileArtifacts:
    interest_profile_markdown: str
    search_profile: SearchProfile


def _schema_section_field(name: str) -> dict:
    return {"type": "string", "description": name}


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
                    "Generate a concise problem-solution artifact that matches the existing extractor workflow. "
                    "Separate author claims, analyst inference, and uncertainty. "
                    "Do not pretend you have read the full PDF if you only have title and abstract. "
                    "Use medium or low confidence when evidence is limited."
                ),
            },
            ensure_ascii=False,
        )
        data = self._request(
            instructions=(
                "You are acting as the problem-solution-extractor skill. "
                "Produce a short structured artifact with one-sentence summary, problem, proposed solution, "
                "claimed contributions, evidence basis, limitations, relevance to profile, and analyst notes. "
                "Be concrete, cautious, and concise."
            ),
            input_payload=payload,
            schema=schema,
        )
        return SummaryArtifact(**data)

    def detailed_analyze_paper(
        self,
        *,
        profile: InterestProfile,
        entry: RegistryEntry,
        pdf_text: str,
    ) -> dict[str, str]:
        schema = {
            "name": "detailed_analysis",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "one_paragraph_summary": _schema_section_field("one_paragraph_summary"),
                    "problem": _schema_section_field("problem"),
                    "solution": _schema_section_field("solution"),
                    "key_mechanism": _schema_section_field("key_mechanism"),
                    "assumptions": _schema_section_field("assumptions"),
                    "strengths": _schema_section_field("strengths"),
                    "weaknesses": _schema_section_field("weaknesses"),
                    "what_is_missing": _schema_section_field("what_is_missing"),
                    "why_it_matters": _schema_section_field("why_it_matters"),
                    "follow_up_ideas": _schema_section_field("follow_up_ideas"),
                },
                "required": [
                    "one_paragraph_summary",
                    "problem",
                    "solution",
                    "key_mechanism",
                    "assumptions",
                    "strengths",
                    "weaknesses",
                    "what_is_missing",
                    "why_it_matters",
                    "follow_up_ideas",
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
                },
                "pdf_text": pdf_text[:60000],
                "task": (
                    "Generate a deeper analysis from the available paper text. "
                    "Focus on problem, solution, key mechanism, assumptions, strengths, weaknesses, "
                    "what is missing, why it matters to the profile, and plausible follow-up ideas. "
                    "Preserve uncertainty when the extracted text is noisy."
                ),
            },
            ensure_ascii=False,
        )
        return self._request(
            instructions=(
                "You are producing a detailed follow-up analysis for a shortlisted research paper. "
                "Use the full available text conservatively. "
                "Write concise but specific sections that help identify idea gaps and follow-up directions."
            ),
            input_payload=payload,
            schema=schema,
        )

    def summarize_daily_findings(
        self,
        *,
        profile: InterestProfile,
        analyses: list[dict[str, str]],
        failed_items: list[str],
    ) -> dict[str, object]:
        schema = {
            "name": "daily_summary",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "headline": {"type": "string"},
                    "top_takeaways": {"type": "array", "items": {"type": "string"}},
                    "good_problem_weak_solution": {"type": "array", "items": {"type": "string"}},
                    "worth_further_thought": {"type": "array", "items": {"type": "string"}},
                    "recurring_themes": {"type": "array", "items": {"type": "string"}},
                    "failed_or_retry": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "headline",
                    "top_takeaways",
                    "good_problem_weak_solution",
                    "worth_further_thought",
                    "recurring_themes",
                    "failed_or_retry",
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
                "analyses": analyses,
                "failed_items": failed_items,
                "task": (
                    "Summarize today's analyzed papers for idea discovery. "
                    "Highlight good problems, weak solutions, recurring themes, and papers worth further thought."
                ),
            },
            ensure_ascii=False,
        )
        return self._request(
            instructions=(
                "You are producing a daily research-idea summary. "
                "Be concise, selective, and oriented toward idea discovery. "
                "Explicitly identify recurring themes across today's papers."
            ),
            input_payload=payload,
            schema=schema,
        )

    def update_longterm_findings(
        self,
        *,
        profile: InterestProfile,
        previous_summary: str,
        analyses: list[dict[str, str]],
        daily_summary: dict[str, object],
    ) -> str:
        schema = {
            "name": "longterm_summary",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "markdown": {"type": "string"},
                },
                "required": ["markdown"],
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
                "previous_summary": previous_summary,
                "analyses": analyses,
                "daily_summary": daily_summary,
                "task": (
                    "Update a rolling long-term summary organized by recurring problem clusters, "
                    "common weaknesses in existing solutions, and the most promising directions."
                ),
            },
            ensure_ascii=False,
        )
        data = self._request(
            instructions=(
                "You maintain a long-term research summary. "
                "Keep it compact, cumulative, and organized by problem clusters, recurring gaps, and the most promising directions."
            ),
            input_payload=payload,
            schema=schema,
        )
        return data["markdown"]

    def build_issue_profiles(self, *, direction: str, issue_texts: list[str]) -> IssueProfileArtifacts:
        schema = {
            "name": "issue_profile_artifacts",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "interest_profile_markdown": {"type": "string"},
                    "search_profile": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "direction": {"type": "string"},
                            "canonical_topic": {"type": "string"},
                            "aliases": {"type": "array", "items": {"type": "string"}},
                            "related_terms": {"type": "array", "items": {"type": "string"}},
                            "exclude_terms": {"type": "array", "items": {"type": "string"}},
                            "preferred_problem_types": {"type": "array", "items": {"type": "string"}},
                            "preferred_system_axes": {"type": "array", "items": {"type": "string"}},
                            "retrieval_hints": {"type": "array", "items": {"type": "string"}},
                            "seed_queries": {"type": "array", "items": {"type": "string"}},
                            "source_preferences": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": [
                            "direction",
                            "canonical_topic",
                            "aliases",
                            "related_terms",
                            "exclude_terms",
                            "preferred_problem_types",
                            "preferred_system_axes",
                            "retrieval_hints",
                            "seed_queries",
                            "source_preferences",
                        ],
                    },
                },
                "required": ["interest_profile_markdown", "search_profile"],
            },
        }
        data = self._request(
            instructions="Turn issue intake into an interest profile and a retrieval-oriented search profile.",
            input_payload=json.dumps({"direction": direction, "issue_texts": issue_texts}, ensure_ascii=False),
            schema=schema,
        )
        return IssueProfileArtifacts(
            interest_profile_markdown=data["interest_profile_markdown"],
            search_profile=SearchProfile(**data["search_profile"]),
        )

    def retrieve_web_candidates(self, *, search_profile: SearchProfile, limit: int) -> list[dict[str, object]]:
        schema = {
            "name": "web_retrieval_candidates",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "candidates": {
                        "type": "array",
                        "maxItems": limit,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "title": {"type": "string"},
                                "authors": {"type": "array", "items": {"type": "string"}},
                                "year": {"type": "integer"},
                                "arxiv_id": {"type": "string"},
                                "landing_page_url": {"type": "string"},
                                "pdf_url": {"type": "string"},
                                "source_family": {"type": "string"},
                                "relevance_reason": {"type": "string"},
                            },
                            "required": [
                                "title",
                                "authors",
                                "year",
                                "arxiv_id",
                                "landing_page_url",
                                "pdf_url",
                                "source_family",
                                "relevance_reason",
                            ],
                        },
                    }
                },
                "required": ["candidates"],
            },
        }
        data = self._request(
            instructions="Use broader web retrieval to find paper candidates matching the search profile.",
            input_payload=json.dumps({"search_profile": asdict(search_profile), "limit": limit}, ensure_ascii=False),
            schema=schema,
        )
        return list(data["candidates"])
