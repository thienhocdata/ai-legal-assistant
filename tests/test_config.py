from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import Settings


def test_settings_load_local_env_without_overriding_process_env(
    tmp_path: Path,
    monkeypatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LLM_PROVIDER=qwen\nRETRIEVAL_TOP_K=3\nMINIMUM_DENSE_SCORE=0.7\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("RETRIEVAL_TOP_K", raising=False)
    monkeypatch.delenv("MINIMUM_DENSE_SCORE", raising=False)
    settings = Settings.from_env(project_root=tmp_path, env_file=env_file)
    assert settings.project_root == tmp_path.resolve()
    assert settings.llm_provider == "qwen"
    assert settings.retrieval_top_k == 3
    assert settings.minimum_dense_score == 0.7

    monkeypatch.setenv("LLM_PROVIDER", "none")
    settings = Settings.from_env(project_root=tmp_path, env_file=env_file)
    assert settings.llm_provider == "none"
