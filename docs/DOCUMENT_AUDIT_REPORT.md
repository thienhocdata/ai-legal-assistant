# Báo cáo kiểm toán tài liệu

Ngày kiểm toán: 05/08/2026. Phạm vi: repository hiện tại; không thay đổi source, dữ liệu hay artifact.

## Kết luận

Source, test và artifact hiện nhất quán ở mức kỹ thuật: 431 legal chunks, embedding 431 × 384, FAISS 431 vectors và bộ đánh giá 30 câu. Lệnh `pytest -q` đạt 25 test; có một cảnh báo do pytest không ghi được cache, không ảnh hưởng kết quả test.

Kho dữ liệu pháp luật chưa đủ điều kiện làm nguồn hiệu lực hoàn chỉnh. Sau kiểm toán, metadata Luật Đất đai 2024 đã được chuẩn hóa ngày ban hành/hiệu lực, URL, hash, trạng thái index và quan hệ sửa đổi. Tuy nhiên corpus đang index vẫn là bản gốc; Luật 43/2024/QH15 và Văn bản hợp nhất 133/VBHN-VPQH chưa được tải hoặc ingest.

## Phân loại

### ACTIVE

- `README.md`: hướng dẫn tổng quan, chạy ứng dụng và giới hạn sử dụng phù hợp source hiện tại.
- `docs/architecture/system.md`: mô tả đúng chuỗi 15 thành phần và ranh giới tin cậy chính.
- `data/metadata/processing_manifest.json`: cấu hình pipeline hiện hành.
- `data/metadata/source_inventory.csv`: inventory nguồn đã chuẩn hóa, gồm nguồn hợp nhất ưu tiên tiếp theo.
- Manifest trong `data/processed/` và `data/vector_db/`: nguồn trạng thái cho artifact đã sinh.

### NEEDS_REVIEW

- `app/kb/embedding/README_MODULE7.md`: nội dung kỹ thuật đúng cơ bản nhưng lệnh cài đặt dùng tên file tương đối không rõ điểm chạy và trùng requirements theo module.
- `data/metadata/documents/tthc_dang_ky_dat_dai.json`: chưa có URL định danh ổn định hoặc dữ kiện thủ tục đã xác minh.
- `data/vector_db/vector_store_manifest.json`: chứa đường dẫn tuyệt đối theo máy, giảm tính di động.

### STALE

- `docs/ghi chú/Bao_cao_nhat_ky_phat_trien_AI_Legal_Assistant_2026-07-10.docx`: đúng với mốc lịch sử nhưng không còn là trạng thái hiện hành. Tài liệu ghi 432 chunks và Module 10–15 chưa triển khai, trong khi hiện tại có 431 chunks và source/test cho query understanding, clarification, citation, answering, guardrails, evaluation/logging.
- `app/rag/README_MODULE9.md`: chỉ dẫn “chỉ thêm đúng 3 file” là ràng buộc của giai đoạn cũ; retriever hiện còn liên quan embedding, vector store, query understanding và evaluation.

### DUPLICATE

- `scripts/requirements_module7.txt` và `app/kb/embedding/requirements_module7.txt`: hai bản requirements theo module; `requirements.txt` ở root nên là điểm cài đặt mặc định.

### ARCHIVE_CANDIDATE

- Hai README module và báo cáo Word có thể chuyển vào khu vực lịch sử sau khi người dùng duyệt. Lượt kiểm toán này không di chuyển hoặc xóa file.

## Chênh lệch quan trọng

- Báo cáo Word: 432 chunks; artifact hiện tại: 431 chunks.
- Corpus 431 chunks hiện được tạo từ bản gốc Luật 31/2024/QH15, chưa phải Văn bản hợp nhất 133/VBHN-VPQH.
- README công bố hybrid retrieval v1 với 30 câu; các artifact đánh giá tương ứng có mặt, nhưng đây là baseline kỹ thuật, không phải thẩm định pháp lý chuyên gia.

## Hành động khuyến nghị

1. Tải và ingest Văn bản hợp nhất 133/VBHN-VPQH, đồng thời giữ provenance về các luật gốc/sửa đổi.
2. Đồng bộ document metadata sau mỗi pipeline run thay vì cập nhật thủ công.
3. Hợp nhất requirements module hoặc ghi rõ mục đích lịch sử.
4. Mở rộng ground truth và bổ sung quy trình chuyên gia pháp lý duyệt câu hỏi/đáp án.
5. Chỉ archive tài liệu cũ sau khi người dùng duyệt danh sách.

## Giới hạn kiểm toán

Tài liệu Word đã được trích xuất và đọc toàn bộ nội dung. Không thể render để kiểm tra hình thức vì môi trường không có LibreOffice/`soffice`; việc này không ảnh hưởng kết luận về độ mới của nội dung.
