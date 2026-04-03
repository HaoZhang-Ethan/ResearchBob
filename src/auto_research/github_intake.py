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
