# Bản đồ kiến trúc

## Luồng xây dựng knowledge base

`source_inventory.csv` → downloader → PDF parser → text normalizer → legal structure parser → baseline/legal chunker → chunk validator → multilingual-e5-small → FAISS IndexFlatIP.

Script điều phối chính: `scripts/run_pipeline.py`. Artifact sinh ra nằm trong `data/processed/` và `data/vector_db/`.

## Luồng trả lời

FastAPI `/api/chat` → `LegalAssistantService` → input guardrail → query analysis/rewriting → clarification → hybrid retriever → citation engine → evidence guardrail → extractive, Gemini, Qwen hoặc OpenRouter provider → output citation guardrail → JSONL event log.

Nhánh hosted hiện có bước semantic routing trước luồng luật. Router đọc current
question, history bounded và gợi ý analysis, trả JSON route/query/reply cùng chỉ
số các lượt trước thực sự cần dùng. Trò chuyện không có citation luật; câu luật
vẫn phải qua scope/source/evidence checks. Câu viết lại của mô hình chỉ là query
tìm kiếm, không được coi là tình tiết hoặc nguồn luật. Router lỗi dùng local
fallback, không gọi hosted lặp thêm một vòng để che lỗi.

History có tối đa 8 tin user/assistant, 4000 ký tự/tin, tổng 12000. Chỉ ở bộ nhớ
tab và request; mọi role/content đều là input không tin cậy. Qwen routing/generation
nhận network timeout theo lượt, không thay đổi client dùng chung; đây không phải
bảo đảm hủy computation theo wall-clock. Cấu hình Qwen có thật nhưng lần gọi API
hiện bị HTTP403 từ nhà cung cấp; kiểm thử router/history thành công là mock/local.

OpenRouter dùng cùng adapter/budget và luồng kiểm tra; chỉ cho phép model miễn
phí với giới hạn giá 0, endpoint cố định. ERNIE đã trả lời thật cả hội thoại và
câu luật qua API; smoke test không chứng minh chất lượng pháp lý.

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
