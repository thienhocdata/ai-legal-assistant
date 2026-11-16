# Vai trò dataset và cách diễn giải vòng sửa kỹ thuật

## Mốc chuyển vai trò

Ngày 16/11/2026, sau khi đã xem lỗi V2, người dùng yêu cầu sửa hệ thống dựa trên
phân tích lỗi. Từ vòng sửa này, V1 và V2 là **dữ liệu phát triển đã quan sát**.
Việc chạy lại V2 giúp so sánh regression/tác dụng của thay đổi trên dev; kết quả
đó không được trình bày như phép đo độc lập trên dữ liệu chưa từng thấy.

| Dataset | Vai trò hiện tại | Cách sử dụng |
|---|---|---|
| `test_questions_v1.json` | Development baseline, 30 câu | Regression và so sánh với baseline cũ |
| `candidate_questions_v2_blind.json` | Development candidate đã quan sát, 60 câu | Audit lỗi, routing, xếp hạng; nhãn vẫn chờ người duyệt |
| V2.1, nếu tạo | Dataset mới sau sửa nhãn | Phải ghi người/cách duyệt, lý do từng chỉnh sửa và manifest mới |
| V3 | Chưa có bộ câu độc lập đã hoàn thành | Chỉ công bố kết quả sau khi thực hiện giao thức bên dưới |

Tên file V2 chứa `blind` là tên lịch sử. Freeze manifest/SHA bảo vệ việc truy
vết nội dung, không chứng minh tính độc lập hoặc chất lượng nhãn. Dataset và
manifest V2 cũ được giữ nguyên để kiểm toán. Chính sách không tune trong
manifest cũ mô tả giai đoạn đo hậu baseline trước đây; tài liệu này ghi nhận
việc sử dụng tiếp V2 làm dev đã được yêu cầu rõ. Không sửa lịch sử thành một
benchmark độc lập.

## Metric schema 2.0

Evaluator mới không viết đè báo cáo schema cũ. Cần dùng output path mới.

| Tên | Ý nghĩa kỹ thuật |
|---|---|
| `answer_status_success_rate` | Tỷ lệ `status=success` trên nhóm kỳ vọng answer |
| `article_hit_at_1_rate` | Citation đầu tiên có một Điều kỳ vọng |
| `article_hit_at_k_rate` | Có một Điều kỳ vọng trong danh sách citation trả về |
| `article_mrr` | Trung bình nghịch đảo hạng citation đúng đầu tiên; miss = 0 |
| `refusal_route_match_rate` | Status thuộc `expected_statuses` trên nhóm refuse |
| `routing_and_top1_article_match_rate` | Answer cần success + Hit@1; refuse cần status phù hợp |
| `answer_cited_article_hit_rate` | Marker `[n]` trong answer tham chiếu một Điều kỳ vọng |
| `answer_cited_all_expected_articles_rate` | Marker `[n]` tham chiếu mọi Điều được liệt kê trong nhãn |

Các metric là kiểm tra status/thứ hạng/marker. Chúng không xác minh nội dung
đúng, hiệu lực luật, quan hệ suy luận giữa nhận định và trích dẫn, hoặc mức đầy
đủ của câu trả lời. All-label coverage cũng không đồng nghĩa completeness:
nhãn có thể còn thiếu hoặc có nhiều Điều là đáp án thay thế.

Schema 2 giữ nguyên vị trí citation kể cả khi nhiều chunk cùng Điều xuất hiện.
Schema cũ bỏ trùng Điều trước khi tính MRR, nên MRR mới có thể khác dù danh sách
citation không đổi. So sánh hai phương án phải dùng cùng phiên bản evaluator;
không ghép MRR schema 1 với schema 2 như một phép đo cải thiện hệ thống.

V2 hiện chỉ có expected behavior `refuse`, gộp clarification, thiếu nguồn và
các trạng thái không trả lời khác. Khi chưa có nhãn status chi tiết, evaluator
dùng tập legacy và ghi `uses_legacy_broad_refusal_status_set=true` ở từng câu.
Đây là phép khớp nhánh rộng, chưa phải đúng loại refusal. Dataset mới có thể
thêm `expected_statuses`, ví dụ `["needs_clarification"]`; schema sẽ kiểm tra
status đó thay vì coi mọi loại từ chối đều đúng.

