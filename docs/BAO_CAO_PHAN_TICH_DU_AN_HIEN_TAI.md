# BÁO CÁO PHÂN TÍCH HIỆN TRẠNG DỰ ÁN AI LEGAL ASSISTANT CỦA CÔNG TY MINH LONG

> Tài liệu nền phục vụ xây dựng đồ án môn **Kỹ năng làm việc tại doanh nghiệp**
>
> Thời điểm khảo sát ban đầu: **24/10/2026**
>
> Cập nhật quality hardening: **15/11/2026**
>
> Repository khảo sát: `AI - Agent pháp luật`
>
> Nhánh baseline: `main`; nhánh hardening: `codex/quality-hardening`
>
> Remote được cấu hình: `https://github.com/thienhocdata/ai-legal-assistant.git`

## 1. Mục đích và phạm vi báo cáo

Báo cáo này tổng hợp hiện trạng dự án từ các nguồn có thể kiểm tra trực tiếp:

1. source code trong `app/` và `scripts/`;
2. test trong `tests/` và kết quả chạy test tại thời điểm khảo sát;
3. artifact, manifest và bộ đánh giá trong `data/`;
4. tài liệu đang được repository đánh dấu là còn hiệu lực;
5. lịch sử Git;
6. lịch sử task Codex liên quan trực tiếp có thể truy cập.

Tài liệu không xem README hoặc báo cáo phát triển cũ là bằng chứng duy nhất. Khi tài liệu mâu thuẫn với source, test hoặc artifact, báo cáo ưu tiên source, test và artifact theo quy tắc tại `AGENTS.md` và `docs/INDEX.md`.

### 1.1. Quy ước mức độ xác minh

| Nhãn | Ý nghĩa |
|---|---|
| **Đã xác minh** | Có bằng chứng trực tiếp trong source, test, artifact/manifest hoặc lịch sử Git. |
| **Suy luận có cơ sở** | Suy ra hợp lý từ nhiều bằng chứng kỹ thuật, nhưng không có biên bản/quyết định chính thức xác nhận. |
| **Chưa thể xác minh** | Chỉ xuất hiện trong mô tả, định hướng hoặc lịch sử trao đổi; chưa có artifact phù hợp để khẳng định đã hoàn thành. |

## 2. Tóm tắt điều hành

**Đã xác minh:** đây là dự án AI Legal Assistant của **công ty Minh Long**, tập trung hỗ trợ tra cứu pháp luật đất đai Việt Nam theo kiến trúc Retrieval-Augmented Generation (RAG). Hệ thống tiếp nhận câu hỏi tiếng Việt, phân tích và viết lại truy vấn, truy hồi các đoạn luật liên quan, tạo trích dẫn Điều–Khoản–Điểm, kiểm tra đầu vào/bằng chứng/đầu ra bằng guardrails, rồi trả lời bằng chế độ trích xuất local, Gemini hoặc Qwen nếu được cấu hình. Qwen mới được xác minh bằng mock HTTP, chưa có live test vì repository không chứa API key.

Tên **“Minh Luật”** từng xuất hiện trong `README.md` và `app/static/` là nhãn cũ, không phải tên công ty. Ngày 15/11/2026, README và giao diện chính đã được đồng bộ thành **Minh Long**; bộ prototype riêng vẫn chưa được tích hợp.

Sản phẩm đang ở mức **demo/nghiên cứu**, không phải dịch vụ tư vấn pháp lý chuyên nghiệp và không phải kho pháp luật đầy đủ. Corpus production mặc định là Văn bản hợp nhất số 133/VBHN-VPQH. Artifact hiện có 260 Điều, 441 legal chunks, embedding kích thước `441 × 384` và FAISS `IndexFlatIP` với 441 vector.

Baseline ngày 24/10/2026 đạt **38/38 test**. Sau quality hardening ngày 15/11/2026, bộ test chạy thực tế đạt **54/54 test**, vẫn có cảnh báo quyền ghi `.pytest_cache` nhưng không có test thất bại. Bộ đánh giá hybrid production trên 30 câu hỏi đạt Hit@1 `0,9667`, Recall@3 `1,0`, Recall@5 `1,0` và MRR `0,9778`. Các số này chỉ phản ánh baseline retrieval trên tập nhỏ, chưa chứng minh độ chính xác pháp lý tổng quát.

