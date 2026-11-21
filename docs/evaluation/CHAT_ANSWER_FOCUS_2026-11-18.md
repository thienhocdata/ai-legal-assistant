# Hội thoại và trọng tâm câu trả lời — 18/11/2026

## Cập nhật cuối: semantic router/history và quyền truy cập Qwen

Nhánh hosted đã thay luồng chỉ nhận câu mẫu bằng router dùng mô hình, đọc
tin nhắn hiện tại và lịch sử có giới hạn để chọn conversation/legal/clarify/
out-of-scope. JSON route/query được kiểm tra, source-gap không được xóa bởi
query viết lại; nhánh luật vẫn truy hồi căn cứ mới và qua guard. Router lỗi
dùng local fallback thay vì gọi hosted vòng nữa. Qwen có network timeout theo
lượt, không sửa client dùng chung và không hứa hủy computation theo wall-clock.

History ở tab/request, tối đa 8 tin, 4000 ký tự/tin, tổng 12000. Chỉ các lượt
hoàn thành được gửi; không có system role, không lưu localStorage/server hoặc
raw history vào log. Tin quá dài được bỏ nguyên thay vì cắt quote.

Full suite cuối: **439 passed, 1 warning**, gồm wrapper chạy **19 Node tests**.
Doctor local xác nhận 441 chunks/vectors, chiều384, hash/IDs/vector khớp. V2
dev cuối ở `runs/system_behavior_v2_semantic_history_dev_20261118_final.json`
giữ nguyên 39/50 Hit@1,46/50 Hit@k,35/50 marker coverage,10/10 broad route match.
Provenance working tree dirty; không gọi là clean-checkout hoặc held-out run.

