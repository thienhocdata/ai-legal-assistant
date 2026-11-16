from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    project_root: Path
    llm_provider: str = "none"
    retrieval_top_k: int = 5
    minimum_dense_score: float = 0.55

    @classmethod
    def from_env(
        cls,
        *,
        project_root: Path | None = None,
        env_file: Path | None = None,
    ) -> "Settings":
        root = (project_root or Path(__file__).resolve().parents[2]).resolve()
        load_dotenv(dotenv_path=env_file or root / ".env", override=False)
        return cls(
            project_root=root,
            llm_provider=os.getenv("LLM_PROVIDER", "none"),
            retrieval_top_k=int(os.getenv("RETRIEVAL_TOP_K", "5")),
            minimum_dense_score=float(os.getenv("MINIMUM_DENSE_SCORE", "0.55")),
        )