Các hạn chế chính là corpus còn hẹp, Luật 43/2024/QH15 chưa được ingest, metadata hiệu lực của corpus hợp nhất chưa hoàn chỉnh, bộ ground truth mới có 30 câu và chưa có bằng chứng được chuyên gia pháp lý duyệt, còn thiếu kiểm soát production như xác thực, rate limiting, CORS, retention/redaction log và triển khai vận hành chính thức.

## 3. Mục tiêu và phạm vi sản phẩm

### 3.0. Nhận diện dự án

- **Doanh nghiệp/chủ thể:** Công ty Minh Long — được người phụ trách dự án xác nhận trực tiếp và phù hợp với bộ prototype UI mới.
- **Tên mô tả kỹ thuật:** AI Legal Assistant / trợ lý pháp luật đất đai.
- **Nhãn “Minh Luật”:** nhận diện cũ, đã được đổi thành Minh Long trong README và giao diện chính ngày 15/11/2026.
- **Tên sản phẩm thương mại chính thức:** chưa thấy tài liệu định danh riêng được phê duyệt trong repository; do đó báo cáo không tự đặt thêm tên sản phẩm.

### 3.1. Mục tiêu đã được chứng minh

Source và tài liệu hiện hành cùng cho thấy hệ thống hướng tới các mục tiêu sau:

- hỗ trợ tra cứu pháp luật đất đai Việt Nam bằng ngôn ngữ tự nhiên;
- ưu tiên truy hồi căn cứ trước khi sinh câu trả lời;
- giữ được cấu trúc pháp lý Chương–Mục–Điều–Khoản–Điểm trong quá trình xử lý;
- đưa ra trích dẫn có thể truy ngược về document và vị trí pháp lý;
- từ chối hoặc yêu cầu làm rõ khi câu hỏi ngoài phạm vi, thiếu dữ kiện hoặc bằng chứng yếu;
- cho phép chạy local không cần API key, đồng thời hỗ trợ provider Gemini và Qwen tùy chọn;
- đo lường retrieval bằng dataset và metric có thể tái tạo;
- duy trì provenance của nguồn và tính nhất quán giữa chunk, embedding, metadata và vector index.

### 3.2. Đối tượng và tình huống sử dụng

**Suy luận có cơ sở:** giao diện, câu hỏi gợi ý và tập đánh giá cho thấy đối tượng trực tiếp là người cần tìm hiểu các quy định phổ biến về chuyển nhượng, thu hồi, bồi thường, cấp Giấy chứng nhận, tách/hợp thửa và tranh chấp đất đai. Repository chưa có tài liệu nghiên cứu người dùng hoặc yêu cầu nghiệp vụ được phê duyệt để xác định chính xác persona, tổ chức sử dụng hay quy mô triển khai.

### 3.3. Ranh giới sản phẩm

Các giới hạn được ghi rõ trong README, system prompt và tài liệu bảo mật:

- không thay thế luật sư hoặc cơ quan nhà nước;
- không tự chứng minh hiệu lực của quy định chỉ từ metadata hiện tại;
- không suy đoán tình tiết vụ việc khi thiếu dữ kiện;
- không coi citation kỹ thuật là bằng chứng rằng văn bản vẫn còn hiệu lực;
- chưa bao phủ toàn bộ pháp luật đất đai Việt Nam;
- chưa đủ điều kiện triển khai công khai như một dịch vụ production.

## 4. Chức năng hiện có

