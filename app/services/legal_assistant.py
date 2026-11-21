from __future__ import annotations

import logging
from time import perf_counter
from typing import Any
import re

from app.agent import ClarificationEngine, QueryAnalyzer
from app.agent.chat_intents import ChatIntentReply, classify_chat_intent
from app.agent.concepts import (
    LAND_GENERAL_EXPLANATION, LAND_STATUTORY_ABSENCE, parse_concept_request,
)
from app.agent.conversation import apply_clarification_reply, fold_text, validate_clarification_context
from app.agent.dialogue_router import HostedDialogueRouter
from app.agent.history import validate_chat_history
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
from app.llm_provider.budget import RequestScopedProvider
from app.rag.retriever import LegalRetriever


SYSTEM_PROMPT = """Bạn là trợ lý tra cứu pháp luật đất đai Việt Nam.
Chỉ sử dụng các căn cứ được cung cấp. Mỗi nhận định pháp lý phải gắn nhãn [n]
tương ứng. Nếu căn cứ không đủ, hãy nói rõ là chưa đủ căn cứ. Không tự suy đoán
hiệu lực văn bản, tình tiết vụ việc hoặc kết luận thay cho luật sư. Trả lời bằng
tiếng Việt, dùng lời dễ hiểu và trả lời ngay vào ý người dùng hỏi. Không chép
hàng loạt điều luật thay cho lời giải thích. Chỉ thêm điều kiện, ngoại lệ hoặc
bước thực hiện khi câu hỏi cần đến; không ép mọi câu vào cùng một khuôn.
Phân biệt quy định pháp luật với khuyến nghị người dùng nên xác minh."""


