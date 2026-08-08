# Quy trình theo loại công việc

Đây là bản định tuyến công việc của repository, không phải danh sách package Python.

## Tài liệu và kiến trúc

Đọc `docs/INDEX.md`, kiểm tra source/test rồi cập nhật tài liệu duy nhất đang active. Không tạo README hoặc báo cáo mới nếu nội dung thuộc một tài liệu hiện có.

## Knowledge base

Đọc `DATA_AND_LEGAL_SOURCES.md`; thay đổi từ inventory/metadata nguồn; chạy script pipeline và validator; không sửa artifact nhị phân trực tiếp.

## Retrieval và evaluation

Giữ cùng dataset khi so sánh phương pháp; báo cáo Hit@k, Recall@k, MRR và latency; tách kết quả kỹ thuật khỏi kết luận pháp lý.

## Citation, LLM và guardrails

Kiểm tra bằng chứng đầu vào, citation hợp lệ, nhánh thiếu bằng chứng, prompt injection và fallback. Không cho phép provider suy đoán hiệu lực văn bản.

## API/UI

Giữ schema tương thích nếu không có yêu cầu breaking change; test API và kiểm tra trực quan UI khi có thay đổi giao diện.