| Nhóm chức năng | Mô tả hiện trạng | Bằng chứng | Mức xác minh |
|---|---|---|---|
| Quản lý nguồn | Inventory, metadata, tải nguồn, retry, hash và atomic write | `app/kb/downloader/`, `data/metadata/source_inventory.csv` | Đã xác minh |
| Trích xuất văn bản | Đọc PDF; corpus VBHN production dùng ba phần Công báo Word chính thức đã chuyển đổi sang DOCX có provenance | `app/kb/parser/`, metadata VBHN 133 | Đã xác minh |
| Chuẩn hóa | Loại nhiễu, sửa dòng bị ngắt, tạo normalizer report | `app/kb/normalizer/`, artifact report | Đã xác minh |
| Phân tích cấu trúc luật | Tách Chương, Mục, Điều, Khoản, Điểm | `app/kb/legal_parser/` và regression tests | Đã xác minh |
| Chunking | Có character chunker để làm baseline và legal-aware chunker ưu tiên ranh giới pháp lý | `app/kb/baseline_chunker/`, `app/kb/chunker/` | Đã xác minh |
| Validation | Kiểm tra chunk rỗng, ID trùng, độ dài và metadata | `app/kb/chunk_validator.py`, test | Đã xác minh |
| Embedding | `intfloat/multilingual-e5-small`, chuẩn hóa L2, 384 chiều | embedding source và manifest | Đã xác minh |
| Vector search | FAISS `IndexFlatIP`, kiểm tra dimension/count/hash | `app/rag/vector_store.py`, manifest | Đã xác minh |
| Retrieval | Dense retrieval và hybrid retrieval có lexical/legal-title boost | `app/rag/retriever.py` | Đã xác minh |
| Hiểu truy vấn | Nhận diện intent, tham chiếu Điều/Khoản và viết lại bằng synonym | `app/agent/query_understanding.py` | Đã xác minh |
| Làm rõ | Phát hiện câu hỏi ngoài phạm vi hoặc thiếu ngữ cảnh và sinh câu hỏi làm rõ | `app/agent/clarification.py` | Đã xác minh |
| Citation | Tạo danh sách căn cứ và context đánh số `[n]` | `app/citation/engine.py` | Đã xác minh |
| Sinh câu trả lời | Provider trích xuất local mặc định; Gemini/Qwen tùy chọn | `app/llm_provider/` | Đã xác minh bằng source/test; Qwen chưa live test |
| Guardrails | Chặn prompt injection, bằng chứng yếu và citation đầu ra không hợp lệ; fallback local nếu hosted output không đạt | `app/guardrails/engine.py`, `app/services/legal_assistant.py` | Đã xác minh |
| API | `GET /api/health`, `POST /api/chat`, Swagger tại `/docs` | `app/main.py`, `tests/test_api.py` | Đã xác minh |
| Web UI | Chat responsive bằng HTML/CSS/JavaScript, health status, câu hỏi gợi ý và hiển thị citation | `app/static/` | Đã xác minh |
| Logging | Ghi event kỹ thuật dạng JSONL, không ghi nguyên câu hỏi trong payload orchestration hiện tại | `app/observability/event_logger.py`, service | Đã xác minh |
| Evaluation | Hit@k, Recall@k, MRR trên 30 câu ground truth | `app/evaluation/`, `data/evaluation/` | Đã xác minh |

## 5. Công nghệ sử dụng

### 5.1. Ngôn ngữ và framework

- **Python 3.11+**: backend, pipeline dữ liệu, retrieval, evaluation và test.
- **FastAPI**: API và phục vụ static UI.
- **Uvicorn**: ASGI server khi chạy local.
- **Pydantic 2**: schema và validation dữ liệu.
- **HTML, CSS, JavaScript thuần**: giao diện hiện đang được phục vụ từ `app/static/`.

### 5.2. Xử lý tài liệu và dữ liệu

- **PyMuPDF**: đọc PDF;
- **python-docx**: đọc nguồn DOCX chuyển đổi từ Công báo Word;
- **NumPy**: lưu và kiểm tra embedding;
- **SHA-256**: truy vết phiên bản nguồn/chunk và kiểm tra tính nhất quán artifact.

### 5.3. AI và retrieval

- **Sentence Transformers**;
- model **`intfloat/multilingual-e5-small`**;
- **PyTorch**;
- **FAISS CPU**, index `IndexFlatIP`;
- **Google Gen AI SDK** cho Gemini và **HTTPX/OpenAI-compatible API** cho Qwen tùy chọn;
- extractive provider local làm chế độ mặc định/fallback.

### 5.4. Kiểm thử và quản lý mã nguồn

- **pytest** cho unit/integration tests;
- **Git** và remote GitHub;
- repository chưa có `pyproject.toml`, lockfile hay cấu hình CI được tìm thấy trong phạm vi khảo sát.

## 6. Kiến trúc hệ thống

### 6.1. Kiến trúc tổng thể

