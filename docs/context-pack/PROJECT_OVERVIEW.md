# Tổng quan dự án

`Minh Long AI Legal Assistant` là trợ lý tra cứu pháp luật đất đai Việt Nam dựa trên RAG, ưu tiên truy hồi căn cứ và trích dẫn Điều–Khoản–Điểm. Sản phẩm hiện là demo/nghiên cứu, không thay thế luật sư hoặc cơ quan nhà nước.

## Trạng thái hiện hành

- API FastAPI và web chat tĩnh.
- Pipeline PDF → chuẩn hóa → cây pháp lý → chunks → embeddings → FAISS.
- Dense và hybrid retrieval có tăng trọng số tiêu đề pháp lý.
- Query rewriting, clarification, citation, provider local/Gemini/Qwen và guardrails.
- 30 câu ground truth; artifact hiện có báo cáo dense/hybrid.
- 441 legal chunks, embeddings 441 × 384 và FAISS IndexFlatIP 441 vectors.
- Baseline sau promotion ngày 08/08/2026 là 38 test; quality hardening ngày
  15/11/2026 nâng bộ test lên 54 test đạt.

## Phạm vi dữ liệu

Nguồn lõi production đã chuyển sang Văn bản hợp nhất 133/VBHN-VPQH từ ngày 08/08/2026, trích từ ba phần Công báo chính thức và qua quality gate. Bản gốc Luật 31/2024/QH15 vẫn được giữ để truy vết; Luật 43/2024/QH15 mới có metadata/URL. Văn bản hợp nhất là nguồn tra cứu thuận tiện, không tự chứng minh hiệu lực từng quy định hoặc thay thế việc kiểm tra văn bản liên quan.