Mỗi tỷ lệ đi kèm tử số, mẫu số và Wilson 95% tại `metric_details`. `cohorts`
tách theo `question_type` (direct, colloquial_paraphrase, multi_condition,
ambiguous_refusal; dataset không có trường này dùng unspecified). Wilson chỉ
mô tả bất định của tỷ lệ nhị thức dưới giả định lấy mẫu; nó không sửa thiên lệch
chọn câu, lỗi nhãn AI hoặc phụ thuộc giữa các câu. MRR không phải tỷ lệ nhị
thức nên không gắn Wilson. Nhóm không có mẫu phù hợp trả `null`, không trả 0%.

## Chạy lại từ clean checkout

Evaluator nhận `--require-clean`, kiểm tra source/artifact trước và sau lúc chạy.
Nó ghi commit, trạng thái worktree, cấu hình và fingerprint mọi module Python
trong `app/`, script evaluator, requirements và các artifact ảnh hưởng kết quả.
Nếu file bị thay đổi trong lúc chạy, evaluator dừng thay vì ghi report lẫn
phiên bản. Không đưa `.env`, secret hoặc cache model vào fingerprint/report.

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_system_behavior.py `
  --questions data\evaluation\candidate_questions_v2_blind.json `
  --manifest data\evaluation\candidate_questions_v2_blind_manifest.json `
  --output data\evaluation\runs\v2_dev_schema2.json `
  --dataset-role development_observed `
  --allow-code-drift --require-clean
```

`--allow-code-drift` công khai rằng commit đang chạy khác baseline được ghi
trong manifest dataset. Nó không biến kết quả đó thành cùng baseline. Output
cũ vẫn giữ nguyên commit/config và provenance của lần chạy cũ.

`--dataset-role` cho phép `development_observed` hoặc `candidate_unreviewed`;
cả hai đều không phải nhãn độc lập/chuyên gia. V1/V2 đã biết bị bắt buộc giữ
`development_observed`. Evaluator không cung cấp cờ tự biến dataset thành
expert-reviewed hay independent holdout.

## Giao thức V3 cần thực hiện

1. Chỉ định người viết câu và người duyệt nhãn. Muốn gọi là bộ độc lập, người
   viết không được dựa vào danh sách lỗi V2 hoặc rule mới để soạn câu tương ứng.
2. Soạn 30–40 câu mới với phân bố chủ đề, diễn đạt, nhiều điều kiện và các loại
   không trả lời được ghi trước; mỗi câu có nhãn Điều hoặc expected status cùng
   căn cứ và trạng thái review. Ghi rõ có hay không chuyên gia pháp lý duyệt.
3. Người viết giữ nội dung/nhãn khỏi vòng chỉnh code. Chốt code/config/corpus
   bằng commit và hash; đóng băng dataset bằng manifest trước lần chạy cuối.
4. Chạy một lần đo cuối theo cấu hình đã ghi, lưu toàn bộ kết quả. Nếu lỗi kỹ
   thuật buộc chạy lại, ghi rõ lý do và giữ cả lần lỗi; không âm thầm chọn số tốt.
5. Sau khi xem V3, mọi vòng sửa tiếp dùng V3 như dữ liệu đã quan sát; xác nhận
   độc lập tiếp theo cần bộ mới. Không tự đổi câu/nhãn để tăng điểm.

Khung bàn giao V3 dưới đây cố ý để rỗng và chỉ là hướng dẫn trong tài liệu;
chưa phải dataset để chạy hoặc bằng chứng rằng người độc lập đã viết/duyệt:

```json
{
  "dataset_metadata": {
    "dataset_id": "v3_pending_independent_author",
    "status": "not_created",
    "author": null,
    "reviewer": null,
    "legal_expert_reviewed": false,
    "frozen_code_commit": null
  },
  "questions": []
}
```

AI có thể hỗ trợ kiểm tra cấu trúc, tìm dẫn chiếu và tạo candidate, nhưng không
được tự điền author/reviewer thành một người thật hoặc đổi nhãn AI thành
human/expert review. Hiện chưa có live Qwen/Gemini comparison hay V3 độc lập;
các bước đó cần điều kiện thực tế và phải được ghi bằng artifact tương ứng.
