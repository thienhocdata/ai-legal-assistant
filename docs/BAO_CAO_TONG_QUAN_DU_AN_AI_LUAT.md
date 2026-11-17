# BÁO CÁO TỔNG QUAN KỸ THUẬT AI LEGAL ASSISTANT

> Kết quả runtime: 16/11/2026; rà soát cách diễn giải: 17/11/2026
>
> Mốc code mới nhất được đo: `3506bab` (sau `ec2fd78`)
>
> Phạm vi: trợ lý tra cứu pháp luật đất đai Việt Nam phục vụ demo/nghiên cứu

## Tóm tắt

AI Legal Assistant là hệ thống RAG chạy qua FastAPI và giao diện web, nhận câu
hỏi tiếng Việt, tìm đoạn luật liên quan, tạo câu trả lời có citation và có thể
chạy local bằng extractive provider sau khi model/artifact đã có sẵn. Corpus production hiện gồm một
văn bản lõi: VBHN 133/VBHN-VPQH, được tách thành 441 legal chunks và lập chỉ mục
bằng E5 + FAISS.

Ba commit được dùng làm mốc so sánh không đại diện cho ba lần xây lại sản phẩm.
`47eae78` đã là checkpoint end-to-end; `73d3a14` harden provider, guardrail,
routing và quality gates; `255adb7` bổ sung evaluation V2 cùng provenance. Core
chunks, vector index và artifact V1 30 câu không đổi giữa ba mốc, nên báo cáo
không tuyên bố retrieval đã được cải thiện qua chuỗi commit này.

Tại mốc `255adb7`, suite đạt **70 passed**. V2 có 60 câu do AI tạo và đang chờ
người duyệt; extractive offline đạt answer success 98%, Hit@1 76%, Hit@k 90%,
MRR 0,825, refusal correctness 30% và grounded behavior 68,33%. Đây là metric kỹ
thuật trên candidate dataset, không phải bằng chứng về độ đúng pháp lý.

Vòng sửa mới nhất đạt **116 passed**. Từ vòng này V1/V2 là dev đã quan sát.
Kết quả mới, những thay đổi đã giữ và những thử nghiệm bị loại nằm ngay bên
dưới; phần so sánh ba commit cũ vẫn giữ làm lịch sử kỹ thuật.

## Những gì vừa sửa và kết quả hiện tại

### So với bản trước vòng sửa

| Hạng mục | Bản trước | Bản đã sửa |
|---|---|---|
| Baseline | Run gốc ghi worktree dirty | Run lại `2cafc54` từ checkout sạch, số gốc tái lập |
| Audit | Chưa phân tích từng lỗi | Đủ 19 câu riêng biệt; AI audit, chưa có chuyên gia duyệt |
| Missing context/source | Rule corpus-gap gộp rộng | Tách nguồn thiếu và dữ kiện thiếu, câu hỏi làm rõ cụ thể |
| False refusal | Chặn câu hỏi nguyên tắc bảng giá đất cấp tỉnh | Cho phép tra cứu câu hỏi chung đó |
| Refusal dev | 7/10 câu cần không kết luận vẫn trả success | 8 làm rõ + 2 thiếu nguồn trên 10 câu dev |
| Extractive | Chỉ trích `[1]` | Trích tối đa 3 block, tách question/instructions khỏi evidence |
| Metric | Tên success/grounded dễ bị hiểu thành độ đúng | Schema 2: tên status/rank/marker, mẫu số, cohort, Wilson |
| Provenance | Có commit/hash nhưng khó chặn dirty run | `--require-clean`, snapshot trước/sau, hash code/artifact |
| UI | Đặt Recall@5 100% lên đầu | Hiển thị baseline V2 trước sửa và trạng thái nhãn; V1 ghi dev |
| Pytest cache | Không ghi được cache root | Cache nằm trong thư mục runtime đã gitignore |
| Kiểm thử | 70 test | 116 test; thêm API POST và UI contract thực sự được pytest chạy |

Audit chi tiết: `docs/evaluation/V2_FAILURE_AUDIT.md`. 12 câu trượt hạng 1 đã
bao gồm 5 câu trượt top-k; cộng 7 refusal failure là **19**, không phải 24.
Câu V2Q030 có diễn đạt/nhãn mơ hồ; chưa tự sửa nhãn và chưa tạo V2.1.

### So sánh hồi quy trên V2 dev đã quan sát

Baseline clean tại `2cafc54`:
`data/evaluation/system_behavior_v2_clean_baseline.json`.
Run sau sửa tại `3506bab`, có `require_clean_enforced=true` và
`relevant_worktree_dirty=false`:
`data/evaluation/system_behavior_v2_dev_after_fixes.json`.

