# Vấn đề đã biết

## Ưu tiên cao

- Corpus đang index là bản gốc Luật 31/2024/QH15, chưa phải Văn bản hợp nhất 133/VBHN-VPQH.
- Bản PDF của 133/VBHN-VPQH có trang 218 là ảnh scan và chú thích hợp nhất gây nhiễu parser; pipeline đã tránh lỗi này bằng ba phần Công báo Word chính thức, nhưng nhánh PDF vẫn không được dùng để build index.
- Index 133/VBHN-VPQH hiện chỉ là artifact thử nghiệm, chưa được chọn làm corpus production.
- Luật 43/2024/QH15 đã có metadata/URL nhưng chưa tải hoặc ingest.
- Kho luật chỉ có một văn bản lõi; câu hỏi ngoài phạm vi dễ thiếu căn cứ.
- Ground truth 30 câu còn nhỏ và chưa phải đánh giá pháp lý bởi chuyên gia.
- Hybrid retrieval trên 30 câu của index thử nghiệm đạt cùng baseline production; kết quả này chưa đủ để quyết định chuyển production.

## Kỹ thuật và vận hành

- `vector_store_manifest.json` chứa đường dẫn tuyệt đối Windows, không portable.
- Requirements Module 7 bị lặp ở hai vị trí.
- README Module 9 chứa ràng buộc phát triển cũ.
- Event log production chưa có chính sách retention/redaction được tài liệu hóa.
- API/UI chưa có tài liệu triển khai production về auth, rate limit và CORS.
- Pytest có thể cảnh báo permission khi ghi `.pytest_cache` trong môi trường hiện tại.
