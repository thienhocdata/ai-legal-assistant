# Quality hardening ngày 15/11/2026

## Phạm vi

Đợt này bổ sung công cụ đo giới hạn evidence guardrail, không tuyên bố nâng độ
chính xác pháp lý và không thay đổi corpus production. Bộ 30 câu retrieval cũ
được dùng làm nhóm dương; 30 câu diagnostic mới gồm 15 câu bị scope router loại
trước retrieval và 15 câu thuộc đất đai nhưng cần nguồn chưa có trong corpus.

Nhãn `missing_source` là nhãn kỹ thuật dựa trên inventory hiện hành, chưa được
chuyên gia pháp lý duyệt. Báo cáo calibration chọn và chấm ngưỡng trên cùng dữ
liệu nên là **in-sample diagnostic**, không phải held-out validation.

## Kết quả đo

| Nhóm | Số câu | Dense score nhỏ nhất | Trung vị | Lớn nhất |
|---|---:|---:|---:|---:|
| Answerable positive | 30 | 0,853728 | 0,905956 | 0,929356 |
| Missing source | 15 | 0,831392 | 0,861451 | 0,888160 |
| Upstream scope rejection | 15 | 0,762238 | 0,808588 | 0,841713 |

Ngưỡng production `0,55` đạt balanced accuracy `0,5` trên nhóm positive so với
missing-source, tức không loại được câu âm nào trong diagnostic này. Ngưỡng
in-sample tốt nhất là `0,890138`, balanced accuracy `0,9`, nhưng từ chối nhầm
20% câu dương. Vì tập nhỏ, nhãn chưa được duyệt và chưa có held-out validation,
ngưỡng production **không được tự động nâng** trong đợt này.

## Thay đổi an toàn đã áp dụng

- Nhận diện một số yêu cầu chắc chắn cần nguồn ngoài corpus hiện có: thuế, lệ
  phí trước bạ, mẫu đơn cụ thể, dữ liệu thửa đất trực tiếp và quy định địa phương.
- Các yêu cầu này trả `insufficient_coverage` trước retrieval, thay vì cố suy
  luận từ Văn bản hợp nhất Luật Đất đai.
- Câu chào hỏi/giới thiệu có nhánh tĩnh, không gọi retrieval hoặc hosted LLM.
- Qwen là provider opt-in; có giới hạn output, timeout, retry có giới hạn và
  extractive fallback cho lỗi provider đã phân loại.

## Việc chưa được coi là hoàn thành

- Chưa có held-out set do người độc lập xây dựng.
- Chưa có chuyên gia pháp lý duyệt nhãn Điều–Khoản–Điểm và missing-source.
- Chưa so sánh Qwen/Gemini/extractive vì repository không chứa API key.
- Chưa có số liệu citation correctness, faithfulness và answer completeness do
  người đánh giá chấm.

Các mục trên phải được báo cáo là pending, không được suy diễn từ retrieval
metric hoặc calibration diagnostic.

## Quy trình review câu trả lời cuối

Sao chép `data/evaluation/answer_review_template.json` sang một file review,
điền câu hỏi, câu trả lời và citation thực tế rồi cho người đánh giá đặt
`review_status: reviewed`. Với câu cần trả lời, bắt buộc chấm ba nhãn boolean:

- `citation_correct`: citation có hỗ trợ nhận định không;
- `faithful`: câu trả lời có bám hoàn toàn vào evidence không;
- `complete`: có đủ điều kiện và ngoại lệ quan trọng không.

Với câu cần từ chối, chấm `refusal_correct`. Sau đó chạy:

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_answer_reviews.py `
  --reviews <review-file.json> --output <report.json>
```

Không commit review chứa dữ liệu hồ sơ thật hoặc thông tin cá nhân.
