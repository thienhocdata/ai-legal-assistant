# So sánh provider an toàn

Script `scripts/compare_answer_providers.py` chạy cùng một dataset tổng hợp qua
extractive, Gemini và Qwen để thu thập trạng thái, latency, token, citation và
fallback. Kết quả này chỉ phản ánh hành vi runtime; không phải đánh giá độ đúng
pháp lý nếu chưa có human review.

## Nguyên tắc riêng tư

- Input bắt buộc nằm trong `data/evaluation/`.
- Output bắt buộc nằm trong `data/evaluation/runs/`, thư mục đã được gitignore.
- Báo cáo mặc định chỉ lưu `question_id`, không lưu nguyên câu hỏi hoặc câu trả lời.
- Muốn lưu câu trả lời để human review phải truyền đồng thời
  `--include-answer-text --acknowledge-synthetic-data` và chỉ dùng dữ liệu tổng
  hợp không chứa hồ sơ cá nhân.
- Script không đọc hoặc ghi API key vào báo cáo. Cấu hình ứng dụng nạp `.env`
  cục bộ với `override=False`, nên biến môi trường của tiến trình vẫn được ưu
  tiên; thiếu key được ghi là `not_configured` mà không lưu thông báo có thể
  chứa bí mật.

## Chạy extractive không cần key

```powershell
.\.venv\Scripts\python.exe scripts\compare_answer_providers.py `
  --questions data\evaluation\candidate_questions_v2_blind.json `
  --providers extractive
```

## Chạy hosted providers

Đặt `GEMINI_API_KEY` hoặc `QWEN_API_KEY` trong file `.env` cục bộ hoặc
environment của tiến trình, không commit và không gửi key qua chat. Sau đó chạy:

```powershell
.\.venv\Scripts\python.exe scripts\compare_answer_providers.py `
  --questions data\evaluation\candidate_questions_v2_blind.json `
  --providers extractive gemini qwen --require-all
```

`--require-all` chỉ đạt khi mọi provider khởi tạo được, không có runner error,
không fallback và mỗi provider có ít nhất một phản hồi do chính provider đó sinh
ra. Vì một số câu có thể bị guardrail/clarification chặn trước bước generation,
`native_response_count` không nhất thiết bằng tổng số câu.

Không có API key thì mock test chỉ chứng minh request/fallback hoạt động đúng,
không chứng minh chất lượng câu trả lời của provider.
