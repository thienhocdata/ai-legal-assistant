# Dữ liệu và nguồn pháp luật

## Nguồn hiện có

- Luật Đất đai 2024, số 31/2024/QH15: ba PDF từ miền `datafiles.chinhphu.vn`, đã lưu hash từng file và collection hash, trạng thái `indexed`. Corpus là bản gốc đã được sửa đổi.
- Luật 43/2024/QH15: URL và dữ kiện pháp lý đã xác minh, chưa tải file, trạng thái `pending`.
- Văn bản hợp nhất 133/VBHN-VPQH ngày 03/09/2025: đã tải PDF và ba phần Công báo dạng DOC chính thức, lưu hash từng file và bản DOCX chuyển đổi cục bộ. Nguồn Công báo qua quality gate với đủ 260 Điều, 0 tiêu đề đáng ngờ và 441 chunks; embeddings/FAISS chỉ nằm trong `data/experiments/`, chưa thay index chính.
- Technical diff theo Điều giữa production và bản hợp nhất: 225/260 Điều khớp sau chuẩn hóa khoảng trắng, 35 Điều có thay đổi cần kiểm tra citation/pháp lý; báo cáo nằm trong artifact thử nghiệm.
- Thủ tục đăng ký đất đai: metadata dự kiến, chưa có URL/file, trạng thái `pending`.

## Các trường bắt buộc trước khi coi một nguồn là sẵn sàng pháp lý

- Cơ quan ban hành, số/ký hiệu, ngày ban hành.
- Ngày hiệu lực hiện hành, ngày hết hiệu lực nếu có và trạng thái pháp lý.
- URL chính thức, thời điểm kiểm tra gần nhất và SHA-256 của file nguồn.
- Quan hệ sửa đổi, bổ sung, thay thế và văn bản liên quan.
- Phiên bản parser/chunker/embedding, thời điểm xử lý và trạng thái index.

## Quy tắc thay đổi dữ liệu

- Không sửa bằng tay file `.npy`, `.faiss` hoặc JSON sinh tự động để “khớp số”.
- Artifact thử nghiệm phải nằm trong `data/experiments/`; không được ghi vào `data/processed/` hoặc `data/vector_db/`.
- Cập nhật inventory/metadata nguồn, chạy pipeline, rồi xác minh manifest và test.
- Giữ nguyên raw source để truy vết; nguồn thay đổi phải có version/hash mới.
- Chỉ dùng nguồn chính thức hoặc nguồn được phê duyệt rõ ràng.
- Citation phải trỏ được về document và cấu trúc Điều–Khoản–Điểm; citation kỹ thuật không đồng nghĩa văn bản còn hiệu lực.
