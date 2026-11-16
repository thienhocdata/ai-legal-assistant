from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from statistics import fmean
from time import perf_counter
from typing import Any, Callable, Protocol


class AnswerService(Protocol):
    def answer(self, question: str) -> dict[str, Any]: ...


ServiceFactory = Callable[[str], AnswerService]


@dataclass(slots=True)
class ProviderComparisonRunner:
    """Run the same explicit synthetic dataset through multiple answer providers."""

    service_factory: ServiceFactory

    def run(
        self,
        questions: list[dict[str, Any]],
        providers: list[str],
        *,
        dataset_sha256: str,
        include_answer_text: bool = False,
    ) -> dict[str, Any]:
        self._validate_questions(questions)
        normalized_providers = self._validate_providers(providers)
        provider_reports: list[dict[str, Any]] = []

        for requested_provider in normalized_providers:
            try:
                service = self.service_factory(requested_provider)
            except (ImportError, ValueError) as exc:
                provider_reports.append(
                    {
                        "requested_provider": requested_provider,
                        "setup_status": "not_configured",
                        "setup_error_code": type(exc).__name__,
                        "summary": self._summarize([]),
                        "rows": [],
                    }
                )
                continue

            rows: list[dict[str, Any]] = []
            for item in questions:
                started = perf_counter()
                try:
                    result = service.answer(str(item["question"]))
                    elapsed_ms = round((perf_counter() - started) * 1000, 2)
                    row = self._result_row(
                        item,
                        result,
                        requested_provider=requested_provider,
                        elapsed_ms=elapsed_ms,
                        include_answer_text=include_answer_text,
                    )
                except Exception as exc:
                    row = {
                        "question_id": str(item["question_id"]),
                        "requested_provider": requested_provider,
                        "status": "runner_error",
                        "error_code": type(exc).__name__,
                        "elapsed_ms": round((perf_counter() - started) * 1000, 2),
                        "citation_count": 0,
                        "fallback_used": False,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                    }
                rows.append(row)

            provider_reports.append(
                {
                    "requested_provider": requested_provider,
                    "setup_status": "ready",
                    "setup_error_code": None,
                    "summary": self._summarize(rows),
                    "rows": rows,
                }
            )

        return {
            "dataset_sha256": dataset_sha256,
            "question_count": len(questions),
            "question_text_stored": False,
            "answer_text_stored": include_answer_text,
            "label_status": "provider_runtime_comparison_not_legal_quality_review",
            "providers": provider_reports,
        }

    @staticmethod
    def hash_bytes(content: bytes) -> str:
        return sha256(content).hexdigest()

    @staticmethod
    def _validate_questions(questions: Any) -> None:
        if not isinstance(questions, list) or not questions:
            raise ValueError("Dataset provider comparison phải là JSON array không rỗng.")
        seen: set[str] = set()
        for index, item in enumerate(questions):
            if not isinstance(item, dict):
                raise ValueError(f"Question {index} phải là object.")
            question_id = str(item.get("question_id", "")).strip()
            question = str(item.get("question", "")).strip()
            if not question_id or not question:
                raise ValueError(f"Question {index} thiếu question_id hoặc question.")
            if question_id in seen:
                raise ValueError(f"Trùng question_id: {question_id}")
            seen.add(question_id)

    @staticmethod
    def _validate_providers(providers: Any) -> list[str]:
        allowed = {"extractive", "gemini", "qwen"}
        if not isinstance(providers, list) or not providers:
            raise ValueError("Cần ít nhất một provider để so sánh.")
        normalized = [str(value).strip().lower() for value in providers]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Danh sách provider bị trùng.")
        unsupported = sorted(set(normalized).difference(allowed))
        if unsupported:
            raise ValueError(f"Provider chưa được phép: {', '.join(unsupported)}")
        return normalized

    @classmethod
    def _result_row(
        cls,
        item: dict[str, Any],
        result: dict[str, Any],
        *,
        requested_provider: str,
        elapsed_ms: float,
        include_answer_text: bool,
    ) -> dict[str, Any]:
        usage = result.get("usage") if isinstance(result.get("usage"), dict) else {}
        input_tokens = cls._usage_value(usage, "prompt_tokens", "input_tokens")
        output_tokens = cls._usage_value(
            usage, "completion_tokens", "output_tokens"
        )
        total_tokens = cls._usage_value(usage, "total_tokens")
        if not total_tokens:
            total_tokens = input_tokens + output_tokens
        citations = result.get("citations") if isinstance(result.get("citations"), list) else []
        row: dict[str, Any] = {
            "question_id": str(item["question_id"]),
            "requested_provider": requested_provider,
            "actual_provider": result.get("provider"),
            "model": result.get("model"),
            "status": result.get("status", "unknown"),
            "elapsed_ms": elapsed_ms,
            "service_latency_ms": result.get("latency_ms"),
            "citation_count": len(citations),
            "cited_articles": sorted(
                {
                    int(citation["article_no"])
                    for citation in citations
                    if citation.get("article_no") is not None
                }
            ),
            "fallback_used": bool(result.get("generation_fallback_reason")),
            "fallback_reason": result.get("generation_fallback_reason"),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "answer_sha256": sha256(
                str(result.get("answer", "")).encode("utf-8")
            ).hexdigest(),
        }
        if include_answer_text:
            row["answer"] = str(result.get("answer", ""))
        return row

    @staticmethod
    def _usage_value(usage: dict[str, Any], *names: str) -> int:
        for name in names:
            value = usage.get(name)
            if isinstance(value, int) and value >= 0:
                return value
        return 0

    @staticmethod
    def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
        if not rows:
            return {
                "attempted": 0,
                "completed": 0,
                "runner_errors": 0,
                "success_count": 0,
                "fallback_count": 0,
                "native_response_count": 0,
                "mean_elapsed_ms": None,
                "total_tokens": 0,
            }
        completed = [row for row in rows if row["status"] != "runner_error"]
        return {
            "attempted": len(rows),
            "completed": len(completed),
            "runner_errors": len(rows) - len(completed),
            "success_count": sum(row["status"] == "success" for row in rows),
            "fallback_count": sum(bool(row.get("fallback_used")) for row in rows),
            "native_response_count": sum(
                row.get("actual_provider") == row.get("requested_provider")
                and not row.get("fallback_used")
                and row.get("status") != "runner_error"
                for row in rows
            ),
            "mean_elapsed_ms": round(
                fmean(float(row["elapsed_ms"]) for row in rows), 2
            ),
            "total_tokens": sum(int(row.get("total_tokens", 0)) for row in rows),
        }