| Phép đo | Trước sửa — V2 dev đã quan sát | Sau sửa — cùng V2 dev đã dùng chỉnh rule |
|---|---:|---:|
| Status success trên câu kỳ vọng answer | 49/50 (98%) | 50/50 (100%) |
| Expected-article Hit@1 | 38/50 (76%) | 39/50 (78%) |
| Expected-article Hit@k | 45/50 (90%) | 46/50 (92%) |
| Khớp nhóm status không trả lời trên câu refuse | 3/10 (30%) | 10/10 (100%) |

Đây là kiểm tra hồi quy trên dữ liệu đã quan sát; đặc biệt 10 câu refusal đã
được đọc trước khi sửa rule. Bảng không ước lượng hiệu quả trên câu mới.
Proxy gộp `routing_and_top1_article_match_rate` vẫn lưu trong artifact để truy
vết (49/60, 81,67%), nhưng không dùng làm chỉ số chất lượng tổng quát hoặc tiêu
chí chấp nhận sản phẩm.

Hit@1/Hit@k tăng một câu nhờ bỏ chặn nhầm Q037; không có thay đổi index hay
thuật toán hybrid mặc định để nhận công cho mức tăng này. Đối chiếu từng cặp
trước/sau cho thấy Q037 là câu answer duy nhất đổi Hit@1. Đây là sửa được một
false refusal cụ thể; mức tăng 2 điểm phần trăm chưa chứng minh cải thiện
retrieval khái quát. Không suy từ khoảng Wilson rộng rằng lỗi đã sửa chỉ là
nhiễu. 10/10 routing chỉ là
khớp nhãn broad-refusal trên tập đã dùng sửa rule; Wilson 95% vẫn rộng
`72,25%–100%`. Việc dùng lại dev tạo nguy cơ overfit lớn; chưa có dữ liệu chưa
quan sát để xác nhận mức overfit hoặc chất lượng trên câu mới. Khoảng Wilson
không khắc phục việc dùng tập này để chỉnh rule.

Sau sửa còn **11/50 câu trượt hạng 1 và 4/50 trượt top-k**. MRR mới là `0,845`
theo hạng citation thực tế. MRR gốc `0,825` dùng schema bỏ trùng Điều, nên không
ghép hai số thành một mức tăng mà không chấm lại cùng evaluator.

Marker trong câu trả lời trỏ tới ít nhất một Điều kỳ vọng ở 45/50 câu (90%).
Marker trỏ tới toàn bộ các Điều liệt kê trong nhãn ở 35/50 câu (70%). Đây là
khớp marker/nhãn; chưa chấm nội dung, faithfulness hay completeness pháp lý.
15/50 câu chưa phủ mọi nhãn không tự động có nghĩa là 15 câu trả lời thiếu ý:
nhãn có thể bao gồm các Điều thay thế nhau, thiếu nhãn hoặc chưa được duyệt.
Cần tách Điều vắng ngay ở top-k khỏi Điều đã truy hồi nhưng chưa được trích.

Đối chiếu danh sách Điều theo từng câu cho 15 coverage miss:

| Tình trạng thiếu theo nhãn | Số câu (nhóm không trùng nhau) |
|---|---:|
| Chỉ có nhãn thiếu ngay ở top-k | 10 |
| Mọi nhãn đã có trong top-k nhưng answer không trích hết | 4 |
| Vừa có nhãn thiếu ở top-k, vừa có nhãn tìm được nhưng chưa trích | 1 |

Nếu đếm không loại trùng: 11 câu thiếu ít nhất một Điều ở top-k và 5 câu có ít
nhất một Điều tìm thấy nhưng chưa trích; giao nhau 1 câu. Top-k phủ mọi nhãn ở
39/50 câu, còn answer phủ mọi nhãn ở 35/50. Chỉ tăng số block được trích lên
toàn bộ top-5 cũng chỉ có thể giải quyết thêm tối đa 4 câu theo metric này.
Vì vậy cần xử lý cả retrieval lẫn lựa chọn evidence, thay vì quy mọi coverage
miss cho giới hạn 3 block của extractive.

Độ phủ mọi nhãn theo cohort là direct 20/20, paraphrase 12/18 và
multi-condition 3/12. Đây là dấu hiệu ưu tiên đọc lại câu/nhãn và kiểm tra đủ
căn cứ cho nhóm nhiều điều kiện; chưa được gọi là 9/12 câu thiếu ý khi các
nhãn nhiều Điều vẫn chưa được người có chuyên môn rà soát.

### Theo nhóm câu hỏi sau sửa