class LegalAssistantService:
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
        conversation_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        started = perf_counter()
        if fold_text(question.strip()).startswith("cau hoi moi:"):
            question = question.split(":", 1)[1].strip()
            clarification_context = None
            conversation_history = None
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

        context = validate_clarification_context(clarification_context)
        history = validate_chat_history(conversation_history)
        if context and not history:
            history = [{"role": "user", "content": text}
                       for text in [context["question"], *context["answers"]]]
        history_guard = GuardrailEngine(max_question_chars=4000)
        for turn in history:
            decision = history_guard.check_input(turn["content"])
            if not decision.allowed:
                return self._finish(started, {
                    "status": "blocked", "answer": decision.message,
                    "guardrail": decision.to_dict(), "citations": [],
                })
        if context:
            for earlier_input in [context["question"], *context["answers"]]:
                decision = self.guardrails.check_input(earlier_input)
                if not decision.allowed:
                    return self._finish(started, {
                        "status": "blocked", "answer": decision.message,
                        "guardrail": decision.to_dict(), "citations": [],
                    })
        chat_reply = classify_chat_intent(question)
        routing_info = {"mode": "local_rules", "history_turns": len(history)}
        semantic = None
        routing_failure = None
        request_provider = self.provider
        if not isinstance(self.provider, ExtractiveProvider):
            route_provider = RequestScopedProvider(
                self.provider, deadline=started + 75, stage_limit_seconds=20,
            )
            try:
                semantic = HostedDialogueRouter(route_provider).route(
                    question, history, self.query_analyzer.analyze(question).to_dict(),
                )
                routing_info.update({"mode": "hosted", "route": semantic.route})
            except ProviderError as exc:
                routing_failure = type(exc).__name__
                routing_info.update({"mode": "local_fallback", "error_code": routing_failure})
                request_provider = ExtractiveProvider()

        base_analysis = self.query_analyzer.analyze(question)
        if semantic and semantic.route != "legal_lookup":
            legal_request = chat_reply is None and (
                base_analysis.in_scope or base_analysis.missing_source_types
                or re.search(r"\b(?:luat|phap luat|ly hon|thue|hop dong|bao hiem|bi phat)\b", fold_text(question))
            )
            if semantic.route == "conversation" and legal_request:
                routing_info["override"] = "legal_request_requires_evidence"
            elif semantic.route == "out_of_scope" and base_analysis.in_scope and chat_reply is None:
                routing_info["override"] = "land_request_requires_scope_checks"
            else:
                status = {"conversation": "smalltalk", "needs_clarification": "needs_clarification",
                          "out_of_scope": "out_of_scope"}[semantic.route]
                return self._finish(started, {
                    "status": status, "answer": semantic.reply, "citations": [],
                    "provider": semantic.provider, "model": semantic.model,
                    "conversation_mode": "hosted", "usage": semantic.usage,
                    "conversation_intent": chat_reply.intent if chat_reply else "open_conversation",
                    "dialogue_routing": routing_info,
                    "answer_validation": {"validation_scope": "router_format_only",
                                          "semantic_support_verified": False},
                    **({"continuation_context": context} if context and status == "smalltalk" else {}),
                })
        # A bare negative can answer a pending question about case facts. Do not
        # turn it into a goodbye or erase the bounded clarification chain.
        if chat_reply and semantic is None and not (
            context and chat_reply.intent == "decline"
        ):
            return self._finish(started, {
                **self._answer_chat(chat_reply, routing_failed=bool(routing_failure)),
                "dialogue_routing": routing_info,
                **({"generation_fallback_reason": routing_failure} if routing_failure else {}),
                **({"continuation_context": context}
                   if context and chat_reply.intent in {
                       "feedback_tone", "feedback_relevance", "rephrase_request",
                       "acknowledgement", "conversation_capability",
                   } else {}),
            })
        concept_answer = self._answer_concept(question)
        if concept_answer is not None:
            concept_answer["dialogue_routing"] = routing_info
            return self._finish(started, concept_answer)
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
        if semantic and semantic.route == "legal_lookup":
            selected_users = [history[index]["content"] for index in semantic.context_indices
                              if history[index]["role"] == "user"]
            if selected_users and not context:
                analysis = self.query_analyzer.analyze(
                    "\n".join([*selected_users, question])
                )
            rewrite_guard = self.guardrails.check_input(semantic.standalone_question)
            if not rewrite_guard.allowed:
                return self._finish(started, {
                    "status": "blocked", "answer": rewrite_guard.message,
                    "guardrail": rewrite_guard.to_dict(), "citations": [],
                })
            rewritten_analysis = self.query_analyzer.analyze(semantic.standalone_question)
            analysis.in_scope = analysis.in_scope or rewritten_analysis.in_scope
            analysis.missing_source_types = list(dict.fromkeys(
                base_analysis.missing_source_types + analysis.missing_source_types
                + rewritten_analysis.missing_source_types
            ))
            analysis.missing_context_types = list(dict.fromkeys(
                base_analysis.missing_context_types + analysis.missing_context_types
                + rewritten_analysis.missing_context_types
            ))
            if analysis.missing_source_types and "requires_source_outside_current_corpus" not in analysis.reasons:
                analysis.reasons.append("requires_source_outside_current_corpus")
            if rewritten_analysis.in_scope:
                analysis.rewritten_question = semantic.standalone_question
        clarification = self.clarification.clarify(analysis)
        if clarification.status != "ready":
            return self._finish(
                started,
                {
                    "status": clarification.status,
                    "answer": clarification.reason,
                    "clarification_questions": clarification.questions,
                    "analysis": analysis.to_dict(),
                    "dialogue_routing": routing_info,
                    **({"generation_fallback_reason": routing_failure} if routing_failure else {}),
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
            "Mở đầu bằng câu trả lời trực tiếp cho câu hỏi, dùng tiếng Việt dễ hiểu. "
            "Chỉ giải thích các căn cứ giúp trả lời ý đó; không liệt kê đoạn không liên quan. "
            "Nếu hỏi điều kiện thì nêu đủ điều kiện và ngoại lệ được căn cứ hỗ trợ; "
            "nếu hỏi thủ tục thì nêu các bước có trong nguồn. "
            "Mỗi nhận định pháp lý phải gắn [n]. Nói rõ phần chưa đủ căn cứ."
        )
        generation_fallback_reason = routing_failure
        generation_provider = request_provider
        if not isinstance(request_provider, ExtractiveProvider):
            generation_provider = RequestScopedProvider(
                request_provider, deadline=started + 75, stage_limit_seconds=45,
            )
        try:
            response = generation_provider.generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
            )
        except ProviderError as exc:
            if isinstance(generation_provider, ExtractiveProvider):
                raise
            generation_fallback_reason = type(exc).__name__
            response = ExtractiveProvider().generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
            )
        output_decision = self.guardrails.check_grounded_output(
            response.text, citations, extractive=response.provider == "extractive"
        )
        if not output_decision.allowed and not isinstance(generation_provider, ExtractiveProvider):
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
                "dialogue_routing": routing_info,
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

    def _answer_chat(self, reply: ChatIntentReply, *, routing_failed: bool = False) -> dict[str, Any]:
        payload = {
            "status": "smalltalk", "answer": reply.answer, "citations": [],
            "conversation_intent": reply.intent, "conversation_mode": "local_rules",
        }
        if routing_failed and reply.intent == "conversation_capability":
            payload["answer"] = (
                "Lượt này mình chưa nhận được phản hồi từ mô hình trò chuyện. "
                "Bạn có thể thử nhắn lại; hiện mình đang dùng phản hồi có sẵn."
            )
        return payload

    def _answer_concept(self, question: str) -> dict[str, Any] | None:
        request = parse_concept_request(question)
        if request is None:
            return None
        analysis = self.query_analyzer.analyze(question)
        if fold_text(request.term) == "dat dai" and not request.statutory:
            return {
                "status": "success", "answer": LAND_GENERAL_EXPLANATION,
                "answer_kind": "general_concept", "citations": [],
                "provider": "glossary", "model": "plain-language-v1",
                "analysis": analysis.to_dict(), "answer_citation_labels": [],
                "answer_validation": {
                    "validation_scope": "curated_nonlegal_explanation",
                    "semantic_support_verified": False,
                },
            }
        lookup = getattr(self.retriever, "lookup_definition", None)
        if not callable(lookup):
            return None
        result = lookup(request.term)
        if result is None:
            if not analysis.in_scope or not request.explicit_definition:
                return None
            return {
                "status": "insufficient_evidence",
                "answer": (
                    LAND_STATUTORY_ABSENCE if fold_text(request.term) == "dat dai"
                    else f'Mình chưa tìm thấy định nghĩa trực tiếp của “{request.term}” '
                    "trong kho luật hiện có. Mình chưa thể dùng các điều chỉ nhắc đến "
                    "thuật ngữ này để khẳng định đó là định nghĩa."
                ),
                "answer_kind": "definition_not_found", "citations": [],
                "analysis": analysis.to_dict(),
            }
        citations = self.citations.build([result])
        answer = self.citations.format_definition_answer(citations[0])
        decision = self.guardrails.check_grounded_output(
            answer, citations, extractive=True, definition=True,
        )
        return {
            "status": "success" if decision.allowed else "generation_rejected",
            "answer": answer if decision.allowed else decision.message,
            "answer_kind": "source_definition", "analysis": analysis.to_dict(),
            "citations": [citation.to_dict() for citation in citations],
            "provider": "extractive", "model": "deterministic-definition-v1",
            "retrieval": {"method": "exact_definition", "top_k": 1},
            "answer_validation": decision.to_dict(),
            "answer_citation_labels": [1] if decision.allowed else [],
            "disclaimer": (
                "Đây là định nghĩa trong văn bản đang tra cứu. Chưa kiểm tra hiệu lực "
                "hiện hành và văn bản sửa đổi."
            ),
        }

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
