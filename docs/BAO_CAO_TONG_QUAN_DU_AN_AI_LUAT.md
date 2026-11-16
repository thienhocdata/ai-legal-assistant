# BÁO CÁO TỔNG QUAN KỸ THUẬT AI LEGAL ASSISTANT

> Trạng thái xác minh: 16/11/2026
>
> Mốc code được phân tích: `255adb7`
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

Hiện tại toàn bộ suite đạt **70 passed**. V2 có 60 câu do AI tạo và đang chờ
người duyệt; extractive offline đạt answer success 98%, Hit@1 76%, Hit@k 90%,
MRR 0,825, refusal correctness 30% và grounded behavior 68,33%. Đây là metric kỹ
thuật trên candidate dataset, không phải bằng chứng về độ đúng pháp lý.

---

## Phần I. So sánh các mốc kỹ thuật

### 1.1. Bảng so sánh

| Thành phần | `47eae78` | `73d3a14` | `255adb7` / hiện tại |
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

Mốc hiện hành thêm một candidate dataset hậu baseline và đóng băng bằng manifest:

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

Mốc này còn thêm system-behavior evaluator và provider comparison harness. Không
có thay đổi retrieval/query tuning sau khi xem V2. Suite tăng lên 70 test.

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
70 passed, 1 warning
```

Warning duy nhất là pytest không ghi được `.pytest_cache`; không phải test
failure. Test bao phủ pipeline dữ liệu, artifact integrity, retrieval, query,
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

### 4.4. V2: frozen post-baseline candidate

Kết quả extractive offline trên 60 câu:

| Metric | Kết quả | Đếm tương ứng |
|---|---:|---:|
| Answer success | 98% | 49/50 answer questions |
| Expected-article Hit@1 | 76% | 38/50; 12 miss rank 1 |
| Expected-article Hit@k | 90% | 45/50; 5 miss top-k |
| Article MRR | 0,825 | trên 50 answer questions |
| Refusal correctness | 30% | 3/10; 7/10 bị trả lời sai hành vi |
| Grounded behavior | 68,33% | 41/60 |

V2 là tín hiệu post-baseline nhưng nhãn vẫn do AI tạo và chờ human review. V1
và V2 là hai dataset khác nhau; không diễn giải chênh lệch Hit@1 như mức giảm
chất lượng tuyệt đối hoặc bằng chứng chắc chắn V1 bị tune theo. Không được tune trực tiếp trên V2 rồi báo lại V2 như test
độc lập. Sửa nhãn phải tạo version/manifest mới.

`Answer success` chỉ đếm `status=success`. `Grounded behavior` là phép đo kỹ
thuật gồm success + expected-article Hit@1 ở nhóm answer và routing ở nhóm
refuse. Cả hai đều chưa chấm độ đúng nội dung. Vòng evaluator tiếp theo nên dùng
tên tường minh hơn và giữ schema/artifact cũ để truy vết.

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
- V2 chưa được người độc lập/chuyên gia duyệt; refusal correctness chỉ 30%.
- Chưa có human metrics về citation correctness, faithfulness, completeness.
- Chưa có live Qwen/Gemini comparison, token/cost/latency hosted thực tế.
- Output citation guardrail chưa kiểm tra semantic entailment từng nhận định.
- Health check, auth, rate limit, CORS, retention, monitoring, CI/CD và load test
  chưa đủ cho public production.
- Hội thoại nhiều lượt, case/session state và accessibility còn hạn chế.

### 5.3. Ưu tiên tiếp theo

**P0 — Evaluation độc lập**

1. Cho người độc lập/chuyên gia duyệt 60 nhãn V2.
2. Sửa nhãn bằng V2.1 + manifest/hash mới, không ghi đè.
3. Audit 19 câu riêng biệt: 12 miss rank1 (trong đó có 5 miss top-k) và 7 refusal
   failures. Đọc câu hỏi, expected article, rewrite và top-k trước khi kết luận
   lỗi retrieval, lỗi rewrite, nhãn sai hoặc nhiều Điều cùng hợp lý.
4. Phát triển fix trên development set riêng.
5. Chấm thay đổi bằng fresh V3 hoặc expert-held-out set.

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

**P2 — Retrieval/runtime**

- Thử dedup/diversification, BM25 + RRF hoặc reranker chỉ sau khi có evaluation
  sạch; đo trên development set rồi xác nhận bằng fresh set.
- Bổ sung deep health check, auth/rate limit/CORS, log policy, CI/CD, monitoring
  và load testing trước mọi cân nhắc public deployment.

### 5.4. Phạm vi sửa tiếp theo có thể thực hiện

| Hạng mục | Công việc cụ thể | Điều kiện xác nhận hoàn thành |
|---|---|---|
| Clean baseline | Chạy lại evaluator từ clean checkout đã commit, lưu artifact riêng | Commit/config/hash có thể đối chiếu, metric tái lập hoặc ghi rõ sai khác |
| Audit lỗi V2 | Phân loại 19 câu, tách clarification/corpus-gap/out-of-scope | Có từng câu, căn cứ và lý do; nhãn chưa có chuyên gia vẫn ghi chờ duyệt |
| Refusal routing | Phân loại nguồn thiếu và dữ kiện thiếu; kiểm thử từng nhánh | Có regression test, đo false refusal trên câu hợp lệ cùng với refusal đúng |
| Metric | Đổi tên status success, phân biệt rank-hit và chất lượng nội dung | Báo cáo không gọi status/citation hit là accuracy câu trả lời |
| Phân nhóm và bất định | Báo cáo direct/paraphrase/multi-condition/refusal; Wilson cho các tỷ lệ | Có tử số/mẫu số và khoảng tin cậy; MRR dùng phương pháp phù hợp riêng |
| Vai trò dataset | V1 là dev; nếu dùng V2 sửa rule thì đánh dấu V2 là dev đã quan sát | Giữ nguyên baseline gốc; có V3 mới trước vòng đo cuối |
| UI metric | Gắn nhãn dev set cho số V1, hiển thị V2 kèm ngày/mẫu số/giới hạn | Không tạo ấn tượng 100% chính xác pháp lý |

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
| 70 passed | pytest output ngày 16/11/2026 | Cache warning không phải failure |
| Qwen contract | provider source và mock tests | Không có live quality result |
| Provider harness | script, docs và tests | Chưa có live Qwen/Gemini comparison |

## Kết luận

Hệ thống hiện là baseline RAG pháp luật có pipeline dữ liệu, artifact integrity,
retrieval, citation, provider fallback và evaluation có provenance ở mức
demo/nghiên cứu. Tiến bộ giữa ba mốc chủ yếu là hardening và đo lường, không
phải cải thiện core retrieval.

V2 làm lộ hai vùng cần ưu tiên: ranking còn 12/50 miss ở rank 1, 5/50 miss trong
top-k và routing chỉ từ chối đúng 3/10 câu. Bước tiếp theo hợp lệ là duyệt nhãn,
phân tích lỗi, phát triển trên tập riêng và xác nhận bằng fresh evaluation. Cho
đến khi có human/expert review và live provider runs, không có cơ sở để tuyên bố
độ đúng pháp lý, provider tốt nhất hoặc mức sẵn sàng production.
