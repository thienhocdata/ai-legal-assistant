# Cổng tài liệu dự án

Ngày rà soát gần nhất: 16/11/2026.

## Đọc nhanh

1. `context-pack/PROJECT_OVERVIEW.md` — mục tiêu, phạm vi và trạng thái hiện hành.
2. `context-pack/ARCHITECTURE_MAP.md` — luồng dữ liệu và luồng trả lời.
3. `context-pack/DIRECTORY_MAP.md` — tìm code, dữ liệu và test.
4. `context-pack/DOCUMENT_STATUS.md` — tài liệu nào đang được tin cậy.
5. `BAO_CAO_TONG_QUAN_DU_AN_AI_LUAT.md` — so sánh baseline với các thay đổi
   mới, tổng quan sản phẩm hiện tại, kết quả và hạn chế có bằng chứng.

## Định tuyến theo công việc

- API, orchestration hoặc UI: `PROJECT_OVERVIEW.md`, `ARCHITECTURE_MAP.md`, `SYSTEM_REGISTRY.md`.
- Ingest, parser, chunking, embedding hoặc FAISS: `DATA_AND_LEGAL_SOURCES.md`, `ARCHITECTURE_MAP.md`, `TESTING_GUIDE.md`.
- Retrieval, query understanding hoặc evaluation: `ARCHITECTURE_MAP.md`,
  `KNOWN_ISSUES.md`, `TESTING_GUIDE.md`; kết quả V2 tại
  `evaluation/EVALUATION_V2_2026-11-16.md`, so sánh provider tại
  `evaluation/PROVIDER_COMPARISON.md`.
- Vòng sửa sau V2: `evaluation/DATASET_ROLES.md` (dev/holdout và schema metric),
  `evaluation/V2_FAILURE_AUDIT.md` (19 lỗi); kết quả trước/sau trong báo cáo tổng quan.
- Citation, LLM hoặc guardrails: `SECURITY_AND_PRIVACY.md`, `DATA_AND_LEGAL_SOURCES.md`, `TESTING_GUIDE.md`.
- Lập kế hoạch: `CURRENT_PRIORITIES.md`, `KNOWN_ISSUES.md`.
- Kiểm tra tài liệu cũ: `DOCUMENT_AUDIT_REPORT.md`, `context-pack/DOCUMENT_STATUS.md`.

## Nguồn chuẩn

- Kiến trúc hiện hành: `docs/architecture/system.md`, nhưng phải đối chiếu source và test.
- Cách cài đặt/chạy: `README.md`.
- Trạng thái artifact: các manifest trong `data/metadata/`, `data/processed/`, `data/vector_db/`.
- Hành vi hệ thống: source trong `app/` và test trong `tests/`.

Không dùng `docs/ghi chú/Bao_cao_nhat_ky_phat_trien_AI_Legal_Assistant_2026-07-10.docx` làm trạng thái hiện tại; đây là nhật ký lịch sử.
