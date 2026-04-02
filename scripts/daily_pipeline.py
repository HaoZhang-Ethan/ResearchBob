from __future__ import annotations

import sys
from pathlib import Path


def run() -> int:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))

    from auto_research.env import load_env_file
    from auto_research.automation import PipelineConfig, run_daily_pipeline

    load_env_file(root / ".env.local")

    result = run_daily_pipeline(
        PipelineConfig(
            workspace=root / "research-workspace",
            push=True,
        )
    )
    print(result.report_path)
    print(result.ris_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
