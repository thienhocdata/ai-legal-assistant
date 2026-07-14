from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

import numpy as np


class BaseEmbedder(ABC):
    """Interface chung cho các embedding provider."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def dimension(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def encode_documents(
        self,
        texts: Sequence[str],
        *,
        batch_size: int = 32,
    ) -> np.ndarray:
        raise NotImplementedError

    @abstractmethod
    def encode_queries(
        self,
        texts: Sequence[str],
        *,
        batch_size: int = 32,
    ) -> np.ndarray:
        raise NotImplementedError
