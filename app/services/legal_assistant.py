from __future__ import annotations

from dataclasses import asdict
import logging
from time import perf_counter
from typing import Any
import re

from app.agent import ClarificationEngine, QueryAnalyzer
from app.agent.conversation import apply_clarification_reply, fold_text, validate_clarification_context
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

    def answer(
        self,
        question: str,
        *,
        clarification_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        started = perf_counter()
        if fold_text(question.strip()).startswith("cau hoi moi:"):
            question = question.split(":", 1)[1].strip()
            clarification_context = None
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

        if self.SMALLTALK_RE.fullmatch(question.strip()) or re.fullmatch(
            r"(?:xin chao|chao|hello|hi|ban la ai|ban lam duoc gi)[!.?\s]*",
            fold_text(question.strip()),
        ):
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

        context = validate_clarification_context(clarification_context)
        if context:
            for earlier_input in [context["question"], *context["answers"]]:
                decision = self.guardrails.check_input(earlier_input)
                if not decision.allowed:
                    return self._finish(started, {
                        "status": "blocked", "answer": decision.message,
                        "guardrail": decision.to_dict(), "citations": [],
                    })
        previous = self.query_analyzer.analyze(context["question"]) if context else None
        if previous and self.clarification.clarify(previous).status not in {
            "needs_clarification", "insufficient_coverage",
        }:
            context = None
            previous = None
        if context and previous:
            if len(context["answers"]) >= 3:
                return self._finish(started, {
                    "status": "needs_clarification",
                    "answer": "Đã đạt giới hạn lượt bổ sung. Bạn hãy đặt lại câu hỏi đầy đủ trong một lượt.",
                    "clarification_questions": [], "citations": [],
                })
            replies = [*context["answers"], question.strip()]
            if len(context["question"]) + sum(map(len, replies)) > 6000:
                raise ValueError("Tổng câu hỏi và thông tin bổ sung vượt 6000 ký tự.")
            effective_question = context["question"] + "\nThông tin người dùng bổ sung: " + " | ".join(replies)
            analysis = self.query_analyzer.analyze(effective_question)
            apply_clarification_reply(analysis, previous, replies)
            next_context = {"question": context["question"], "answers": replies}
        else:
            analysis = self.query_analyzer.analyze(question)
            next_context = {"question": question.strip(), "answers": []}
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
                    **({"continuation_context": next_context}
                       if clarification.status in {"needs_clarification", "insufficient_coverage"}
                       and len(next_context["answers"]) < 3 else {}),
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
        output_decision = self.guardrails.check_grounded_output(
            response.text, citations, extractive=response.provider == "extractive"
        )
        if not output_decision.allowed and not isinstance(self.provider, ExtractiveProvider):
            generation_fallback_reason = output_decision.code
            response = ExtractiveProvider().generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
            )
            output_decision = self.guardrails.check_grounded_output(
                response.text, citations, extractive=True
            )

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
                "answer_validation": output_decision.to_dict(),
                "answer_citation_labels": sorted(
                    {int(label) for label in re.findall(r"\[(\d+)\]", answer)}
                ),
                "disclaimer": (
                    "Căn cứ là các văn bản trong citation. Chưa kiểm tra hiệu lực hiện hành "
                    "và văn bản sửa đổi. Thông tin chỉ phục vụ tham khảo; cần đối chiếu "
                    "toàn văn và tình tiết cụ thể trước khi áp dụng."
                    + (" Nội dung do mô hình sinh mới qua kiểm tra cấu trúc citation, "
                       "chưa xác minh mức hỗ trợ của từng nhận định."
                       if response.provider != "extractive" else "")
                ),
            },
        )

    def warmup(self) -> None:
        """Probe the local retrieval path, without calling a hosted answer API."""
        results = self.retriever.retrieve_hybrid(
            "Phạm vi điều chỉnh của Luật Đất đai", top_k=1
        )
        citations = self.citations.build(results)
        if not results or not citations:
            raise RuntimeError("Không có căn cứ để xác nhận retrieval sẵn sàng.")

    def _finish(
        self,
        started: float,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        payload["latency_ms"] = round((perf_counter() - started) * 1000, 2)
        try:
            self.logger.log("answer", {
                "status": payload.get("status"),
                "latency_ms": payload["latency_ms"],
                "citation_count": len(payload.get("citations", [])),
                "provider": payload.get("provider"),
                "generation_fallback_reason": payload.get(
                    "generation_fallback_reason"
                ),
            })
            payload["logging_status"] = "ok"
        except OSError:
            # Diagnostics must not discard a completed response. Never include
            # question/context or the possibly sensitive filesystem path in logs.
            logging.getLogger(__name__).warning("Technical event log write failed (OSError).")
            payload["logging_status"] = "unavailable"
        return payload