| Nhóm | Mẫu | Phép đo | Tỷ lệ | Wilson 95% |
|---|---:|---|---:|---:|
| Direct | 20 | Hit@1 | 18/20 = 90% | 69,90%–97,21% |
| Colloquial/paraphrase | 18 | Hit@1 | 11/18 = 61,11% | 38,62%–79,69% |
| Multi-condition | 12 | Hit@1 | 10/12 = 83,33% | 55,20%–95,30% |
| Refusal/clarification | 10 | Broad route match | 10/10 = 100% | 72,25%–100% |

Khoảng Wilson chỉ mô tả bất định lấy mẫu dưới giả định nhị thức; không xử lý
lỗi nhãn AI, các câu phụ thuộc nhau hoặc thiên lệch tạo bộ câu. Nhóm paraphrase
vẫn là vùng retrieval yếu rõ nhất trong tập dev này.

### Rủi ro chuỗi đánh giá khép kín bởi AI

Nhãn V2 do AI tạo; audit 19 lỗi, sửa rule và đánh giá lại cũng được AI hỗ trợ.
Các bước này có thể lặp lại cùng một cách hiểu sai hoặc cùng thiên lệch. Thêm
agent, freeze bằng hash và kiểm thử nhiều lần đều chưa tạo được kiểm chứng bởi
người thật độc lập.

Ưu tiên một người thật đọc khoảng 20 câu có chủ đích, gồm câu đúng/sai, diễn
đạt đời thường, nhiều điều kiện, refusal và nhãn mơ hồ. Ghi câu nào được duyệt,
ai duyệt, lý do đồng ý/bất đồng và căn cứ. Đây là một lớp kiểm tra bên ngoài;
chỉ gọi là legal-expert review nếu người duyệt thực sự có chuyên môn, và chưa
thay thế được đánh giá độc lập trên V3 mới.

### Thử nghiệm xếp hạng đã làm nhưng chưa promote

Artifact: `data/evaluation/retrieval_development_variants_v1.json`, chạy từ
clean checkout `ec2fd78`, có source/config fingerprints. Thí nghiệm bypass
router để tách riêng ranking nên baseline V2 ở đây là 78%/92%.

| Phương án | V1 Hit@1 / Hit@5 | V2 answer Hit@1 / Hit@5 |
|---|---|---|
| Hybrid đang dùng | 96,67% / 100% | 78% / 92% |
| Mỗi Điều giữ chunk tốt nhất | 96,67% / 100% | 78% / 96% |
| Dense + BM25 binary-presence/RRF thử nghiệm | 50% / 76,67% | 62% / 88% |

RRF thử nghiệm giảm điểm nên không đưa vào runtime. Article diversity cải thiện
top-k nhưng ở truy vấn chi tiết Điều 138 có thể giữ chunk giới thiệu và loại
các chunk chứa điều kiện. Vì thế diversity **chỉ opt-in**, mặc định vẫn giữ
nhiều chunk cùng Điều. Điểm article-hit không đủ để duyệt thay đổi làm mất
evidence; đã thêm regression bảo vệ việc này.

### Những việc chưa hoàn thành

- Chưa có human/expert label review, V3 độc lập hoặc live Qwen/Gemini run.
- Chưa sửa hết ranking/paraphrase và chưa kết luận nhãn V2Q030 đúng hay sai.
- Chưa calibrate một ngưỡng margin mới; margin chỉ được ghi để phân tích.
- Chưa ingest thêm văn bản, thay model/index hoặc hoàn thiện public production.
- Hội thoại nhiều lượt, quản lý hiệu lực, bảo mật/operations vẫn theo mục hạn chế.

Giao thức V3 và vai trò dev: `docs/evaluation/DATASET_ROLES.md`. Không tự tạo
candidate bằng AI rồi gọi là bộ do người độc lập viết.

---

## Phần I. Lịch sử ba mốc trước vòng sửa mới

### 1.1. Bảng so sánh

| Thành phần | `47eae78` | `73d3a14` | `255adb7` / mốc lịch sử |
|---|---|---|---|
| Vai trò | Checkpoint sản phẩm end-to-end | Quality hardening | Evaluation và provenance hardening |
| Corpus | VBHN 133, 260 Điều, 441 chunks | Không đổi | Không đổi |
| Embedding/index | 441 × 384, FAISS `IndexFlatIP` | Không đổi | Không đổi |
| V1 retrieval artifact | 30 câu | Blob không đổi | Blob không đổi |
| Provider | Extractive, Gemini | Thêm Qwen/OpenAI-compatible và error policy | Thêm comparison harness |
| Routing/guardrail | Đã có luồng cơ bản | Thêm smalltalk, corpus-gap và fallback rõ nghĩa | Được đo thêm bằng V2 |
| Evaluation | V1 development set | Negative diagnostic và human-review framework | Frozen V2 post-baseline |
| Test suite | 38 test | 54 test | 70 test |
| Hosted-provider quality | Chưa có live comparison | Chưa có | Chưa có |

