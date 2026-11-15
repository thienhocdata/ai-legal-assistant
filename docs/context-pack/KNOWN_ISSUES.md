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

## Kỹ thuật và vận hành

- Đường dẫn trong `vector_store_manifest.json` đã chuyển sang tương đối; cần
  tiếp tục kiểm tra portability trên Linux/CI thực tế.
- Requirements Module 7 bị lặp ở hai vị trí.
- README Module 9 chứa ràng buộc phát triển cũ.
- Event log production chưa có chính sách retention/redaction được tài liệu hóa.
- API/UI chưa có tài liệu triển khai production về auth, rate limit và CORS.
- Pytest có thể cảnh báo permission khi ghi `.pytest_cache` trong môi trường hiện tại.
