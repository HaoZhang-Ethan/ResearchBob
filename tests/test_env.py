from __future__ import annotations

import os

from auto_research.env import load_env_file


def test_load_env_file_sets_missing_values(tmp_path, monkeypatch) -> None:
    env_path = tmp_path / ".env.local"
    env_path.write_text(
        "OPENAI_API_KEY=test-key\nOPENAI_BASE_URL='http://example.test:8080'\nAUTO_RESEARCH_MODEL=gpt-5.4\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("AUTO_RESEARCH_MODEL", raising=False)

    load_env_file(env_path)

    assert os.environ["OPENAI_API_KEY"] == "test-key"
    assert os.environ["OPENAI_BASE_URL"] == "http://example.test:8080"
    assert os.environ["AUTO_RESEARCH_MODEL"] == "gpt-5.4"


def test_load_env_file_does_not_override_existing_values(tmp_path, monkeypatch) -> None:
    env_path = tmp_path / ".env.local"
    env_path.write_text("OPENAI_API_KEY=file-key\n", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")

    load_env_file(env_path)

    assert os.environ["OPENAI_API_KEY"] == "env-key"