### 1.2. Mốc `47eae78`: checkpoint end-to-end

Đây không phải thời điểm khởi tạo dự án. Tại mốc này, hệ thống đã có:

- FastAPI, web chat và endpoint `/api/chat`;
- downloader, PDF/DOCX parser, normalizer và legal-aware chunker;
- embedding `intfloat/multilingual-e5-small`;
- FAISS `IndexFlatIP` và hybrid retrieval;
- query analysis, rewrite và clarification;
- citation engine cùng input/evidence/output guardrails;
- extractive provider và Gemini tùy chọn;
- corpus production 260 Điều, 441 chunks;
- V1 retrieval evaluation 30 câu;
- 38 test theo testing artifact của mốc.

Các giới hạn đã tồn tại ở checkpoint:

- V1 là development set nhỏ, không phải held-out benchmark;
- threshold evidence `0,55` chưa có negative-set calibration;
- chưa có live comparison giữa hosted providers;
- fallback chưa phân biệt đầy đủ lỗi provider với lỗi lập trình;
- metadata hiệu lực pháp lý chưa đầy đủ;
- embedding manifest chứa đường dẫn tuyệt đối, làm giảm portability.

### 1.3. Mốc `73d3a14`: quality hardening

Mốc này không thay core retrieval artifacts. Thay đổi tập trung vào độ bền và
khả năng kiểm soát:

1. Thêm Qwen qua OpenAI-compatible API, timeout, output cap và retry giới hạn.
2. Không retry lỗi xác thực; không lưu API key vào source/report.
3. Chuẩn hóa network/timeout/upstream/malformed response thành `ProviderError`.
4. Hosted provider lỗi dự kiến thì fallback về extractive.
5. Lỗi lập trình ngoài provider hierarchy không bị fallback che giấu.
6. Thêm smalltalk route và corpus-gap route.
7. Thêm bộ câu âm và evidence-threshold diagnostic.
8. Thêm `AnswerQualityEvaluator` cho quy trình human review.
9. Đồng bộ cảnh báo giới hạn và citation mở rộng trên UI.

Suite tăng từ 38 lên 54 test. Qwen chỉ được kiểm tra bằng mock HTTP; mốc này
không tạo bằng chứng live về chất lượng Qwen hoặc Gemini.

### 1.4. Mốc `255adb7`: evaluation V2 và provenance

Mốc `255adb7` thêm một candidate dataset hậu baseline và đóng băng bằng manifest:

- 60 câu: 50 `answer`, 10 `refuse`/clarify;
- nhãn `ai_generated_candidate_pending_human_review`;
- baseline commit đầy đủ:
  `73d3a141e51c7348763ead7379bf56bf36b54586`;
- dataset SHA-256:
  `fc892269eae03256ce8a2808c444c89a98af7ac3a16d62a97fabb452e8bef363`;
- provider evaluation hiện có: extractive offline.

Dataset được tạo sau baseline và manifest ghi rằng quá trình sinh không tham
khảo V1, retrieval report, query rules, retriever implementation hoặc test hiện
có. Nhãn Điều được suy ra từ inventory số/tên Điều của corpus. Điều này giảm
nguy cơ trùng trực tiếp với V1, nhưng không biến V2 thành benchmark độc lập hoặc
đã được chuyên gia xác nhận.

Mốc này còn thêm system-behavior evaluator và provider comparison harness. Tới
commit này chưa có thay đổi retrieval/query tuning sau khi xem V2. Suite tăng
lên 70 test; vòng sửa mới sau đó đã chuyển V2 sang vai trò dev như phần đầu.

Artifact V2 ghi baseline `73d3a14`, đồng thời ghi worktree còn dirty và
fingerprint các file thực tế lúc chạy. Vì vậy kết quả này chưa phải một lần đo
từ clean checkout của `255adb7`. Commit hiện hành đã lưu evaluator/config;
chạy lại trên clean checkout sẽ là một artifact mới, giữ artifact gốc để so sánh.

### 1.5. Các bất biến và kết luận hợp lệ

Git/blob comparison cho thấy core chunks, vector index và V1 retrieval blobs
giống nhau tại `47eae78`, `73d3a14` và `255adb7`. Vì vậy:

- có thể kết luận quality controls và evaluation coverage tăng;
- không thể kết luận retrieval model/index tốt hơn qua ba mốc;
- chênh lệch V1/V2 phản ánh hai dataset khác nhau, không phải before/after test;
- không dùng V2 để tune rồi chấm lại V2 như một independent test.

---