```text
Nguồn chính thức + inventory/metadata
        │
        ▼
Downloader → PDF/DOCX parser → Normalizer → Legal structure parser
        │
        ▼
Character chunker (baseline) / Legal-aware chunker
        │
        ▼
Chunk validator → E5 embeddings → FAISS IndexFlatIP
        │
        ▼
FastAPI /api/chat
        │
        ▼
Input guardrail → Query analysis/rewrite → Clarification
        │
        ▼
Hybrid retriever → Citation engine → Evidence guardrail
        │
        ▼
Extractive local, Gemini hoặc Qwen → Output citation guardrail
        │
        ▼
JSON response + disclaimer + JSONL event log
```

### 6.2. Các lớp chính

1. **Acquisition và provenance**: quản lý URL, file nguồn, hash và metadata.
2. **Knowledge-base construction**: parse, normalize, legal parse, chunk và validate.
3. **Representation và index**: embedding E5 và FAISS.
4. **Question understanding**: phân tích intent, synonym, tham chiếu pháp lý và yêu cầu làm rõ.
5. **Retrieval và evidence**: dense/hybrid search, title boost và citation.
6. **Answer orchestration**: điều phối guardrails, provider, fallback và response.
7. **Delivery**: FastAPI, static web chat và health endpoint.
8. **Quality/observability**: test, evaluation artifact và JSONL event log.

### 6.3. Ranh giới tin cậy

Source và tài liệu thể hiện năm lớp kiểm soát đáng chú ý:

- file nguồn có provenance và hash;
- cấu trúc luật/chunk phải vượt validator;
- chunk, embedding metadata và FAISS phải đồng nhất count/dimension/hash;
- provider chỉ nhận context đã truy hồi;
- đầu ra phải có citation hợp lệ, nếu không hosted output bị thay bằng extractive fallback hoặc bị từ chối.

Guardrails chỉ giảm rủi ro, không phải sandbox và không chứng minh tính đúng pháp lý.

## 7. Dữ liệu và artifact hiện tại

### 7.1. Corpus production

Corpus mặc định là **Văn bản hợp nhất 133/VBHN-VPQH ngày 03/09/2025**. Metadata ghi nguồn từ Cổng Thông tin điện tử Chính phủ và Công báo Chính phủ; raw source gồm PDF, ba file `.doc` chính thức và ba file `.docx` dẫn xuất có quan hệ `derived_from`.

Kết quả kiểm tra artifact tại thời điểm khảo sát:

| Thuộc tính | Giá trị |
|---|---:|
| Document ID | `vbhn_133_2025_luat_dat_dai` |
| Số Điều khác nhau | 260 |
| Legal chunks | 441 |
| Độ dài chunk tối đa | 5.000 ký tự |
| Embedding model | `intfloat/multilingual-e5-small` |
| Kích thước embedding | 384 |
| Số embedding/vector | 441 |
| Chuẩn hóa embedding | L2 normalized |
| FAISS index | `IndexFlatIP` |

### 7.2. Các nguồn khác

- Luật Đất đai 31/2024/QH15: ba PDF đã tải và giữ để truy vết; không còn là index production mặc định.
- Luật 43/2024/QH15: đã có URL và metadata; chưa tải file, chưa chunk/embed/index.
- Thủ tục đăng ký đất đai: metadata dự kiến nhưng chưa có URL định danh ổn định; chưa ingest.

### 7.3. Điểm cần thận trọng

Metadata của VBHN 133 để trống `current_effective_date` và gắn `legal_status: reference`. Vì vậy không được mô tả corpus này là bằng chứng hoàn chỉnh về hiệu lực hiện hành của từng quy định.

## 8. Các giai đoạn phát triển có bằng chứng

Timeline dưới đây dựa trên lịch sử Git hiện có, không dựa vào hồi tưởng.

