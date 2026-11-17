# Bản đồ kiến trúc

## Luồng xây dựng knowledge base

`source_inventory.csv` → downloader → PDF parser → text normalizer → legal structure parser → baseline/legal chunker → chunk validator → multilingual-e5-small → FAISS IndexFlatIP.

Script điều phối chính: `scripts/run_pipeline.py`. Artifact sinh ra nằm trong `data/processed/` và `data/vector_db/`.

## Luồng trả lời

FastAPI `/api/chat` → `LegalAssistantService` → input guardrail → query analysis/rewriting → clarification → hybrid retriever → citation engine → evidence guardrail → extractive, Gemini hoặc Qwen provider → output citation guardrail → JSONL event log.

Từ vòng sửa chat 17/11/2026, request có context làm rõ tùy chọn, được giới hạn
và guard như input không tin cậy. Context chỉ ở bộ nhớ client, không session
server/event log. Startup probe local retriever/model quyết định readiness;
khởi tạo service và load artifact có lock. Log I/O failure không làm mất answer.
Local output kiểm tra renderer nguyên văn; hosted chỉ được xác minh cấu trúc
citation/integrity, không entailment pháp lý.

## Ranh giới tin cậy

- Downloader và metadata chịu trách nhiệm truy vết nguồn, nhưng metadata hiệu lực hiện chưa hoàn chỉnh.
- Parser/chunker phải giữ cấu trúc Điều–Khoản–Điểm và vượt validator.
- Embedding metadata, manifest và FAISS phải thống nhất count/dimension/model.
- Provider chỉ được dùng context truy hồi; output phải có citation hợp lệ.
- Guardrails giảm rủi ro nhưng không chứng minh tính đúng pháp lý.
