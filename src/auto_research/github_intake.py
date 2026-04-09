from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from auto_research.workspace import ensure_workspace

_HTTPS_REMOTE_RE = re.compile(r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$")
_SSH_REMOTE_RE = re.compile(r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$")
_FRONTMATTER_RE = re.compile(r"\A---\n(?P<frontmatter>.*?)\n---\n?(?P<body>.*)\Z", re.DOTALL)
_HEADING_RE = re.compile(r"^##\s+(?P<heading>[^\n]+)\n", re.MULTILINE)
_SAFE_SEGMENT_RE = re.compile(r"[^a-z0-9]+")
_BULLET_RE = re.compile(r"^- (?P<value>.+)$", re.MULTILINE)


class IssueParseError(ValueError):
    pass


@dataclass(slots=True)
class ParsedIssueBody:
    direction: str
    normalized_direction: str
    body: str
    background: str = ""
    requirements: str = ""
    constraints: str = ""
    notes: str = ""


@dataclass(slots=True)
class GitHubIssue:
    number: int
    title: str
    body: str
    author_login: str
    created_at: str
    updated_at: str
    url: str
    state: str


@dataclass(slots=True)
class IssueSyncConfig:
    workspace: Path
    repo: str | None = None
    state: str = "open"
    limit: int = 100
    push: bool = False


@dataclass(slots=True)
class IssueSyncResult:
    inspected_issue_count: int
    parsed_issue_count: int
    changed_request_count: int
    refreshed_summaries: list[Path]


@dataclass(slots=True)
class FallbackProfileResult:
    markdown: str
    repo: str | None
    issue_numbers: list[int]
    source_keys: list[str]
    direction: str


def discover_issue_directions(workspace: Path) -> list[str]:
    issue_root = workspace / "issue-intake"
    if not issue_root.exists():
        return []
    directions: list[str] = []
    for direction_dir in sorted(path for path in issue_root.iterdir() if path.is_dir()):
        if any((user_dir / "summary.md").exists() for user_dir in direction_dir.iterdir() if user_dir.is_dir()):
            directions.append(direction_dir.name)
    return directions


IssueFetcher = Callable[[str, str, int], list[GitHubIssue]]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _slugify(value: str) -> str:
    normalized = _SAFE_SEGMENT_RE.sub("-", value.strip().lower()).strip("-")
    if not normalized:
        raise IssueParseError("direction must normalize to a non-empty filesystem-safe value")
    return normalized


def parse_github_repo(remote_url: str) -> str:
    text = remote_url.strip()
    match = _HTTPS_REMOTE_RE.match(text) or _SSH_REMOTE_RE.match(text)
    if match is None:
        raise ValueError(f"Unsupported GitHub remote URL: {remote_url}")
    return f"{match.group('owner')}/{match.group('repo')}"


def _extract_sections(body: str) -> dict[str, str]:
    matches = list(_HEADING_RE.finditer(body))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group("heading").strip().lower()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[heading] = body[start:end].strip()
    return sections


def parse_issue_body(body: str) -> ParsedIssueBody:
    match = _FRONTMATTER_RE.match(body)
    if match is None:
        raise IssueParseError("Issue body must start with frontmatter containing direction")

    direction = ""
    for line in match.group("frontmatter").splitlines():
        key, _, value = line.partition(":")
        if key.strip() == "direction":
            direction = value.strip()
            break

    if not direction:
        raise IssueParseError("Issue frontmatter must include a non-empty direction")

    content = match.group("body").strip()
    sections = _extract_sections(content)
    return ParsedIssueBody(
        direction=direction,
        normalized_direction=_slugify(direction),
        body=content,
        background=sections.get("background", ""),
        requirements=sections.get("requirements", ""),
        constraints=sections.get("constraints", ""),
        notes=sections.get("notes", ""),
    )


def _load_profile(path: Path) -> dict[str, object]:
    if not path.exists():
        return {
            "direction": "",
            "github_username": "",
            "last_synced_at": "",
            "latest_issue_updated_at": "",
            "processed_issues": {},
        }
    return json.loads(path.read_text(encoding="utf-8"))


def _render_request_markdown(issue: GitHubIssue, parsed: ParsedIssueBody) -> str:
    lines = [
        "---",
        f"issue_number: {issue.number}",
        f"title: {json.dumps(issue.title, ensure_ascii=False)}",
        f"state: {json.dumps(issue.state, ensure_ascii=False)}",
        f"author_login: {json.dumps(issue.author_login, ensure_ascii=False)}",
        f"direction: {json.dumps(parsed.direction, ensure_ascii=False)}",
        f"normalized_direction: {json.dumps(parsed.normalized_direction, ensure_ascii=False)}",
        f"created_at: {json.dumps(issue.created_at, ensure_ascii=False)}",
        f"updated_at: {json.dumps(issue.updated_at, ensure_ascii=False)}",
        f"url: {json.dumps(issue.url, ensure_ascii=False)}",
        "---",
        "",
        "# Title",
        issue.title,
        "",
        "# Background",
        parsed.background or "_None_",
        "",
        "# Requirements",
        parsed.requirements or "_None_",
        "",
        "# Constraints",
        parsed.constraints or "_None_",
        "",
        "# Notes",
        parsed.notes or "_None_",
        "",
        "# Raw Body",
        parsed.body or "_Empty_",
        "",
    ]
    return "\n".join(lines)


def _load_request_metadata(request_path: Path) -> dict[str, str]:
    if not request_path.exists():
        return {}
    lines = request_path.read_text(encoding="utf-8").splitlines()
    metadata: dict[str, str] = {}
    if not lines or lines[0] != "---":
        return metadata
    for line in lines[1:]:
        if line == "---":
            break
        key, _, value = line.partition(":")
        metadata[key.strip()] = value.strip().strip('"')
    return metadata


def _collect_request_documents(requests_dir: Path) -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []
    if not requests_dir.exists():
        return documents
    for path in sorted(requests_dir.glob("*.md")):
        metadata = _load_request_metadata(path)
        metadata["path"] = str(path)
        documents.append(metadata)
    return documents


def _render_summary(direction: str, github_username: str, requests_dir: Path) -> str:
    documents = _collect_request_documents(requests_dir)
    lines = [
        f"# Issue Intake Summary: {direction} / {github_username}",
        "",
        f"- Direction: `{direction}`",
        f"- GitHub Username: `{github_username}`",
        f"- Request Count: {len(documents)}",
        "",
        "## Active Issues",
    ]
    if not documents:
        lines.append("- None")
    else:
        for document in documents:
            lines.append(
                f"- #{document.get('issue_number', '?')}: {document.get('title', '')} ({document.get('state', '')})"
            )
    return "\n".join(lines) + "\n"


def _extract_summary_section(text: str, heading: str) -> list[str]:
    pattern = re.compile(rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(text)
    if match is None:
        return []
    return [item.group("value").strip() for item in _BULLET_RE.finditer(match.group("body")) if item.group("value").strip()]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(normalized)
    return ordered


def _collect_issue_intake_sources(workspace: Path, direction: str | None = None) -> list[tuple[str, str, str]]:
    issue_root = workspace / "issue-intake"
    if not issue_root.exists():
        return []
    if direction:
        direction_dirs = [issue_root / direction]
    else:
        direction_dirs = sorted(path for path in issue_root.iterdir() if path.is_dir())
    sources: list[tuple[str, str, str]] = []
    for direction_dir in direction_dirs:
        if not direction_dir.is_dir():
            continue
        for user_dir in sorted(path for path in direction_dir.iterdir() if path.is_dir()):
            summary_path = user_dir / "summary.md"
            if not summary_path.exists():
                continue
            sources.append((direction_dir.name, user_dir.name, summary_path.read_text(encoding="utf-8")))
    return sources


def _collect_issue_numbers_for_source(user_dir: Path) -> list[int]:
    issue_numbers: list[int] = []
    for request_path in sorted((user_dir / "requests").glob("*.md")):
        metadata = _load_request_metadata(request_path)
        value = metadata.get("issue_number", "").strip()
        if value.isdigit():
            issue_numbers.append(int(value))
    return issue_numbers


def render_profile_from_issue_intake(workspace: Path) -> str:
    return build_fallback_profile_from_issue_intake(workspace).markdown


def build_fallback_profile_from_issue_intake(
    workspace: Path,
    direction: str | None = None,
    repo: str | None = None,
) -> FallbackProfileResult:
    sources = _collect_issue_intake_sources(workspace, direction)
    if not sources:
        if direction:
            raise ValueError(f"No usable issue intake data available for direction: {direction}")
        raise ValueError("No usable issue intake data available to generate an interest profile")

    source_lines = [f"> - {direction_name} / {username}" for direction_name, username, _ in sources]
    source_keys = [f"{direction_name}/{username}" for direction_name, username, _ in sources]
    core_interests = _dedupe([direction_name for direction_name, _, _ in sources])
    soft_boundaries: list[str] = []
    exclusions: list[str] = []
    current_phase_bias: list[str] = []
    evaluation_heuristics: list[str] = []
    open_questions: list[str] = []
    issue_numbers: list[int] = []

    for direction_name, _, text in sources:
        requirements = _extract_summary_section(text, "Requirements")
        constraints = _extract_summary_section(text, "Constraints")
        notes = _extract_summary_section(text, "Notes")
        active_issues = _extract_summary_section(text, "Active Issues")

        current_phase_bias.extend(requirements)
        exclusions.extend(constraints)
        open_questions.extend([item for item in notes if "?" in item])
        soft_boundaries.extend([item for item in notes if "?" not in item])
        evaluation_heuristics.extend([item for item in requirements if "prefer" in item.lower() or "priority" in item.lower()])
        soft_boundaries.extend([item for item in active_issues if direction_name not in item.lower()])

    issue_root = workspace / "issue-intake"
    for direction_name, username, _ in sources:
        issue_numbers.extend(_collect_issue_numbers_for_source(issue_root / direction_name / username))

    sections = {
        "Core Interests": _dedupe(core_interests + current_phase_bias[:2]) or ["issue-intake derived research topics"],
        "Soft Boundaries": _dedupe(soft_boundaries) or ["adjacent topics inferred from issue intake"],
        "Exclusions": _dedupe(exclusions) or ["no explicit exclusions were provided in issue intake"],
        "Current-Phase Bias": _dedupe(current_phase_bias) or ["focus on the active issue-intake directions"],
        "Evaluation Heuristics": _dedupe(evaluation_heuristics) or ["prefer papers aligned with the current issue-intake requests"],
        "Open Questions": _dedupe(open_questions) or ["which issue-intake directions should be prioritized next"],
    }

    lines = [
        "# Research Interest Profile",
        "",
        f"> Auto-generated from GitHub issue intake on {_utc_now_iso()}.",
        "> Sources:",
    ]
    lines.extend(source_lines)
    lines.append("")
    for section_name, items in sections.items():
        lines.append(f"## {section_name}")
        lines.extend(f"- {item}" for item in items)
        lines.append("")
    return FallbackProfileResult(
        markdown="\n".join(lines).rstrip() + "\n",
        repo=repo,
        issue_numbers=sorted(set(issue_numbers)),
        source_keys=source_keys,
        direction=direction or "all",
    )


def sync_issues(
    config: IssueSyncConfig,
    *,
    fetcher: IssueFetcher | None = None,
) -> IssueSyncResult:
    workspace = ensure_workspace(config.workspace)
    repo = config.repo or discover_github_repo()
    issue_fetcher = fetcher or fetch_github_issues
    issues = issue_fetcher(repo, config.state, config.limit)

    changed_request_count = 0
    parsed_issue_count = 0
    refreshed_summaries: list[Path] = []
    refreshed_keys: set[tuple[str, str]] = set()

    for issue in issues:
        try:
            parsed = parse_issue_body(issue.body)
        except IssueParseError:
            continue

        parsed_issue_count += 1
        user_root = workspace / "issue-intake" / parsed.normalized_direction / issue.author_login
        requests_dir = user_root / "requests"
        requests_dir.mkdir(parents=True, exist_ok=True)
        profile_path = user_root / "profile.json"
        request_path = requests_dir / f"{issue.number}.md"

        profile = _load_profile(profile_path)
        processed_issues = dict(profile.get("processed_issues", {}))
        previous_updated_at = processed_issues.get(str(issue.number))

        if previous_updated_at != issue.updated_at:
            request_path.write_text(_render_request_markdown(issue, parsed), encoding="utf-8")
            changed_request_count += 1

        processed_issues[str(issue.number)] = issue.updated_at
        latest_issue_updated_at = max(
            [value for value in processed_issues.values() if isinstance(value, str)],
            default=issue.updated_at,
        )
        profile_path.write_text(
            json.dumps(
                {
                    "direction": parsed.direction,
                    "github_username": issue.author_login,
                    "last_synced_at": _utc_now_iso(),
                    "latest_issue_updated_at": latest_issue_updated_at,
                    "processed_issues": processed_issues,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        refresh_key = (parsed.normalized_direction, issue.author_login)
        if refresh_key not in refreshed_keys:
            summary_path = user_root / "summary.md"
            summary_path.write_text(
                _render_summary(parsed.direction, issue.author_login, requests_dir),
                encoding="utf-8",
            )
            refreshed_summaries.append(summary_path)
            refreshed_keys.add(refresh_key)

    if config.push:
        _stage_commit_push_issue_intake(workspace, _utc_now_iso()[:10])

    return IssueSyncResult(
        inspected_issue_count=len(issues),
        parsed_issue_count=parsed_issue_count,
        changed_request_count=changed_request_count,
        refreshed_summaries=refreshed_summaries,
    )


def discover_github_repo(cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return parse_github_repo(result.stdout.strip())


def fetch_github_issues(repo: str, state: str, limit: int) -> list[GitHubIssue]:
    result = subprocess.run(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            "number,title,body,author,createdAt,updatedAt,url,state",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    issues: list[GitHubIssue] = []
    for item in payload:
        author = item.get("author") or {}
        issues.append(
            GitHubIssue(
                number=item["number"],
                title=item["title"],
                body=item["body"],
                author_login=author.get("login", ""),
                created_at=item["createdAt"],
                updated_at=item["updatedAt"],
                url=item["url"],
                state=item["state"],
            )
        )
    return issues


def comment_on_issue(*, repo: str, issue_number: int, body: str) -> None:
    subprocess.run(
        ["gh", "issue", "comment", str(issue_number), "--repo", repo, "--body", body],
        capture_output=True,
        text=True,
        check=True,
    )


def close_issue(*, repo: str, issue_number: int) -> None:
    subprocess.run(
        ["gh", "issue", "close", str(issue_number), "--repo", repo],
        capture_output=True,
        text=True,
        check=True,
    )


def _stage_commit_push_issue_intake(workspace: Path, label: str) -> None:
    repo_root = workspace.parent if workspace.name == "research-workspace" else Path.cwd()
    issue_intake_root = workspace / "issue-intake"
    subprocess.run(["git", "add", "-f", str(issue_intake_root)], cwd=repo_root, check=True)
    status = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if status.returncode == 0:
        return
    if status.returncode != 1:
        raise RuntimeError("Unable to determine staged git diff status for issue intake")
    subprocess.run(
        ["git", "commit", "-m", f"chore: sync issue intake {label}"],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(["git", "push"], cwd=repo_root, check=True)