| Mốc | Commit/bằng chứng | Nội dung có thể xác minh | Kết quả |
|---|---|---|---|
| 06/07/2026 | `9f725ac` | Khởi tạo project tối thiểu: `.env.example`, `.gitignore`, README, `app/main.py`, requirements | Có repository và skeleton ban đầu |
| 06/07/2026 | `e3d56e5` | Tạo khung thư mục app, data, docs, scripts, tests và notebooks | Có cấu trúc phân lớp ban đầu, phần lớn là `.gitkeep` |
| 14/07/2026 | `868ad8d` | Thêm MVP RAG gần như đầy đủ: pipeline, parser, chunker, embedding, FAISS, retrieval, query understanding, citation, guardrails, provider, API, UI, evaluation, test và corpus Luật 31/2024/QH15 | Hình thành baseline chạy được end-to-end |
| 08/08/2026 | `2a46fad` | Thêm thử nghiệm corpus hợp nhất 133, provenance, document audit/context pack, experimental pipeline, corpus comparison và test liên quan | Có luồng thử nghiệm tách khỏi production và quality gate |
| 08/08/2026 | `7242e7a` | Promote VBHN 133 vào production, cập nhật chunks/embeddings/FAISS, report hybrid, metadata và promotion script | Corpus production chuyển sang VBHN 133 |
| 08/08/2026 | `47eae78` | Chuẩn hóa lại text corpus hợp nhất và cập nhật manifest/hash | Artifact được đồng bộ sau normalization |
| 18/08/2026 | `ui-explorations/` và lịch sử task Codex | Tạo nhiều prototype HTML và ảnh desktop/mobile, sửa lỗi font/overflow responsive | Có bộ khám phá UI riêng, nhưng chưa áp dụng vào `app/static/` và chưa commit |

### 8.1. Điều không thể suy ra từ timeline

- Không thể xác định số giờ công, sprint, cuộc họp hay quy trình Scrum.
- Không thể xác định ai đảm nhận vai trò PM, BA, AI engineer, backend, frontend hoặc QA.
- Không có issue tracker, pull request hoặc review record trong repository để chứng minh quy trình phối hợp nhóm.
- Git chỉ hiển thị một tác giả trong sáu commit hiện có; điều này không chứng minh toàn bộ công việc do một người duy nhất thực hiện, nhưng cũng không cho phép tự tạo phân công nhóm.

## 9. Khó khăn đã gặp, cách xử lý và kết quả

### 9.1. PDF VBHN có trang scan và chú thích gây nhiễu

- **Khó khăn — đã xác minh:** tài liệu ghi PDF 133/VBHN-VPQH có trang 218 là ảnh scan và chú thích hợp nhất gây nhiễu parser.
- **Cách xử lý — đã xác minh:** pipeline production sử dụng ba phần Công báo Word chính thức; các file DOCX chuyển đổi được lưu cùng provenance về file `.doc` nguồn.
- **Kết quả — đã xác minh:** quality gate đạt 260 Điều, 441 chunks, không có tiêu đề đáng ngờ và không còn boilerplate Công báo theo tài liệu/manifest hiện hành.
- **Hạn chế còn lại:** nhánh PDF vẫn không được dùng để build index; đây là workaround nguồn, chưa phải parser PDF xử lý được mọi trang scan.

### 9.2. Cần giữ cấu trúc pháp lý khi chunking

- **Khó khăn — suy luận từ source/test:** character chunking dễ cắt qua ranh giới Điều–Khoản–Điểm, làm yếu citation và retrieval.
- **Cách xử lý — đã xác minh:** duy trì character chunker làm baseline, xây legal-aware chunker ưu tiên cấu trúc pháp lý và validator chung.
- **Kết quả — đã xác minh:** artifact production có 441 legal chunks bao phủ 260 Điều, mỗi chunk mang metadata cấu trúc và giới hạn tối đa 5.000 ký tự.

### 9.3. Đồng bộ nhiều artifact của vector database

- **Khó khăn — suy luận từ source/test:** embedding, metadata, chunk source và FAISS có thể lệch phiên bản/count/dimension.
- **Cách xử lý — đã xác minh:** manifest lưu model, dimension, count, normalization và source hash; retriever/vector store kiểm tra hash, ID, dimension và count khi load; có test integrity.
- **Kết quả — đã xác minh:** hiện có 441 chunks, 441 embedding và 441 FAISS vectors, dimension 384.
- **Cập nhật 15/11/2026:** `vector_store_manifest.json` đã dùng đường dẫn tương đối; portability thực tế trên Linux/CI vẫn cần kiểm tra.

### 9.4. Tránh câu trả lời không có căn cứ hoặc citation sai

- **Khó khăn — đã xác minh qua thiết kế source:** LLM có thể trả lời khi bằng chứng yếu hoặc tạo citation không hợp lệ.
- **Cách xử lý — đã xác minh:** input/evidence/output guardrails; system prompt yêu cầu chỉ dùng context; kiểm tra chỉ số citation; fallback từ hosted provider về extractive nếu lỗi dự kiến hoặc output không đạt.
- **Kết quả — đã xác minh:** các nhánh blocked, clarification, insufficient evidence, success và generation rejected tồn tại và có test.
- **Hạn chế còn lại:** chưa có bộ đo citation correctness/completeness hoặc đánh giá chuyên gia về chất lượng trả lời.

