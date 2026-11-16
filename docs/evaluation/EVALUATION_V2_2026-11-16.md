# Đánh giá V2 hậu baseline — 16/11/2026

## Kết luận ngắn

Bộ V2 gồm 60 câu hỏi ứng viên được sinh bằng AI sau khi baseline đã được xác
lập và được khóa bằng manifest trước khi chạy đánh giá. Toàn bộ 60 nhãn vẫn ở
trạng thái `ai_generated_candidate_pending_human_review`. Đây **không phải**
đánh giá độc lập, không phải tập expert-held-out và không thay thế thẩm định của
chuyên gia pháp luật.

Lần chạy `extractive_offline` đạt 98% answer success, 76% expected-article
Hit@1, 90% Hit@k, MRR 0,825, 30% refusal correctness và 68,33% grounded
behavior. Các số này là chỉ số kỹ thuật của ranking/routing trên bộ ứng viên,
không phải độ chính xác pháp lý hoặc chất lượng tư vấn.

## Artifact và provenance

- Dataset: `data/evaluation/candidate_questions_v2_blind.json`
- Manifest khóa dataset: `data/evaluation/candidate_questions_v2_blind_manifest.json`
- Kết quả: `data/evaluation/system_behavior_v2_blind_extractive.json`
- Baseline commit ghi trong manifest:
  `73d3a141e51c7348763ead7379bf56bf36b54586`
- SHA-256 của dataset ghi trong manifest:
  `fc892269eae03256ce8a2808c444c89a98af7ac3a16d62a97fabb452e8bef363`
- Thời điểm khóa: `2026-11-16T02:51:12.045867+07:00`
- Thời điểm đánh giá: `2026-11-16T05:01:47.984655+00:00`
- Chế độ provider: `extractive_offline`

Manifest được tạo trước artifact kết quả và gắn đồng thời baseline commit với
hash nội dung dataset. Evaluator từ chối chạy nếu SHA/path không khớp manifest,
ghi SHA của manifest, commit chạy, cấu hình và fingerprint của code/corpus/index
vào artifact kết quả. Lần chạy này có HEAD trùng baseline, nhưng worktree có các
file evaluator/config đang được bổ sung; trạng thái dirty và hash nội dung các
file liên quan được ghi công khai trong `provenance`. Vì vậy đây là dấu vết kiểm
toán tốt hơn, chưa phải bằng chứng tái lập từ một clean checkout độc lập.

## Thành phần bộ câu hỏi

| Thành phần | Số lượng |
|---|---:|
| Tổng số câu | 60 |
| Kỳ vọng trả lời (`answer`) | 50 |
| Kỳ vọng từ chối/làm rõ (`refuse`) | 10 |
| Direct | 20 |
| Colloquial/paraphrase | 18 |
| Multi-condition | 12 |
| Ambiguous/refusal | 10 |
| Nhãn chờ người duyệt | 60 |

`refuse` trong bộ này có nghĩa là không đưa ra kết luận pháp lý riêng cho vụ
việc khi thiếu dữ kiện trọng yếu hoặc nguồn hiện hành; hệ thống nên yêu cầu làm
rõ hoặc hướng dẫn xác minh, không phải từ chối mọi thông tin chung.

## Giao thức khóa hậu baseline

1. Metadata/protocol của dataset ghi nhận bộ câu hỏi được sinh sau baseline mà
   không đọc bộ câu hỏi baseline, báo cáo retrieval, rule query
   understanding/retriever hoặc test hiện có. Repository tự nó chỉ xác minh
   được baseline commit, thời điểm và hash; không chứng minh được mọi thứ người
   tạo đã hoặc chưa xem. Số Điều kỳ vọng được neo vào inventory Điều của corpus
   đã xử lý.
2. Gắn trạng thái chờ người duyệt cho toàn bộ nhãn. Việc sinh bởi AI và việc
   khóa bằng hash không làm bộ dữ liệu trở thành đánh giá độc lập hay
   expert-held-out.
3. Trước khi chạy evaluator, ghi baseline commit, SHA-256 của dataset, số câu,
   phân bố hành vi và thời điểm khóa vào manifest.
4. Chạy evaluator với dataset đã khóa và lưu nguyên kết quả
   `extractive_offline`.
5. Không điều chỉnh rule retrieval/query sau khi đã xem kết quả của lần chạy
   này. Nếu chuyên gia sửa nhãn hoặc nội dung câu hỏi, phải tạo phiên bản dataset
   và manifest mới; không sửa ngược V2 để cải thiện chỉ số.

## Kết quả có thể kiểm toán

| Chỉ số | Số đúng / mẫu số | Kết quả |
|---|---:|---:|
| Answer success | 49 / 50 | 98% |
| Expected-article Hit@1 | 38 / 50 | 76% |
| Expected-article Hit@k | 45 / 50 | 90% |
| Article MRR | — | 0,825 |
| Refusal correctness | 3 / 10 | 30% |
| Grounded behavior | 41 / 60 | 68,33% |

`answer_success` chỉ phản ánh provider trả về trạng thái thành công cho câu kỳ
vọng được trả lời. Hit@k kiểm tra Điều kỳ vọng có xuất hiện ở bất kỳ vị trí nào
trong danh sách citation, còn Hit@1 kiểm tra vị trí đầu. Vì
`ExtractiveProvider` chỉ trả evidence `[1]`, grounded behavior chỉ tính câu
answer đúng khi trạng thái thành công **và** Điều kỳ vọng ở hạng 1; tổng này gồm
38 câu answer và 3 câu refusal. MRR giữ lại thông tin thứ hạng thay vì biến
Hit@k thành độ đúng của câu trả lời.

Kết quả cho thấy expected article thường xuất hiện trong top-k nhưng chỉ đứng
đầu ở 38/50 câu answer; đồng thời 7/10 câu refusal chưa được xử lý đúng. Đây là
phát hiện để báo cáo và thiết kế một vòng đánh giá mới; không được dùng chính V2
để tinh chỉnh rule rồi báo cáo lại như held-out.

## Giới hạn diễn giải và xác minh

- Bộ câu hỏi và expected article đều do AI tạo, chưa được chuyên gia độc lập
  duyệt; vì vậy không được mô tả là benchmark pháp lý đã được xác nhận.
- Hit@1/Hit@k/MRR không chứng minh câu trả lời đầy đủ, đúng hiệu lực hoặc áp dụng
  đúng cho một vụ việc thực tế.
- Chế độ extractive offline không đại diện cho chất lượng của mọi provider LLM.
- Freeze bảo vệ tính truy vết sau baseline, nhưng không loại bỏ thiên lệch của
  người tạo câu hỏi hoặc biến bộ ứng viên thành expert-held-out.

Xác minh repository ngày 16/11/2026:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Kết quả: **70 passed**, kèm một `PytestCacheWarning` do môi trường không tạo
được `.pytest_cache`; cảnh báo này không phải test failure.
