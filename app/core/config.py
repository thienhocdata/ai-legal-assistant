from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True, slots=True)
class Settings:
    project_root: Path
    llm_provider: str = "none"
    retrieval_top_k: int = 5
    minimum_dense_score: float = 0.55

    @classmethod
    def from_env(cls) -> "Settings":
        root = Path(__file__).resolve().parents[2]
        return cls(
            project_root=root,
            llm_provider=os.getenv("LLM_PROVIDER", "none"),
            retrieval_top_k=int(os.getenv("RETRIEVAL_TOP_K", "5")),
            minimum_dense_score=float(os.getenv("MINIMUM_DENSE_SCORE", "0.55")),
        )
