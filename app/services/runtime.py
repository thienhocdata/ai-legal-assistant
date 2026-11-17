from __future__ import annotations

from threading import Event, Lock
from typing import Any, Callable


class RuntimeReadiness:
    """State of a startup local-retrieval probe, not a hosted API quality test."""

    def __init__(self) -> None:
        self._lock = Lock()
        self.completed = Event()
        self._status = "warming_up"
        self._error_code: str | None = None

    def probe(self, service_factory: Callable[[], Any]) -> None:
        try:
            service_factory().warmup()
        except Exception as exc:
            with self._lock:
                self._status = "failed"
                self._error_code = type(exc).__name__
        else:
            with self._lock:
                self._status = "ready"
        finally:
            self.completed.set()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "status": self._status,
                "ready": self._status == "ready",
                "error_code": self._error_code,
                "probe": "startup_local_retrieval",
                "hosted_provider_live_tested": False,
            }
