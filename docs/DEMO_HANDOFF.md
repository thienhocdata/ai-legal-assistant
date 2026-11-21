# Bàn giao bản demo AI Luật

Phạm vi: ứng dụng tra cứu đất đai phục vụ demo/nghiên cứu, dữ liệu production
VBHN 133/VBHN-VPQH. Đây là hướng dẫn chạy và ghi nhận nghiệm thu; không phải
chứng nhận chất lượng pháp lý hoặc biên bản nghiệm thu đã được ký.

## 1. Chạy từ checkout mới trên Windows

Thực hiện tại thư mục repository:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
.\.venv\Scripts\python.exe scripts\check_demo_readiness.py
```

`check_demo_readiness.py` chỉ đọc local: kiểm tra module được cài, file cần
thiết, chunk validator, hash nguồn, shape/ID/vector/manifest và cấu hình.
Script không in key hoặc endpoint, không sửa `.env`, không tạo lại artifact,
không tải model và không gọi Qwen/Gemini/OpenRouter. Module được tìm thấy chưa chứng minh
binary import/model/runtime đều hoạt động.

Để kiểm tra truy hồi local bằng model **đã có trong cache**:

```powershell
.\.venv\Scripts\python.exe scripts\check_demo_readiness.py --probe-model
```

Probe buộc chế độ offline trong lúc chạy và khôi phục biến môi trường sau đó.
Nếu máy mới chưa có cache E5 thì probe sẽ thất bại. Khi có Internet, lần khởi
động ứng dụng bình thường có thể tải model; chờ `/api/health` sẵn sàng rồi mới
chạy probe offline. Không bật `HF_HUB_OFFLINE=1` trước lần tải model đầu tiên.

Chạy web:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Mở `http://127.0.0.1:8000/`. Health ở `/api/health`; chat dùng **POST**
`/api/chat`. Mở `/api/chat` trực tiếp trên thanh địa chỉ sẽ là GET và nhận 405.
Giao diện chỉ có khung chat và nguồn thu gọn, không có metric/sidebar.

## 2. Bật hosted provider sau khi có credential

Người dùng nhập key vào `.env` **trên máy**, không gửi key qua chat, báo cáo
hoặc Git. Mặc định vẫn là `LLM_PROVIDER=none`, chạy trích xuất local.

### 2.1. OpenRouter với ERNIE miễn phí

```text
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=<key-cục-bộ>
OPENROUTER_MODEL=baidu/ernie-5.5-flash-preview:free
LLM_MAX_RETRIES=0
LLM_MAX_OUTPUT_TOKENS=8192
```

8192 là trần token output gồm phần suy luận và câu trả lời, không phải mục tiêu
độ dài. Endpoint ERNIE hiện yêu cầu suy luận; đặt `reasoning.enabled=false`
nhận HTTP400, nên adapter giữ mặc định của model. Thay giới hạn 800 token nếu
còn trong `.env` cũ. Lượt thử ở mức 800 rơi về local với
`ProviderResponseError`; chưa ghi nhận finish reason để kết luận nguyên nhân
chính xác. Lần chẩn đoán ở mức 4096 dùng 4051 completion token, nên tăng ngân
sách cho cả suy luận và câu trả lời.

Base URL được cố định trong adapter: `https://openrouter.ai/api/v1`. Adapter
chỉ chấp nhận model `:free` hoặc `openrouter/free`; request giới hạn giá prompt,
completion và request bằng 0 qua `provider.max_price`, không khai báo model
dự phòng có phí. Mỗi máy/lượt chạy vẫn cần kiểm tra phản hồi thực tế.