## Phần II. Phương pháp xác minh bằng chứng

### 2.1. Thứ tự ưu tiên

Khi tài liệu và trạng thái hiện hành khác nhau, báo cáo ưu tiên:

1. source code và hành vi runtime;
2. output test;
3. artifact, manifest, hash và evaluation report;
4. Git commit/blob history;
5. context-pack còn hiệu lực;
6. README hoặc báo cáo lịch sử.

### 2.2. Mức xác minh

| Mức | Cách dùng trong báo cáo |
|---|---|
| Đã xác minh | Có source, test, artifact, manifest, Git hoặc runtime trực tiếp |
| Giới hạn diễn giải | Metric đúng trong dataset/cấu hình được nêu, không suy rộng |
| Chưa xác minh | Thiếu live run, human review hoặc nguồn phù hợp |

Báo cáo không dùng retrieval metric để khẳng định legal correctness; không dùng
citation kỹ thuật để khẳng định hiệu lực văn bản; không dùng mock provider test
để đánh giá chất lượng mô hình hosted.

---

## Phần III. Tổng quan sản phẩm hiện tại

### 3.1. Mục tiêu và phạm vi

Hệ thống hỗ trợ tra cứu pháp luật đất đai bằng câu hỏi tiếng Việt với các mục
tiêu kỹ thuật:

- retrieval evidence trước khi tạo câu trả lời;
- bảo toàn cấu trúc Chương–Mục–Điều–Khoản–Điểm;
- citation có thể truy ngược về chunk;
- từ chối/giới hạn khi câu hỏi ngoài phạm vi hoặc thiếu nguồn;
- chạy local bằng extractive provider;
- thay provider mà không cần xây lại knowledge base.

Phạm vi hiện có là VBHN 133/VBHN-VPQH và các chủ đề được văn bản này bao phủ.
Hệ thống không phải dịch vụ tư vấn pháp lý, không phải kho pháp luật đầy đủ và
không tự xác nhận hiệu lực của từng quy định.

### 3.2. Chức năng chính

| Lớp | Chức năng đã có |
|---|---|
| Acquisition | Inventory, download/retry, hash, atomic write, provenance |
| Parsing | PDF/DOCX extraction và normalization |
| Legal structure | Chương, Mục, Điều, Khoản, Điểm |
| Validation | ID, metadata, count, dimension và artifact integrity |
| Retrieval | E5 dense search, FAISS, legal-title hybrid boost |
| Query | Intent, synonym rewrite, explicit legal references |
| Routing | Out-of-scope, smalltalk, clarification, corpus-gap |
| Citation | Index `[n]`, Điều–Khoản–Điểm và quote |
| Generation | Extractive, Gemini, Qwen-compatible |
| Guardrail | Prompt injection, evidence threshold, citation validation |
| API/UI | `/`, `/api/health`, `POST /api/chat`, `/docs` |
| Evaluation | V1, threshold diagnostic, V2, provider harness, human-review tool |

### 3.3. Công nghệ

Python 3.11+, FastAPI, Uvicorn, Pydantic, PyMuPDF, python-docx, NumPy, Sentence
Transformers, PyTorch, `multilingual-e5-small`, FAISS CPU, Google Gen AI SDK,
HTTPX/OpenAI-compatible API, HTML/CSS/JavaScript thuần, pytest và Git.

### 3.4. Kiến trúc

```text
Official source + inventory/hash
  → downloader → PDF/DOCX parser → normalizer
  → legal structure → legal-aware chunks → validator
  → E5 embeddings → FAISS IndexFlatIP

POST /api/chat
  → input guardrail → query analysis/rewrite → route/clarify
  → hybrid retrieval → citation context → evidence guardrail
  → extractive / Gemini / Qwen → output citation guardrail
  → JSON response + disclaimer + technical event log
```

### 3.5. Workflow dữ liệu

1. Lưu nguồn chính thức cùng metadata/hash.
2. Trích xuất PDF/DOCX và chuẩn hóa nhiễu.
3. Nhận diện cấu trúc pháp lý.
4. Tạo legal-aware chunks và chạy validator.
5. Encode passage bằng E5, L2-normalize vector.
6. Xây FAISS index và metadata.
7. Đối chiếu count, dimension, model và source hash.
8. Chỉ promote artifact thử nghiệm qua quality gate có xác nhận/backup.

Corpus production dùng ba phần Công báo Word chính thức vì PDF có scan/chú thích
gây nhiễu parser. Kết quả hiện tại:

| Thuộc tính | Giá trị |
|---|---:|
| Document | VBHN 133/VBHN-VPQH, 03/09/2025 |
| Số Điều | 260 |
| Legal chunks | 441 |
| Embeddings | 441 × 384, `float32`, L2 normalized |
| Vector index | 441 vectors, FAISS `IndexFlatIP` |
| Model | `intfloat/multilingual-e5-small` |

