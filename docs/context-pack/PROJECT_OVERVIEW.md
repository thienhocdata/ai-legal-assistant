# Tổng quan dự án

`Minh Luật` là trợ lý tra cứu pháp luật đất đai Việt Nam dựa trên RAG, ưu tiên truy hồi căn cứ và trích dẫn Điều–Khoản–Điểm. Sản phẩm hiện là demo/nghiên cứu, không thay thế luật sư hoặc cơ quan nhà nước.

## Trạng thái hiện hành

- API FastAPI và web chat tĩnh.
- Pipeline PDF → chuẩn hóa → cây pháp lý → chunks → embeddings → FAISS.
- Dense và hybrid retrieval có tăng trọng số tiêu đề pháp lý.
- Query rewriting, clarification, citation, provider local/Gemini và guardrails.
- 30 câu ground truth; artifact hiện có báo cáo dense/hybrid.
- 431 legal chunks, embeddings 431 × 384 và FAISS IndexFlatIP 431 vectors.
- 34 test đạt tại lần kiểm tra 08/08/2026.

## Phạm vi dữ liệu

Nguồn lõi production đang index là ba phần PDF bản gốc của Luật Đất đai 2024, số 31/2024/QH15. Văn bản hợp nhất 133/VBHN-VPQH đã được tải, qua quality gate và có index thử nghiệm riêng; Luật 43/2024/QH15 mới có metadata/URL. Vì production chưa chuyển sang bản hợp nhất, hệ thống không được coi corpus mặc định là nội dung hợp nhất đầy đủ để tự kết luận pháp luật hiện hành.
