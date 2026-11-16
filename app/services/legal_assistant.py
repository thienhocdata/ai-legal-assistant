from __future__ import annotations

from dataclasses import asdict
from time import perf_counter
from typing import Any
import re

from app.agent import ClarificationEngine, QueryAnalyzer
from app.citation import CitationEngine
from app.core.config import Settings
from app.guardrails import GuardrailEngine
from app.llm_provider import (
    BaseLLMProvider,
    ExtractiveProvider,
    ProviderError,
    create_llm_provider,
)
from app.observability import JsonlEventLogger
from app.rag.retriever import LegalRetriever


SYSTEM_PROMPT = """Bạn là trợ lý tra cứu pháp luật đất đai Việt Nam.
Chỉ sử dụng các căn cứ được cung cấp. Mỗi nhận định pháp lý phải gắn nhãn [n]
tương ứng. Nếu căn cứ không đủ, hãy nói rõ là chưa đủ căn cứ. Không tự suy đoán
hiệu lực văn bản, tình tiết vụ việc hoặc kết luận thay cho luật sư. Trả lời bằng
tiếng Việt, phân biệt quy định pháp luật với khuyến nghị người dùng nên xác minh."""


class LegalAssistantService:
    SMALLTALK_RE = re.compile(
        r"^(?:xin chào|chào|hello|hi|bạn là ai|bạn làm được gì)[!.?\s]*$",
        re.IGNORECASE,
    )
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        provider: BaseLLMProvider | None = None,
        retriever: LegalRetriever | None = None,
    ) -> None:
        self.settings = settings or Settings.from_env()
        root = self.settings.project_root
        self.provider = provider or create_llm_provider(self.settings.llm_provider)
        self.retriever = retriever or LegalRetriever(
            index_path=root / "data" / "vector_db" / "legal_chunks.faiss",
            vector_metadata_path=root / "data" / "vector_db" / "legal_chunks_metadata.json",
            embedding_manifest_path=root / "data" / "processed" / "legal_embeddings_manifest.json",
            chunks_path=root / "data" / "processed" / "legal_chunks.json",
            device="cpu",
        )
        self.query_analyzer = QueryAnalyzer()
        self.clarification = ClarificationEngine()
        self.citations = CitationEngine()
        self.guardrails = GuardrailEngine(
            minimum_dense_score=self.settings.minimum_dense_score
        )
        self.logger = JsonlEventLogger(
            root / "data" / "evaluation" / "runs" / "assistant_events.jsonl"
        )

    def answer(self, question: str) -> dict[str, Any]:
        started = perf_counter()
        input_decision = self.guardrails.check_input(question)
        if not input_decision.allowed:
            return self._finish(
                started,
                {
                    "status": "blocked",
                    "answer": input_decision.message,
                    "guardrail": input_decision.to_dict(),
                    "citations": [],
                },
            )

        if self.SMALLTALK_RE.fullmatch(question.strip()):
            return self._finish(
                started,
                {
                    "status": "smalltalk",
                    "answer": (
                        "Mình là trợ lý tra cứu pháp luật đất đai của Minh Long. "
                        "Mình tìm căn cứ Điều–Khoản–Điểm trong kho hiện có; "
                        "kết quả chỉ phục vụ tham khảo."
                    ),
                    "citations": [],
                },
            )

        analysis = self.query_analyzer.analyze(question)
        clarification = self.clarification.clarify(analysis)
        if clarification.status != "ready":
            return self._finish(
                started,
                {
                    "status": clarification.status,
                    "answer": clarification.reason,
                    "clarification_questions": clarification.questions,
                    "analysis": analysis.to_dict(),
                    "citations": [],
                },
            )

        results = self.retriever.retrieve_hybrid(
            analysis.rewritten_question,
            top_k=self.settings.retrieval_top_k,
        )
        citations = self.citations.build(results)
        evidence_decision = self.guardrails.check_evidence(results, citations)
        if not evidence_decision.allowed:
            return self._finish(
                started,
                {
                    "status": "insufficient_evidence",
                    "answer": evidence_decision.message,
                    "guardrail": evidence_decision.to_dict(),
                    "analysis": analysis.to_dict(),
                    "citations": [citation.to_dict() for citation in citations],
                },
            )

        context = self.citations.format_context(citations)
        prompt = (
            f"CÂU HỎI: {analysis.original_question}\n\n"
            f"CĂN CỨ TRUY XUẤT:\n{context}\n\n"
            "YÊU CẦU TRẢ LỜI:\n"
            "Trả lời theo cấu trúc: Kết luận ngắn; Điều kiện áp dụng; "
            "Ngoại lệ hoặc thông tin cần xác minh; Căn cứ. "
            "Mỗi nhận định pháp lý phải gắn [n]. Không lặp lại mục không có dữ liệu."
        )
        generation_fallback_reason = None
        try:
            response = self.provider.generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
            )
        except ProviderError as exc:
            if isinstance(self.provider, ExtractiveProvider):
                raise
            generation_fallback_reason = type(exc).__name__
            response = ExtractiveProvider().generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
            )
        output_decision = self.guardrails.check_output(response.text, len(citations))
        if not output_decision.allowed and not isinstance(self.provider, ExtractiveProvider):
            generation_fallback_reason = output_decision.code
            response = ExtractiveProvider().generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
            )
            output_decision = self.guardrails.check_output(response.text, len(citations))

        status = "success" if output_decision.allowed else "generation_rejected"
        answer = response.text if output_decision.allowed else output_decision.message
        return self._finish(
            started,
            {
                "status": status,
                "answer": answer,
                "analysis": analysis.to_dict(),
                "citations": [citation.to_dict() for citation in citations],
                "retrieval": {
                    "top_k": len(results),
                    "top_dense_score": float(results[0]["dense_score"]),
                    "top_combined_score": float(results[0]["score"]),
                    "top1_top2_score_margin": (
                        round(float(results[0]["score"]) - float(results[1]["score"]), 6)
                        if len(results) > 1 else None
                    ),
                    "margin_interpretation": "diagnostic_only_not_calibrated",
                },
                "provider": response.provider,
                "model": response.model,
                "usage": response.metadata.get("usage", {}),
                "generation_fallback_reason": generation_fallback_reason,
                "answer_citation_labels": sorted(
                    {int(label) for label in re.findall(r"\[(\d+)\]", answer)}
                ),
                "disclaimer": (
                    "Căn cứ là các văn bản trong citation. Chưa kiểm tra hiệu lực hiện hành "
                    "và văn bản sửa đổi. Thông tin chỉ phục vụ tham khảo; cần đối chiếu "
                    "toàn văn và tình tiết cụ thể trước khi áp dụng."
                ),
            },
        )

    def _finish(
        self,
        started: float,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        payload["latency_ms"] = round((perf_counter() - started) * 1000, 2)
        self.logger.log(
            "answer",
            {
                "status": payload.get("status"),
                "latency_ms": payload["latency_ms"],
                "citation_count": len(payload.get("citations", [])),
                "provider": payload.get("provider"),
                "generation_fallback_reason": payload.get(
                    "generation_fallback_reason"
                ),
            },
        )
        return payload