### 3.6. Workflow trả lời

1. Validate input và chặn prompt injection rõ ràng.
2. Trả smalltalk tĩnh khi phù hợp.
3. Phân tích intent/scope, rewrite và legal references.
4. Corpus-gap route hoặc clarification nếu thiếu điều kiện/nguồn.
5. Encode query và hybrid-rank chunks.
6. Tạo context có citation rồi kiểm tra evidence.
7. Provider tạo câu trả lời; output guardrail kiểm tra citation index.
8. Lỗi hosted được phân loại hoặc citation không hợp lệ thì fallback extractive.
9. API trả answer, citations, metadata, provider, usage, disclaimer và latency.

---

## Phần IV. Kết quả test và evaluation

### 4.1. Regression suite hiện hành

Lệnh xác minh:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Kết quả chạy ngày 16/11/2026:

```text
116 passed, 1 warning
```

Warning hiện tại là Starlette deprecates cách TestClient dùng HTTPX; không phải
test failure. Lỗi quyền cache cũ đã xử lý bằng cache_dir trong `pytest.ini`.
Test bao phủ pipeline dữ liệu, artifact integrity, retrieval, query,
routing, citation, providers, guardrails, API/UI contracts, V2 freeze/evaluator
và provider-comparison privacy/configuration.

### 4.2. V1: development-set baseline

Artifact `retrieval_eval_hybrid_vbhn_133.json` có 30 câu, `top_k=5`:

| Hit@1 | Recall@3 | Recall@5 | MRR |
|---:|---:|---:|---:|
| 0,9667 | 1,0000 | 1,0000 | 0,9778 |

V1 nhỏ, xuất hiện trong cùng giai đoạn phát triển rule và chưa có expert review.
Git không chứng minh dataset được viết trước tuning. Đây là development metric,
không phải independent hoặc legal-correctness score.

### 4.3. Evidence-threshold diagnostic

Threshold selection so sánh **30 positive** với **15 missing-source**. Có thêm
**15 upstream-scope** để quan sát riêng vì nhóm này phải bị router loại trước,
không tham gia threshold selection.

| Nhóm | Count | Dense min | Median | Max |
|---|---:|---:|---:|---:|
| Positive | 30 | 0,853728 | 0,905956 | 0,929356 |
| Missing-source | 15 | 0,831392 | 0,861451 | 0,888160 |
| Upstream-scope, quan sát riêng | 15 | 0,762238 | 0,808588 | 0,841713 |

Ngưỡng production `0,55` có balanced accuracy `0,5` trên 30 positive + 15
missing-source. Ngưỡng in-sample `0,890138` đạt `0,9` nhưng từ chối nhầm 20%
positive. Vì vậy ngưỡng production không được đổi máy móc từ diagnostic này.

### 4.4. V2: kết quả baseline gốc (lịch sử)

Kết quả extractive offline trên 60 câu:

| Metric | Kết quả | Đếm tương ứng |
|---|---:|---:|
| Status success — key cũ `answer_success_rate` | 98% | 49/50 answer questions |
| Expected-article Hit@1 | 76% | 38/50; 12 miss rank 1 |
| Expected-article Hit@k | 90% | 45/50; 5 miss top-k |
| Article MRR | 0,825 | trên 50 answer questions |
| Broad-refusal route match — key cũ `refusal_correctness_rate` | 30% | 3/10; 7/10 trả success |
| Proxy routing + top1 — key cũ `overall_grounded_behavior_accuracy` | 68,33% | 41/60; phép đo trên dev |

V2 là tín hiệu post-baseline nhưng nhãn vẫn do AI tạo và chờ human review. V1
và V2 là hai dataset khác nhau; không diễn giải chênh lệch Hit@1 như mức giảm
chất lượng tuyệt đối hoặc bằng chứng chắc chắn V1 bị tune theo. Không được tune trực tiếp trên V2 rồi báo lại V2 như test
độc lập. Sửa nhãn phải tạo version/manifest mới.

`answer_success_rate` trong artifact lịch sử chỉ đếm `status=success`.
`overall_grounded_behavior_accuracy` gộp success + expected-article Hit@1 ở
nhóm answer với routing ở nhóm refuse. Schema 2 hiện đã dùng tên tường minh
`answer_status_success_rate` và `routing_and_top1_article_match_rate`. Giữ
nguyên key/artifact cũ để truy vết; cả hai schema chưa chấm độ đúng nội dung.

### 4.5. Provider status