Đã có key và endpoint Qwen trong `.env` gitignore, đã gửi request thật. Lỗi
quan sát: **HTTP403 AccessDenied.Unpurchased**. Chưa có native answer thành
công, chưa chấm chất lượng Qwen. Chủ tài khoản đang kiểm tra hoàn tất đăng ký,
kích hoạt và quyền dùng model. Tài liệu nhà cung cấp:
[mã lỗi](https://www.alibabacloud.com/help/en/model-studio/error-code-start).
Không lưu key/endpoint workspace trong tài liệu chia sẻ. Những dòng “chưa có
key” ở các mục lịch sử bên dưới thuộc mốc trước khi người dùng cung cấp key.

Runbook: `docs/DEMO_HANDOFF.md`; mẫu20case tất cả PENDING; báo cáo cuối khóa
mới là dự thảo cần thông tin trường/vai trò/thời gian/người hướng dẫn thật.

## Bổ sung: khung chat và phản hồi hội thoại

- Bỏ hero, sidebar, metric và quy trình kỹ thuật khỏi trang; giữ khung chat,
  ô nhập, nút Gửi và nguồn thu gọn. Có cache version cho CSS/JS để tránh dùng
  layout hoặc logic cũ sau khi tải lại trang.
- Tái hiện thêm hai lượt “được ổn áp á chứ” và “bạn không đối thoại với mình
  được hả”. Sau sửa, API local trả `smalltalk`; không còn ép vào thông báo
  ngoài phạm vi. Đây tiếp tục là ví dụ dev đã quan sát.
- Khi provider hosted thực sự được cấu hình, lượt hội thoại được nhận diện
  đi qua prompt riêng để mô hình soạn phản hồi ngắn. Không gửi căn cứ hoặc
  tình tiết vụ việc qua nhánh đó; câu hỏi pháp lý vẫn đi qua retrieval/guard.
  Check format nhánh hội thoại không phải xác minh ngữ nghĩa pháp lý. Chưa có
  hội thoại dài tổng quát hay năng lực hiểu mọi cách nói.
- Khi API lỗi hoặc output hội thoại có format không phù hợp, dùng phản hồi
  local và có metadata/thông báo fallback. Không gọi fallback là Qwen thành công.
- Adapter Qwen từ chối `finish_reason=length` và content null/không phải chuỗi,
  thay vì chấp nhận câu bị cắt như câu hoàn chỉnh. Đã kiểm tra bằng mock.
- Full suite cuối: **352 passed, 1 warning**, gồm wrapper chạy **14 Node tests**.
  V2 dev chạy lại ở `runs/system_behavior_v2_dialogue_ui_dev_20261118.json`
  giữ nguyên Hit@1 39/50, Hit@k 46/50, marker phủ mọi Điều kỳ vọng 35/50,
  broad route match 10/10; không phải đánh giá độc lập hoặc tăng chất lượng pháp lý.
- Đã tạo `.env` cục bộ từ template và xác nhận được gitignore. Tại thời điểm
  kiểm tra key Qwen chưa có, provider vẫn `none`: chưa bật/gọi live Qwen.
  Người dùng đang được hướng dẫn lấy key; không lưu key trong báo cáo hoặc log.

Các mốc và ví dụ ở phần tiếp theo thuộc vòng sửa trước trong cùng ngày.

## Phản hồi đã tái hiện

Người dùng thử giao diện và gửi ảnh. API đang chạy tái hiện được:

| Câu hỏi | Trước sửa | Sau sửa, kiểm tra qua API và trình duyệt |
|---|---|---|
| “sao bạn trả lời thô quá v” | `out_of_scope`, nhắc lại phạm vi đất đai | Nhận phản hồi về giọng điệu, không truy hồi luật |
| “mình không” | `out_of_scope` | Phản hồi từ chối; khi đang làm rõ vụ việc thì vẫn giữ luồng bổ sung |
| “hmm, đất đai là gì” | Trích Điều 12, 223 và các đoạn khác | Giải thích nghĩa thông thường ngắn, không gắn citation pháp lý |
| “mình chỉ hỏi đất đai là gì thôi mà” | Lại trích sở hữu/thống kê đất đai | Nhận câu hỏi khái niệm đầy đủ trong lượt hiện tại |
| “sổ đỏ là gì” | Trích các Điều 134/135 về giấy chứng nhận | Trả nguyên khoản định nghĩa Giấy chứng nhận ở Điều 3 khoản 21 |

Không coi những ví dụ đã quan sát này là tập kiểm định độc lập.

## Nguyên nhân và thay đổi

`ExtractiveProvider` bỏ qua ý câu hỏi khi soạn output, trả ba khối đầu của
retrieval. Nhánh hội thoại cũ chỉ nhận vài câu chào nguyên dạng. Prompt cố định
không thể làm provider local tự sinh lời giải thích.

- Thêm classifier hội thoại cho một số lượt chào/giới thiệu/cảm ơn/từ chối/góp ý.
  Câu có nội dung pháp lý vẫn đi qua pipeline pháp luật và input guard.
- Giữ context làm rõ qua lượt góp ý, không thêm lời góp ý thành tình tiết vụ việc.
  Không có history server hoặc khả năng nhớ toàn bộ hội thoại.
- Nhận yêu cầu định nghĩa bằng các mẫu có giới hạn; chỉ khớp thuật ngữ chính xác
  với các khoản trong phần giải thích từ ngữ của source chunks đã load/validate.
  Không đổi dense ranking, FAISS, embedding, corpus hoặc ngưỡng 0,55.
- Phần định nghĩa trong answer bỏ header và số thứ tự khoản, giữ toàn bộ nội
  dung khoản. Citation giữ nguyên full quote và hash; guard recompute renderer
  để từ chối nội dung thêm/sửa hoặc nguồn không phải khoản định nghĩa.
- Riêng “đất đai” có giải thích nghĩa thông thường biên soạn sẵn. Khi người dùng
  hỏi định nghĩa theo luật, không dùng Điều 12 về sở hữu làm định nghĩa.
- Prompt hosted yêu cầu trả lời trực tiếp và chọn cấu trúc theo câu hỏi, thay vì
  áp một mẫu cho mọi câu. Chưa có live hosted run để xác nhận hiệu quả thay đổi này.

## Xác minh

- `python -m pytest -q`: **307 passed, 1 warning**. Warning deprecation
  Starlette TestClient/HTTPX. Wrapper pytest chạy 12 Node tests, có kiểm tra
  giữ context qua phản hồi hội thoại.
- Runtime `/api/health` sẵn sàng; `/` trả giao diện Minh Long; kiểm tra POST
  `/api/chat` và submit trên trình duyệt với các ví dụ ở bảng trên.
- Smoke API: `data/evaluation/runs/chat_answer_focus_smoke_20261118.json`;
  ảnh giao diện: `data/evaluation/runs/chat_basic_fix_20261118.jpg`.
- V2 dev cuối: `data/evaluation/runs/system_behavior_v2_concepts_dev_20261118_final.json`.
  Kết quả: 50/50 answer có status success, Hit@1 39/50, Hit@k 46/50,
  marker phủ mọi Điều trong nhãn 35/50, broad refusal route match 10/10,
  MRR schema 2 là 0,845. Giữ nguyên so với vòng 17/11; không tuyên bố ranking
  hay độ đúng pháp lý cải thiện.
- Một lượt đo bị validator hủy do source còn đang thay đổi, không ghi report.
  Lượt tiếp theo bắt lỗi phân loại câu hỏi “các nguyên tắc…” thành định nghĩa:
  Hit@1 38/50, Hit@k 45/50. Đã sửa ranh giới và giữ riêng artifact lượt đó ở
  `system_behavior_v2_concepts_dev_20261118.json`; không thay file cũ bằng kết quả mới.
  Source ổn định trong lượt cuối; provenance ghi working tree dirty và không
  dùng `--require-clean`. Không gọi đây là clean-checkout run.

Các file trong `runs/` là output cục bộ, không được commit. V1/V2 vẫn là dev
đã quan sát, nhãn AI chưa được người độc lập duyệt.

## Hạn chế còn lại

Đây là cải thiện các ranh giới chức năng đã phát hiện, không phải thay engine
local bằng mô hình hội thoại. Một câu diễn đạt mới vẫn có thể vượt ra ngoài
rule. Câu pháp lý ngoài nhánh định nghĩa vẫn nhận các đoạn trích nguyên văn;
câu nhiều điều kiện chưa có lời tổng hợp linh hoạt. Thuật ngữ chưa khớp nguồn
có thể nhận thông báo chưa tìm thấy định nghĩa. Chưa chấm mức hữu ích, độ đúng
pháp lý, hiệu lực nguồn hoặc sự hài lòng người dùng độc lập. Qwen/Gemini vẫn
chưa live test; guard hosted chỉ kiểm tra cấu trúc/integrity.
