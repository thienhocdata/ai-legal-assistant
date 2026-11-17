# Vấn đề đã biết

## Ưu tiên cao

- Bản PDF của 133/VBHN-VPQH có trang 218 là ảnh scan và chú thích hợp nhất gây nhiễu parser; pipeline đã tránh lỗi này bằng ba phần Công báo Word chính thức, nhưng nhánh PDF vẫn không được dùng để build index.
- Luật 43/2024/QH15 đã có metadata/URL nhưng chưa tải hoặc ingest.
- Kho luật chỉ có một văn bản lõi; câu hỏi ngoài phạm vi dễ thiếu căn cứ.
- Ground truth 30 câu còn nhỏ và chưa phải đánh giá pháp lý bởi chuyên gia.
- Production đã chuyển sang VBHN 133, nhưng ground truth 30 câu và bộ 35 truy vấn theo tiêu đề chưa phải đánh giá pháp lý bởi chuyên gia.
- Diagnostic ngày 15/11/2026 cho thấy ngưỡng dense `0,55` không phân biệt được
  nhóm answerable với missing-source; chưa nâng ngưỡng vì ngưỡng in-sample tốt
  nhất từ chối nhầm 20% câu dương và chưa có held-out validation.
- Candidate V2 có 60 câu tổng hợp chờ human review. Baseline lịch sử schema 1
  đạt status success `98%`, Hit@1 `76%`, Hit@k `90%`, MRR `0,825`, broad refusal
  `30%` và proxy routing+top1 `68,33%`. Đây là baseline trước vòng sửa, không
  phải metric hiện tại sau sửa hoặc độ chính xác pháp lý.
- V1/V2 đã được dùng làm dev theo `docs/evaluation/DATASET_ROLES.md`. V2.1 cần
  version/manifest mới nếu sửa nhãn. V3 độc lập và expert review vẫn chưa có.
- Routing đã tách loại nguồn thiếu và dữ kiện thiếu, sửa false refusal cho câu
  hỏi chung về bảng giá đất; các rule vẫn có thể bỏ sót cách diễn đạt mới.
- Sau sửa trên dev V2 còn 11/50 câu trượt hạng 1 và 4/50 trượt top-k. Nhãn
  vẫn chưa duyệt; 10/10 broad route match có Wilson95 72,25%–100%, chưa cho
  biết hiệu quả trên câu chưa quan sát.
- Extractive hiện trả tối đa ba evidence blocks. Việc có marker citation hoặc
  Điều kỳ vọng không chứng minh đầy đủ hay phù hợp cho vụ việc.
- Vòng sửa chat đã bỏ cắt quote ngầm, hỗ trợ context làm rõ tối đa 3 lượt và
  dictionary cụm không dấu. Chưa có hội thoại dài tổng quát, khôi phục dấu/tên
  riêng tùy ý, hoặc chấm semantic entailment cho hosted output. UI timeout
  chỉ hủy request phía client, không bảo đảm dừng computation đang chạy ở server.
- Schema 2 giữ đúng vị trí citation kể cả chunk trùng Điều, có cohort và Wilson
  95% cho tỷ lệ. MRR schema 1 từng bỏ trùng Điều nên không so chéo hai schema
  như một cải thiện hệ thống.
- Hybrid mặc định chưa đổi. Article-diversity/RRF là thử nghiệm chưa promote:
  giảm trùng Điều có thể loại mất evidence cần thiết và một số phương án giảm
  điểm trên dev.

## Kỹ thuật và vận hành

- Đường dẫn trong `vector_store_manifest.json` đã chuyển sang tương đối; cần
  tiếp tục kiểm tra portability trên Linux/CI thực tế.
- Requirements Module 7 bị lặp ở hai vị trí.
- README Module 9 chứa ràng buộc phát triển cũ.
- Event log production chưa có chính sách retention/redaction được tài liệu hóa.
- Log OSError không còn làm mất answer; lỗi lập trình khác không bị nuốt. Event
  chỉ ghi metadata kỹ thuật, không question/context. Readiness đã probe local
  model/index lúc startup, chưa phải live hosted-provider test hay load test.
- API/UI chưa có tài liệu triển khai production về auth, rate limit và CORS.
- `pytest.ini` đã chuyển cache sang `data/evaluation/runs/pytest-cache`; lỗi
  quyền ghi cache cũ đã được xử lý. Suite hiện còn cảnh báo deprecation của
  tích hợp Starlette/httpx.
- Chưa có API key cục bộ để chạy so sánh live Gemini/Qwen; mock test chỉ xác
  minh tích hợp, không chứng minh chất lượng câu trả lời.