| Provider | Xác minh hiện có | Live quality comparison |
|---|---|---|
| Extractive | Offline V2 và regression tests | Có kết quả V2 ở trên |
| Gemini | Source/integration contract | Chưa có |
| Qwen | Mock HTTP, auth/retry/fallback tests | Chưa có |

Comparison harness có thể đo status, latency, token usage, citation và fallback,
nhưng hiện không có live Qwen/Gemini run. Mock test chỉ chứng minh request/error
contract, không chứng minh faithfulness, completeness hay chất lượng tiếng Việt.

---

## Phần V. Vấn đề, giới hạn và ưu tiên

### 5.1. Vấn đề đã xử lý

| Vấn đề | Xử lý | Kết quả kỹ thuật |
|---|---|---|
| PDF scan/chú thích nhiễu | Dùng ba phần Công báo Word, giữ provenance | 260 Điều, 441 validated chunks |
| Character chunks cắt cấu trúc | Legal-aware chunker | Metadata Điều–Khoản–Điểm |
| Artifact lệch nhau | Hash/count/dimension validation | 441 chunks = embeddings = vectors |
| Thử nghiệm ghi đè production | Experiments, quality gate, promotion/backup | Promotion có kiểm soát |
| Hosted API lỗi | Error hierarchy, retry cap, extractive fallback | Lỗi dự kiến không làm chat sập |
| Metric V1 dễ bị suy rộng | Frozen V2 + manifest/hash | Có post-baseline signal rõ provenance |

### 5.2. Giới hạn còn lại

- Corpus production mới có một văn bản lõi; Luật 43/2024/QH15 mới có metadata,
  chưa ingest cùng nghị định/thông tư/quy định địa phương.
- Metadata hiệu lực, sửa đổi, thay thế và phạm vi áp dụng chưa đầy đủ.
- Embedding manifest vẫn chứa đường dẫn tuyệt đối, chưa portable hoàn toàn.
- V2 chưa được người độc lập/chuyên gia duyệt. Broad-refusal baseline gốc là
  30%; sau sửa đạt 10/10 broad route match trên dev đã quan sát, chưa chứng
  minh khả năng khái quát sang câu mới.
- Chưa có human metrics về citation correctness, faithfulness, completeness.
- Chưa có live Qwen/Gemini comparison, token/cost/latency hosted thực tế.
- Output citation guardrail chưa kiểm tra semantic entailment từng nhận định.
- Health check, auth, rate limit, CORS, retention, monitoring, CI/CD và load test
  chưa đủ cho public production.
- Hội thoại nhiều lượt, case/session state và accessibility còn hạn chế.

### 5.3. Ưu tiên tiếp theo

**P0 — Evaluation độc lập**

1. Nhờ người thật rà soát mẫu khoảng 20 câu có cả đúng/sai, paraphrase,
   multi-condition, refusal và trường hợp nhãn mơ hồ; sau đó mở rộng duyệt 60
   nhãn nếu có điều kiện. Ghi rõ vai trò và chuyên môn thật của người duyệt.
2. Audit kỹ thuật 19 câu đã xong. Việc còn thiếu là người rà soát độc lập kiểm
   tra các nhận định AI trong `V2_FAILURE_AUDIT.md`, không làm lại audit AI rồi
   coi đó là xác nhận bên ngoài.
3. Chỉ sửa nhãn đã có lý do và bằng chứng bằng V2.1 + manifest/hash mới; chưa
   tự động đổi nhãn cho khớp kết quả.
4. Chốt V3 do người độc lập soạn và duyệt, giữ khỏi vòng chỉnh rule, rồi mới
   đo cuối sau khi đóng băng code/config/corpus. Một nhãn được chuyên gia duyệt
   không tự làm tập dev đã quan sát trở thành held-out.

**P0 — Paraphrase và coverage trên dev**

1. Ưu tiên 7/18 câu paraphrase trượt hạng 1, sau khi kiểm tra lại nhãn và cách
   hiểu câu. Thử synonym/rewrite có giới hạn, đo riêng từng thay đổi trên dev.
2. Theo dõi cả Hit@1 và độ phủ nhãn trong căn cứ thực sự được trích; phân loại
   nhãn và nội dung của 15 coverage miss, với phân rã kỹ thuật đã có ở phần
   đầu (10 retrieval-only, 4 selection-only, 1 cả hai). Không dùng any-hit để
   đại diện câu trả lời đủ ý.
3. Giữ baseline và các phương án bị loại; chỉ kết luận khái quát sau V3.

**P0 — Human answer review**

1. Chấm citation correctness, faithfulness, completeness và refusal behavior.
2. Công bố denominator, rubric và label source.
3. Không dùng LLM-as-judge thay thế nhãn người đánh giá.

**P1 — Corpus và provenance**

