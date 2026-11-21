# Tổng quan dự án

`Minh Long AI Legal Assistant` là trợ lý tra cứu pháp luật đất đai Việt Nam dựa trên RAG, ưu tiên truy hồi căn cứ và trích dẫn Điều–Khoản–Điểm. Sản phẩm hiện là demo/nghiên cứu, không thay thế luật sư hoặc cơ quan nhà nước.

## Trạng thái hiện hành

- API FastAPI và web chat tĩnh.
- Pipeline PDF → chuẩn hóa → cây pháp lý → chunks → embeddings → FAISS.
- Dense và hybrid retrieval có tăng trọng số tiêu đề pháp lý.
- Query rewriting, clarification, citation, provider local/Gemini/Qwen/OpenRouter và guardrails.
- 30 câu ground truth; artifact hiện có báo cáo dense/hybrid.
- Bộ V2 hậu baseline có 60 câu ứng viên AI sinh đang chờ người duyệt: 50 câu
  answer và 10 câu refuse. Baseline gốc đạt Hit@1 76%, Hit@k 90%, broad-refusal
  3/10. Sau sửa routing trên chính dev V2: Hit@1 78%, Hit@k 92%, broad route
  match 10/10 (8 làm rõ, 2 thiếu nguồn); chưa đo trên V3 độc lập.
- 441 legal chunks, embeddings 441 × 384 và FAISS IndexFlatIP 441 vectors.
- Baseline sau promotion ngày 08/08/2026 là 38 test; quality hardening ngày
  15/11/2026 nâng bộ test lên 54 test; sau V2 đạt 70; sau vòng sửa hiện tại đạt
  116; vòng sửa chat ngày 17/11/2026 đạt 171; vòng sửa trọng tâm ngày 18/11/2026
  đạt 307; sau UI/hội thoại 352; sau semantic router/history 439
  (wrapper chạy 19 Node tests).
  Cache đã chuyển vào runtime dir;
  còn warning deprecation TestClient/HTTPX.

Chat hỗ trợ context làm rõ client-only có giới hạn, một số cụm không dấu,
quote giữ nguyên với metadata integrity, UI single-flight và local readiness
probe khi startup. Local output so khớp nguyên văn; hosted chưa có semantic
entailment validation. Không coi bộ test phần mềm là kiểm định pháp lý.

Từ 18/11/2026, một số lời chào/góp ý/từ chối được xử lý riêng bằng rule có
giới hạn. Câu hỏi khái niệm có thể tra đúng một khoản định nghĩa nguyên văn
trong nguồn; riêng nghĩa thông thường của “đất đai” dùng giải thích biên soạn
sẵn, không gắn citation pháp lý. Câu hỏi pháp lý khác ở chế độ local vẫn là
trích xuất, chưa có khả năng tổng hợp linh hoạt. V2 dev chạy lại sau sửa giữ
39/50 Hit@1, 46/50 Hit@k và 35/50 độ phủ mọi nhãn trong answer; không phải
đo độc lập. Chi tiết: `docs/evaluation/CHAT_ANSWER_FOCUS_2026-11-18.md`.

Web chỉ còn ô chat và nguồn thu gọn. Hosted router đọc tin nhắn/lịch sử có giới
hạn để chọn trò chuyện hoặc tra luật; local vẫn dùng rule. History tối đa 8
tin, 4000 ký tự/tin, tổng 12000, chỉ trong tab/request. Đã cấu hình Qwen bằng
key/endpoint cục bộ và gọi thật; API trả HTTP403 AccessDenied.Unpurchased,
chưa có câu trả lời native thành công. Chủ tài khoản cần chốt điều kiện truy
cập. Các test Qwen hiện chỉ xác nhận hợp đồng/cơ chế qua mock.

Sau đó đã tích hợp OpenRouter, cố định ERNIE miễn phí. Lượt thử thật qua
`/api/chat` xác nhận cả hội thoại và sinh câu trả lời luật dùng
`provider=openrouter`, không fallback, API báo cost 0. Full suite sau tích hợp
đạt 457 test. Đây là smoke test, không phải kiểm định nội dung luật; nhánh hosted
vẫn chưa xác minh semantic support. Chi tiết và các lần lỗi giữ riêng tại
`docs/evaluation/OPENROUTER_INTEGRATION_2026-11-18.md`.

Bộ V2 được khóa với baseline commit
`73d3a141e51c7348763ead7379bf56bf36b54586` và dataset SHA-256
`fc892269eae03256ce8a2808c444c89a98af7ac3a16d62a97fabb452e8bef363` trước
khi đánh giá gốc. Vòng sửa mới đã dùng V1/V2 làm dev đã quan sát theo
`docs/evaluation/DATASET_ROLES.md`. Baseline và run sau sửa được giữ riêng;
không coi kết quả sau sửa là held-out hoặc xác nhận độ đúng pháp lý. Xem báo
cáo tổng quan và audit 19 lỗi trong `docs/evaluation/V2_FAILURE_AUDIT.md`.

## Phạm vi dữ liệu

Nguồn lõi production đã chuyển sang Văn bản hợp nhất 133/VBHN-VPQH từ ngày 08/08/2026, trích từ ba phần Công báo chính thức và qua quality gate. Bản gốc Luật 31/2024/QH15 vẫn được giữ để truy vết; Luật 43/2024/QH15 mới có metadata/URL. Văn bản hợp nhất là nguồn tra cứu thuận tiện, không tự chứng minh hiệu lực từng quy định hoặc thay thế việc kiểm tra văn bản liên quan.