Tài khoản chưa mua credit hiện có giới hạn 50 lượt gọi API/ngày, dùng chung
toàn tài khoản. Một lượt chat pháp lý thường gọi hai lần: định tuyến rồi sinh
câu trả lời; 50 lượt API không tương đương 50 câu chat. Model miễn phí còn có
giới hạn tải/khả dụng từ provider. Tham khảo [giới hạn OpenRouter](https://openrouter.ai/docs/api_reference/limits)
và [trang model ERNIE](https://openrouter.ai/baidu/ernie-5.5-flash-preview:free).

Lần thử trên máy ngày 18/11/2026 với câu hỏi tự soạn “Điều kiện để người sử
dụng đất chuyển nhượng quyền sử dụng đất là gì?” đã trả HTTP200,
`status=success`, `provider=openrouter`, model
`baidu/ernie-5.5-flash-preview:free`, không fallback, `usage.cost=0`; thời gian
khoảng 17,9 giây gồm định tuyến và sinh câu trả lời. Có marker `[1]`, `[2]`.
Artifact local: `data/evaluation/runs/openrouter_ernie_web_verified_20261118.json`.
Đây chỉ là smoke test chức năng, không phải kiểm định pháp lý độc lập:
`answer_validation.code=citation_structure_only`,
`semantic_support_verified=false`. Full suite sau thay đổi đạt 457 passed và
một warning deprecation có sẵn; không dùng số test phần mềm làm độ đúng luật.

### 2.2. Qwen khi tài khoản có quyền truy cập

Nhánh Qwen vẫn được hỗ trợ. Lần gọi cục bộ trước khi tích hợp OpenRouter nhận
HTTP403 `AccessDenied.Unpurchased`; chưa có câu trả lời Qwen native thành công.
Các biến cấu hình:

```text
LLM_PROVIDER=qwen
QWEN_API_KEY=<key-cục-bộ>
QWEN_MODEL=<model-được-tài-khoản-cho-phép>
QWEN_BASE_URL=<OpenAI-compatible-base-url-của-key>
```

Key và endpoint phải thuộc cùng khu vực/workspace. Base URL tương thích của
adapter có hậu tố `/compatible-mode/v1`; không dán cả `/chat/completions` vì
adapter tự thêm phần này. Dùng địa chỉ được trang cấp key/tài liệu chính thức
cung cấp, không đoán workspace ID. Hướng dẫn nhà cung cấp:
[lấy API key](https://www.alibabacloud.com/help/en/model-studio/get-api-key),
[base URL](https://www.alibabacloud.com/help/en/model-studio/base-url).

Khởi động lại server sau khi đổi `.env`; service được cache trong tiến trình.
Biến môi trường đã đặt trong tiến trình được ưu tiên hơn file `.env`.

Khi kiểm tra live, dùng câu pháp lý có căn cứ trong kho. Một lời chào hoặc câu
định nghĩa có thể đi qua nhánh local, nên không chứng minh đã gọi API.

```powershell
$demoQuestion = @{ question = 'Điều kiện chuyển nhượng quyền sử dụng đất là gì?' } | ConvertTo-Json
$demoReply = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/chat' -Method Post -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($demoQuestion))
$demoReply | Select-Object status,provider,model,generation_fallback_reason
```

Với OpenRouter, cần `provider=openrouter`, `model` đúng mô hình thực tế và không
có `generation_fallback_reason` để ghi nhận mô hình đã trả lời lượt này. Với
Qwen, kiểm tra tương tự bằng `provider=qwen`. HTTP 200 hoặc `status=success` riêng lẻ chưa đủ: lỗi API có thể
fallback về extractive. `/api/health` chỉ probe truy hồi local. Đọc câu trả
lời và đối chiếu nguồn trước khi ghi nhận chất lượng nội dung.

## 3. Nghiệm thu tình huống có người đọc

Mẫu ghi nhận nằm tại `docs/evaluation/HUMAN_DEMO_REVIEW_PENDING.csv`.
20 dòng đều có trạng thái **PENDING**; các nhóm tình huống là gợi ý do AI
chuẩn bị. Chưa có câu hỏi độc lập, kết quả chạy, nhãn đúng/sai hay chuyên gia
duyệt được điền sẵn.

Sao chép mẫu vào `data/evaluation/runs/` (đã gitignore) để điền kết quả local;
giữ file mẫu trong `docs/` rỗng. Không commit câu hỏi cá nhân, hồ sơ hoặc
thông tin người thử/người duyệt chưa được phép công bố.

Người thử tự viết câu hỏi, ẩn thông tin cá nhân, rồi ghi:

- Câu hỏi và các lượt trước cần thiết để hiểu tình huống.
- Phiên bản source/commit và chế độ provider thực sự trả lời. Nếu working tree
  còn sửa chưa commit, ghi rõ trạng thái đó và lưu fingerprint/snapshot source;
  không chỉ ghi HEAD cũ rồi coi đó là phiên bản đã chạy.
- Phản hồi thực tế, đường dẫn ảnh/output local, lỗi có thể tái hiện.
- Nguồn/Điều/Khoản người đọc đã đối chiếu.
- Mức đúng trọng tâm, dễ hiểu, đủ căn cứ; điểm chưa chắc chắn.
- Người đọc và chuyên môn thực tế. Chỉ gọi là chuyên gia pháp lý nếu đúng.

Nhóm gợi ý gồm hội thoại tự nhiên, câu hỏi khái niệm, hỏi trực tiếp, diễn đạt
đời thường/không dấu, nhiều điều kiện, bổ sung tình tiết, thiếu nguồn và đổi
chủ đề. Tách kiểm tra cơ chế chức năng khỏi đánh giá đúng/sai pháp lý.

Không coi 20 ví dụ này là V3 độc lập hoặc thống kê đại diện nếu câu hỏi đã
được xem để sửa hệ thống. Nếu dùng để tune, gắn nhãn dev; bộ đánh giá độc lập
cần người khác chuẩn bị và giữ tách biệt theo `evaluation/DATASET_ROLES.md`.

## 4. Những đầu vào còn chờ trước khi viết kết quả thực tập

| Đầu vào | Trạng thái tại lần lập hướng dẫn | Cách chốt |
|---|---|---|
| OpenRouter/ERNIE live answer trong ứng dụng | Đã xác nhận native answer cho một câu hỏi điều kiện chuyển nhượng ngày 18/11/2026, không fallback, API báo cost 0 | Kết nối hoạt động ở lượt thử; chất lượng nội dung vẫn cần người đối chiếu nguồn |
| Key/endpoint Qwen và live answer | Đã cấu hình và gọi thật; HTTP403 AccessDenied.Unpurchased, chưa có answer native | Chủ tài khoản kiểm tra đăng ký/kích hoạt/quyền dùng model; sau đó gọi lại và xem provider/fallback |
| Review khoảng 20 tình huống | Chưa có người duyệt | Điền mẫu bằng câu hỏi/kết quả/nhận xét thực tế |
| Hiệu lực và tính đầy đủ pháp luật | Chưa xác minh đầy đủ | Giữ giới hạn phạm vi, nguồn và phiên bản |
| Mẫu báo cáo của trường | Chưa cung cấp | Người dùng gửi đường dẫn mẫu |
| Trường/ngành, họ tên–MSSV, kỳ thực tập, GVHD/người hướng dẫn | Chưa cung cấp đủ | Người dùng xác nhận; không tự điền |
| Yêu cầu, trao đổi và đánh giá thực tế của doanh nghiệp | Repo không chứng minh đầy đủ | Bổ sung từ trải nghiệm/tài liệu thật của người dùng |

## 5. Cách mô tả dự án trong báo cáo

Tên phù hợp: **Xây dựng ứng dụng hỗ trợ tra cứu pháp luật đất đai Việt Nam
bằng kỹ thuật RAG**. Đã dùng embedding model có sẵn để lập chỉ mục; chưa có
bằng chứng train/fine-tune Qwen. Không mô tả phát triển phần mềm, tune rule
hoặc tạo vector là huấn luyện mô hình ngôn ngữ.

Số test, retrieval metric và kết quả demo phải đi kèm thời điểm, dataset và
điều kiện chạy. Không chuyển số khớp Điều/marker trên dev thành phần trăm
trả lời đúng pháp luật. Không bịa vai trò nhóm, người duyệt hoặc xác nhận của
Minh Long từ lịch sử Git.
