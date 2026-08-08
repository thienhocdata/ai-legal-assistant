# Cổng tài liệu dự án

Ngày rà soát gần nhất: 05/08/2026.

## Đọc nhanh

1. `context-pack/PROJECT_OVERVIEW.md` — mục tiêu, phạm vi và trạng thái hiện hành.
2. `context-pack/ARCHITECTURE_MAP.md` — luồng dữ liệu và luồng trả lời.
3. `context-pack/DIRECTORY_MAP.md` — tìm code, dữ liệu và test.
4. `context-pack/DOCUMENT_STATUS.md` — tài liệu nào đang được tin cậy.

## Định tuyến theo công việc

- API, orchestration hoặc UI: `PROJECT_OVERVIEW.md`, `ARCHITECTURE_MAP.md`, `SYSTEM_REGISTRY.md`.
- Ingest, parser, chunking, embedding hoặc FAISS: `DATA_AND_LEGAL_SOURCES.md`, `ARCHITECTURE_MAP.md`, `TESTING_GUIDE.md`.
- Retrieval, query understanding hoặc evaluation: `ARCHITECTURE_MAP.md`, `KNOWN_ISSUES.md`, `TESTING_GUIDE.md`.
- Citation, LLM hoặc guardrails: `SECURITY_AND_PRIVACY.md`, `DATA_AND_LEGAL_SOURCES.md`, `TESTING_GUIDE.md`.
- Lập kế hoạch: `CURRENT_PRIORITIES.md`, `KNOWN_ISSUES.md`.
- Kiểm tra tài liệu cũ: `DOCUMENT_AUDIT_REPORT.md`, `context-pack/DOCUMENT_STATUS.md`.

## Nguồn chuẩn

- Kiến trúc hiện hành: `docs/architecture/system.md`, nhưng phải đối chiếu source và test.
- Cách cài đặt/chạy: `README.md`.
- Trạng thái artifact: các manifest trong `data/metadata/`, `data/processed/`, `data/vector_db/`.
- Hành vi hệ thống: source trong `app/` và test trong `tests/`.

Không dùng `docs/ghi chú/Bao_cao_nhat_ky_phat_trien_AI_Legal_Assistant_2026-07-10.docx` làm trạng thái hiện tại; đây là nhật ký lịch sử.