### 9.5. Chuyển corpus mà không ghi đè production thiếu kiểm soát

- **Khó khăn — đã xác minh qua Git và scripts:** cần thử corpus VBHN mới mà không phá artifact production hiện hành.
- **Cách xử lý — đã xác minh:** artifact thử nghiệm nằm trong `data/experiments/`; script experimental từ chối đường dẫn production; promotion yêu cầu quality gate, `--confirm`, validation và tạo backup.
- **Kết quả — đã xác minh:** VBHN 133 được thử nghiệm, so sánh và promote bằng commit riêng; production manifests cùng trỏ về document mới.

### 9.6. Giao diện thử nghiệm bị giống nhau, lỗi font và tràn ngang mobile

- **Khó khăn — đã xác minh từ lịch sử task:** các prototype UI đầu tiên bị phản hồi là quá giống nhau; font/fallback tiếng Việt và grid mobile có lỗi hiển thị/tràn ngang.
- **Cách xử lý — đã xác minh từ lịch sử task và file:** bỏ bộ prototype cũ, tạo bốn hướng có ngôn ngữ sản phẩm khác nhau, tránh serif/fallback gây lỗi, sửa responsive grid và tạo ảnh kiểm tra desktop/mobile.
- **Kết quả — đã xác minh một phần:** `ui-explorations/minh-long-legal-v2/` có các prototype và ảnh chụp; chúng chưa được tích hợp vào `app/static/` và chưa nằm trong lịch sử Git.

### 9.7. Cảnh báo pytest cache

- **Khó khăn — đã xác minh tại thời điểm khảo sát:** pytest không ghi được `.pytest_cache` do permission.
- **Cách xử lý hiện tại:** cảnh báo được phân loại là vấn đề môi trường/cache, không phải test failure.
- **Kết quả:** 54 test đạt sau quality hardening. Lỗi permission cache chưa được sửa dứt điểm.

## 10. Kết quả kiểm thử và đánh giá

### 10.1. Test tự động

Lệnh được chạy lại ngày 15/11/2026:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Kết quả:

```text
54 passed, 1 warning in 2.63s
```

Phạm vi test bao gồm API, downloader, parser, normalizer, legal structure, character/legal chunks, validator, embedding, vector DB, retriever, query understanding, citation/provider, guardrails/service, evaluator, experimental corpus, corpus comparison, metadata integrity và promotion.

### 10.2. Retrieval evaluation

Artifact `data/evaluation/retrieval_eval_hybrid_vbhn_133.json` ghi:

| Metric | Kết quả |
|---|---:|
| Số câu hỏi | 30 |
| Top-k | 5 |
| Hit@1 | 0,9667 |
| Recall@3 | 1,0000 |
| Recall@5 | 1,0000 |
| MRR | 0,9778 |

**Giới hạn diễn giải:** dataset nhỏ, tập trung một corpus lõi và chưa có bằng chứng được chuyên gia pháp lý duyệt. Vì vậy các metric này chỉ chứng minh hiệu năng retrieval trên tập thử nghiệm, không chứng minh hệ thống trả lời đúng pháp luật trong mọi tình huống.

### 10.3. Bất nhất đã phát hiện

UI từng hiển thị `Recall@5 93,3%` và `MRR 0,846`. Ngày 15/11/2026, giao diện đã được đồng bộ thành `100%` và `0,978`, kèm ngày/tập đánh giá và cảnh báo rằng đây không phải độ chính xác pháp lý tổng quát.

Nhận diện README và giao diện chính đã được đồng bộ thành **Minh Long** ngày 15/11/2026. Các tài liệu lịch sử vẫn có thể nhắc “Minh Luật” khi mô tả trạng thái cũ.

## 11. Trạng thái hiện tại

### 11.1. Những phần đã hoàn thành ở mức demo/nghiên cứu

