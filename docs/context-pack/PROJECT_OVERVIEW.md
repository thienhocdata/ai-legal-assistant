# Tổng quan dự án

`Minh Long AI Legal Assistant` là trợ lý tra cứu pháp luật đất đai Việt Nam dựa trên RAG, ưu tiên truy hồi căn cứ và trích dẫn Điều–Khoản–Điểm. Sản phẩm hiện là demo/nghiên cứu, không thay thế luật sư hoặc cơ quan nhà nước.

## Trạng thái hiện hành

- API FastAPI và web chat tĩnh.
- Pipeline PDF → chuẩn hóa → cây pháp lý → chunks → embeddings → FAISS.
- Dense và hybrid retrieval có tăng trọng số tiêu đề pháp lý.
- Query rewriting, clarification, citation, provider local/Gemini/Qwen và guardrails.
- 30 câu ground truth; artifact hiện có báo cáo dense/hybrid.
- Bộ V2 hậu baseline có 60 câu ứng viên AI sinh đang chờ người duyệt: 50 câu
  answer và 10 câu refuse. Baseline gốc đạt Hit@1 76%, Hit@k 90%, broad-refusal
  3/10. Sau sửa routing trên chính dev V2: Hit@1 78%, Hit@k 92%, broad route
  match 10/10 (8 làm rõ, 2 thiếu nguồn); chưa đo trên V3 độc lập.
- 441 legal chunks, embeddings 441 × 384 và FAISS IndexFlatIP 441 vectors.
- Baseline sau promotion ngày 08/08/2026 là 38 test; quality hardening ngày
  15/11/2026 nâng bộ test lên 54 test; sau V2 đạt 70; sau vòng sửa hiện tại đạt
  116; vòng sửa chat ngày 17/11/2026 đạt 171. Cache đã chuyển vào runtime dir;
  còn warning deprecation TestClient/HTTPX.

Chat hỗ trợ context làm rõ client-only có giới hạn, một số cụm không dấu,
quote giữ nguyên với metadata integrity, UI single-flight và local readiness
probe khi startup. Local output so khớp nguyên văn; hosted chưa có semantic
entailment validation. Không coi 171 test là kiểm định pháp lý.

Bộ V2 được khóa với baseline commit
`73d3a141e51c7348763ead7379bf56bf36b54586` và dataset SHA-256
`fc892269eae03256ce8a2808c444c89a98af7ac3a16d62a97fabb452e8bef363` trước
khi đánh giá gốc. Vòng sửa mới đã dùng V1/V2 làm dev đã quan sát theo
`docs/evaluation/DATASET_ROLES.md`. Baseline và run sau sửa được giữ riêng;
không coi kết quả sau sửa là held-out hoặc xác nhận độ đúng pháp lý. Xem báo
cáo tổng quan và audit 19 lỗi trong `docs/evaluation/V2_FAILURE_AUDIT.md`.

## Phạm vi dữ liệu

Nguồn lõi production đã chuyển sang Văn bản hợp nhất 133/VBHN-VPQH từ ngày 08/08/2026, trích từ ba phần Công báo chính thức và qua quality gate. Bản gốc Luật 31/2024/QH15 vẫn được giữ để truy vết; Luật 43/2024/QH15 mới có metadata/URL. Văn bản hợp nhất là nguồn tra cứu thuận tiện, không tự chứng minh hiệu lực từng quy định hoặc thay thế việc kiểm tra văn bản liên quan.
