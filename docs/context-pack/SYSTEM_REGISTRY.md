# Danh mục thành phần hệ thống

| Thành phần | Source chính | Artifact/phụ thuộc | Test chính |
|---|---|---|---|
| API/UI | `app/main.py`, `app/static/` | KB artifacts | `tests/test_api.py` |
| Orchestration | `app/services/legal_assistant.py` | retriever, provider, guards | `tests/test_guardrails_service.py` |
| Query/clarification | `app/agent/` | câu hỏi người dùng | `tests/test_query_understanding.py` |
| Citation | `app/citation/` | retrieval results | `tests/test_citation_llm.py` |
| Guardrails | `app/guardrails/` | score và citation | `tests/test_guardrails_service.py` |
| LLM providers | `app/llm_provider/` | `LLM_PROVIDER`, Gemini/Qwen key tùy chọn | `tests/test_citation_llm.py`, `tests/test_openai_compatible_provider.py` |
| Acquisition | `app/kb/downloader/` | inventory/raw files | `tests/test_downloader.py` |
| Parse/normalize | `app/kb/parser/`, `app/kb/normalizer/` | PDF/TXT | parser/normalizer tests |
| Legal parsing/chunking | `app/kb/legal_parser/`, `app/kb/chunker/` | legal tree/chunks | legal parser/chunk tests |
| Embedding/vector store | `app/kb/embedding/`, `app/rag/vector_store.py` | NPY/FAISS/manifests | embedding/vector DB tests |
| Retrieval | `app/rag/retriever.py` | FAISS, metadata, chunks | retriever/evaluator tests |
| Evaluation/logging | `app/evaluation/`, `app/observability/` | test questions/reports/JSONL | evaluator tests |
