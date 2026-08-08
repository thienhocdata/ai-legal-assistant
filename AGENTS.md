# Hướng dẫn làm việc với repository

## Điểm vào bắt buộc

Trước task lớn, đọc `docs/INDEX.md`, sau đó chỉ mở các tài liệu được định tuyến cho loại công việc đang làm. Tài liệu chỉ là bản đồ; khi có mâu thuẫn, ưu tiên source code, test, artifact/manifest thực tế và hành vi runtime.

## Nguyên tắc chung

- Giữ thay đổi nhỏ nhất đáp ứng yêu cầu; không tái cấu trúc ngoài phạm vi.
- Không coi báo cáo phát triển hoặc README module cũ là trạng thái hiện hành nếu chưa đối chiếu source.
- Không sửa trực tiếp artifact sinh tự động trong `data/processed/` hoặc `data/vector_db/`; dùng pipeline/script tương ứng.
- Không commit `.env`, API key, log chứa câu hỏi cá nhân, cache model hoặc dữ liệu nhạy cảm.
- Không khẳng định hiệu lực hay tính đầy đủ của văn bản pháp luật chỉ từ metadata hiện tại.
- Mọi thay đổi retrieval, citation, guardrail hoặc nguồn luật phải có test phù hợp.
- Không commit hoặc push nếu người dùng chưa yêu cầu rõ.

## Lệnh xác minh mặc định

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Với thay đổi dữ liệu, đọc `docs/context-pack/DATA_AND_LEGAL_SOURCES.md` và chạy validator/pipeline liên quan. Với API hoặc UI, kiểm tra `/api/health`, `/api/chat` và giao diện tại `/` khi môi trường cho phép.

## Phạm vi sản phẩm

Đây là trợ lý tra cứu pháp luật đất đai Việt Nam phục vụ demo/nghiên cứu. Không mô tả hệ thống là tư vấn pháp lý chuyên nghiệp hoặc kho pháp luật đầy đủ.