1. Ingest văn bản gốc và hướng dẫn chính qua quality gate hiện có.
2. Bổ sung `effective_from`, `effective_to`, `status`, `amends`, `replaced_by`,
   `jurisdiction`, `last_verified_at`.
3. Sửa embedding manifest thành path tương đối và thêm portability test.

**P1 — Live provider comparison**

1. Cấu hình secret cục bộ, không commit/log key.
2. Chạy cùng synthetic dataset qua extractive/Gemini/Qwen.
3. Human-review output trước khi kết luận provider nào tốt hơn.

**P2 — Runtime**

- Bổ sung deep health check, auth/rate limit/CORS, log policy, CI/CD, monitoring
  và load testing trước mọi cân nhắc public deployment.

### 5.4. Phạm vi sửa tiếp theo có thể thực hiện

| Hạng mục | Công việc cụ thể | Điều kiện xác nhận hoàn thành |
|---|---|---|
| Clean baseline | Đã chạy sạch baseline và bản sau sửa, lưu artifact riêng | Có commit/config/hash và trạng thái clean |
| Audit lỗi V2 | Đã audit kỹ thuật 19 câu | Nhãn vẫn chờ người có chuyên môn; chưa tự tạo V2.1 |
| Refusal routing | Đã tách nguồn thiếu/dữ kiện thiếu và thêm regression | Dev có 8 clarification + 2 coverage; cần V3 để kiểm tra khái quát |
| Metric | Đã đổi tên status success và proxy rank/status | Chưa có metric độ đúng nội dung do người chấm |
| Phân nhóm và bất định | Đã có cohort và Wilson cho các tỷ lệ | MRR không gắn Wilson; nhãn và mẫu nhỏ còn giới hạn |
| Vai trò dataset | Đã ghi V1/V2 là dev đã quan sát | V3 mới chưa được người độc lập cung cấp |
| UI metric | Đã hiển thị baseline V2 trước sửa và ghi V1 là dev | Có ngày/mẫu số/trạng thái nhãn |

Các phần kỹ thuật trên có thể triển khai và kiểm thử bằng repository. AI có thể
hỗ trợ audit nhãn hoặc tạo candidate mới, nhưng không được tự ghi kết quả đó
thành human/expert review hoặc một V3 do người độc lập viết. Live Qwen/Gemini
cần credential cục bộ hợp lệ và lần gọi thực tế; hiện chưa có kết quả đó.

---

## Phần VI. Bản đồ bằng chứng

| Nhận định | Bằng chứng chính | Giới hạn |
|---|---|---|
| Ba mốc và vai trò | Git log/diff/blob comparison | `47eae78` đã là end-to-end checkpoint |
| Core retrieval artifacts không đổi | Git blob identity ở ba commit | Không tuyên bố retrieval improvement |
| 260 Điều, 441 chunks | processed artifact, manifests | Không tự chứng minh hiệu lực pháp lý |
| 441 × 384 embeddings | embedding manifest | Manifest còn absolute paths |
| FAISS 441 vectors | vector store manifest/index metadata | Chỉ xác minh integrity |
| V1 30 câu và metrics | `retrieval_eval_hybrid_vbhn_133.json` | Development set |
| Calibration | `evidence_calibration_v1.json` | 30 positive + 15 missing-source; scope riêng |
| V2 schema/hash/baseline | V2 dataset và blind manifest | AI-generated, pending review |
| V2 exact metrics | `system_behavior_v2_blind_extractive.json` | Extractive offline, không phải legal accuracy |
| 116 passed hiện tại; 70 tại mốc trước | pytest output ngày 16/11/2026 | Không chứng minh độ đúng pháp lý |
| Qwen contract | provider source và mock tests | Không có live quality result |
| Provider harness | script, docs và tests | Chưa có live Qwen/Gemini comparison |

## Kết luận

Hệ thống hiện là baseline RAG pháp luật có pipeline dữ liệu, artifact integrity,
retrieval, citation, provider fallback và evaluation có provenance ở mức
demo/nghiên cứu. Tiến bộ giữa ba mốc chủ yếu là hardening và đo lường, không
phải cải thiện core retrieval.

Baseline V2 làm lộ 19 lỗi đã được audit. Sau sửa, routing khớp broad-refusal
10/10 trên dev; ranking còn 11/50 miss ở rank 1 và 4/50 miss trong top-k. Các
số sau sửa chỉ đo trên V2 đã quan sát. Việc duyệt nhãn, giải quyết các lỗi còn
lại và kiểm tra bằng V3 độc lập vẫn cần tiếp tục trước kết luận khái quát. Chưa
có cơ sở để tuyên bố độ đúng pháp lý, provider tốt nhất hoặc production-ready.