- pipeline từ nguồn đến FAISS chạy theo cấu trúc module rõ ràng;
- corpus production có provenance, manifest và quality gate;
- retrieval dense/hybrid và query processing đã được triển khai;
- citation, local/Gemini/Qwen provider và guardrails đã được nối end-to-end; Qwen mới có mock test, chưa live test;
- API, web chat và health endpoint đã có;
- bộ test hiện tại đạt 54/54;
- có dataset và report đánh giá retrieval;
- có cơ chế thử nghiệm/promotion corpus tách khỏi production;
- có tài liệu context pack cập nhật ngày 08/08/2026.

### 11.2. Phần chưa hoàn chỉnh hoặc chưa đủ bằng chứng

- corpus chỉ có một văn bản lõi đang được index;
- Luật 43/2024/QH15 và thủ tục hành chính chưa được ingest;
- metadata hiệu lực và quan hệ pháp lý chưa đủ để khẳng định tính áp dụng hiện hành;
- chưa có đánh giá pháp lý bởi chuyên gia;
- chưa đo citation correctness, answer correctness, completeness, refusal quality;
- chưa có authentication/authorization, rate limit, CORS policy production;
- chưa có retention/redaction policy hoàn chỉnh cho event log;
- chưa thấy CI/CD, container/deployment config, monitoring production hoặc backup vận hành trong repository;
- UI exploration mới chưa tích hợp vào web chính;
- chưa có bằng chứng triển khai production công khai ổn định.
- bộ prototype UI riêng chưa được chọn và tích hợp vào web chính.

### 11.3. Working tree tại thời điểm khảo sát

`git status --short` cho thấy duy nhất `ui-explorations/` là untracked. Báo cáo không sửa hoặc commit thư mục này. Các artifact khác được dùng để đánh giá nằm trong trạng thái Git hiện hành, nhưng thời gian sửa file trên filesystem không tự động được xem là một giai đoạn đã commit.

## 12. Ưu tiên phát triển tiếp theo

Các ưu tiên sau được rút từ `docs/context-pack/CURRENT_PRIORITIES.md` và đối chiếu với source:

1. mở rộng ground truth ngoài 30 câu, đặc biệt các Điều 157, 190, 216 và 255;
2. thêm nhãn Điều–Khoản–Điểm và quy trình chuyên gia pháp lý duyệt;
3. đo citation correctness/completeness, chất lượng từ chối và chất lượng câu trả lời;
4. tải và ingest bản gốc Luật 43/2024/QH15 để hoàn thiện provenance quan hệ sửa đổi;
5. tự động đồng bộ processing/index status vào document metadata;
6. hoàn thiện bảo mật, quyền riêng tư và vận hành trước khi triển khai ngoài local;
7. đồng bộ metric mới lên UI;
8. chỉ tích hợp prototype UI sau khi chọn hướng và kiểm thử accessibility/responsive;
9. xử lý portability của manifest và hợp nhất requirements trùng lặp khi được phê duyệt.

## 13. Phân biệt bằng chứng với nội dung chưa xác minh

### 13.1. Có đủ bằng chứng để sử dụng trong đồ án

- mục tiêu xây trợ lý tra cứu đất đai dựa trên RAG;
- kiến trúc và luồng dữ liệu nêu trong báo cáo;
- danh sách công nghệ từ requirements và import/source;
- sáu commit và các mốc ngày trong Git;
- 260 Điều, 441 chunks, 441 × 384 embedding, 441 FAISS vectors;
- kết quả 54 test đạt tại lần chạy ngày 15/11/2026;
- các metric retrieval trong artifact;
- vấn đề PDF scan/chú thích và cách dùng Công báo Word;
- cơ chế experimental corpus và promotion;
- các hạn chế về phạm vi nguồn, security/privacy và evaluation;
- việc tồn tại prototype UI chưa tích hợp.

### 13.2. Chưa thể khẳng định nếu không có tài liệu bổ sung

- dự án được thực hiện bởi bao nhiêu thành viên;
- tên, vai trò, nhiệm vụ hoặc mức đóng góp của từng người;
- có áp dụng Scrum/Kanban hay không;
- số sprint, daily meeting, retrospective hoặc biên bản họp;
- thời lượng thực hiện từng module;
- yêu cầu chính thức từ doanh nghiệp/khách hàng;
- số người dùng thật, mức độ hài lòng hoặc hiệu quả kinh doanh;
- hệ thống đã được luật sư/chuyên gia pháp lý nghiệm thu;
- hệ thống đã sẵn sàng production hoặc đáp ứng chuẩn bảo mật cụ thể;
- toàn bộ nội dung lịch sử trao đổi Codex là quyết định đã được phê duyệt;
- các định hướng sản phẩm sâu hơn như “legal decision-support platform” hoặc mô hình dữ liệu trung tâm “Legal Case” ở task/repository khác đã được hiện thực hóa trong codebase RAG này.

