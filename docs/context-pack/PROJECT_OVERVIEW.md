# Tổng quan dự án

`Minh Long AI Legal Assistant` là trợ lý tra cứu pháp luật đất đai Việt Nam dựa trên RAG, ưu tiên truy hồi căn cứ và trích dẫn Điều–Khoản–Điểm. Sản phẩm hiện là demo/nghiên cứu, không thay thế luật sư hoặc cơ quan nhà nước.

## Trạng thái hiện hành

- API FastAPI và web chat tĩnh.
- Pipeline PDF → chuẩn hóa → cây pháp lý → chunks → embeddings → FAISS.
- Dense và hybrid retrieval có tăng trọng số tiêu đề pháp lý.
- Query rewriting, clarification, citation, provider local/Gemini/Qwen và guardrails.
- 30 câu ground truth; artifact hiện có báo cáo dense/hybrid.
- Bộ V2 hậu baseline có 60 câu ứng viên AI sinh đang chờ người duyệt: 50 câu
  answer và 10 câu refuse. Lần chạy extractive offline đạt 98% answer success,
  76% expected-article Hit@1, 90% Hit@k, MRR 0,825, 30% refusal correctness và
  68,33% grounded behavior.
- 441 legal chunks, embeddings 441 × 384 và FAISS IndexFlatIP 441 vectors.
- Baseline sau promotion ngày 08/08/2026 là 38 test; quality hardening ngày
  15/11/2026 nâng bộ test lên 54 test; ngày 16/11/2026 bộ test đầy đủ đạt 70
  test, kèm cảnh báo không ghi được `.pytest_cache` nhưng không có test failure.

Bộ V2 được khóa với baseline commit
`73d3a141e51c7348763ead7379bf56bf36b54586` và dataset SHA-256
`fc892269eae03256ce8a2808c444c89a98af7ac3a16d62a97fabb452e8bef363` trước
khi đánh giá. Không có rule retrieval/query nào được điều chỉnh sau khi xem kết
quả. Bộ này không độc lập, không phải expert-held-out và không phải xác nhận độ
đúng pháp lý; chi tiết tại `docs/evaluation/EVALUATION_V2_2026-11-16.md`.

## Phạm vi dữ liệu

Nguồn lõi production đã chuyển sang Văn bản hợp nhất 133/VBHN-VPQH từ ngày 08/08/2026, trích từ ba phần Công báo chính thức và qua quality gate. Bản gốc Luật 31/2024/QH15 vẫn được giữ để truy vết; Luật 43/2024/QH15 mới có metadata/URL. Văn bản hợp nhất là nguồn tra cứu thuận tiện, không tự chứng minh hiệu lực từng quy định hoặc thay thế việc kiểm tra văn bản liên quan.