## 14. Gợi ý sử dụng báo cáo cho môn Kỹ năng làm việc tại doanh nghiệp

Báo cáo này có thể làm nền cho các phần:

- giới thiệu bài toán và phạm vi sản phẩm;
- phân tích yêu cầu và ràng buộc chất lượng;
- mô tả quy trình kỹ thuật theo giai đoạn;
- quản lý rủi ro dữ liệu, chất lượng và bảo mật;
- kiểm thử, đánh giá và quản lý thay đổi;
- bài học từ việc giữ provenance, tách experimental/production và dùng quality gate.

Nếu đồ án yêu cầu mô tả làm việc nhóm, chỉ nên bổ sung thông tin từ nguồn thật như danh sách thành viên, nhật ký phân công, biên bản họp, issue/PR hoặc xác nhận của giảng viên/doanh nghiệp. Không nên biến các module kỹ thuật thành vai trò thành viên giả định.

## 15. Danh mục bằng chứng chính

### Source và test

- `app/main.py`
- `app/services/legal_assistant.py`
- `app/agent/`
- `app/citation/`
- `app/guardrails/`
- `app/kb/`
- `app/llm_provider/`
- `app/rag/`
- `app/evaluation/`
- `app/observability/`
- `app/static/`
- `scripts/`
- `tests/`

### Tài liệu hiện hành

- `AGENTS.md`
- `README.md`
- `docs/INDEX.md`
- `docs/architecture/system.md`
- `docs/context-pack/PROJECT_OVERVIEW.md`
- `docs/context-pack/ARCHITECTURE_MAP.md`
- `docs/context-pack/DATA_AND_LEGAL_SOURCES.md`
- `docs/context-pack/KNOWN_ISSUES.md`
- `docs/context-pack/TESTING_GUIDE.md`
- `docs/context-pack/SECURITY_AND_PRIVACY.md`

### Artifact và manifest

- `data/metadata/source_inventory.csv`
- `data/metadata/documents/vbhn_133_2025_luat_dat_dai.json`
- `data/metadata/documents/luat_43_2024.json`
- `data/processed/legal_chunks.json`
- `data/processed/legal_embeddings_manifest.json`
- `data/processed/promotion_manifest.json`
- `data/vector_db/vector_store_manifest.json`
- `data/evaluation/test_questions_v1.json`
- `data/evaluation/retrieval_eval_hybrid_vbhn_133.json`

### Lịch sử

- Git log nhánh `main`, các commit: `9f725ac`, `e3d56e5`, `868ad8d`, `2a46fad`, `7242e7a`, `47eae78`.
- Lịch sử task Codex liên quan UI, chỉ dùng để xác nhận quá trình prototype; không dùng thay cho Git khi khẳng định trạng thái release.

---

## Kết luận

Dự án đã đạt một baseline RAG pháp luật có cấu trúc tương đối đầy đủ ở mức demo/nghiên cứu: có provenance nguồn, pipeline xử lý văn bản pháp luật, legal-aware chunking, embedding/vector index, hybrid retrieval, query understanding, citation, guardrails, API/UI, test và evaluation artifact. Điểm mạnh nổi bật là tính truy vết kỹ thuật và việc tách thử nghiệm corpus khỏi production bằng quality gate/promotion.

Tuy nhiên, chất lượng retrieval tốt trên 30 câu không thể thay thế đánh giá pháp lý. Giá trị tiếp theo của dự án phụ thuộc vào mở rộng và quản trị nguồn luật, xác minh hiệu lực/thời điểm/địa phương, đánh giá bởi chuyên gia, đo citation và answer quality, đồng thời hoàn thiện security/privacy/operations. Vì các bằng chứng về tổ chức nhóm không tồn tại trong repository hiện tại, mọi phần đồ án về phân công và phối hợp phải được bổ sung từ hồ sơ thực tế, không được suy diễn từ code hoặc lịch sử task.
