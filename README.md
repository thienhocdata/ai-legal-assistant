# Minh Long — AI Legal Assistant

[Báo cáo kỹ thuật: thay đổi so với baseline và sản phẩm hiện tại](docs/BAO_CAO_TONG_QUAN_DU_AN_AI_LUAT.md).

Vòng sửa chat 17/11/2026: nối tối đa 3 lượt làm rõ bằng context trong bộ nhớ
tab, hỗ trợ một số cụm tiếng Việt không dấu, giữ nguyên quote, chống gửi chồng,
probe retrieval khi startup và giữ answer khi log I/O lỗi. Local kiểm tra trích
xuất khớp nguyên văn; hosted chưa được xác minh semantic support.

Trợ lý tra cứu pháp luật đất đai Việt Nam theo kiến trúc RAG, ưu tiên căn cứ
pháp luật và trích dẫn Điều–Khoản–Điểm. Phiên bản hiện tại tập trung Luật Đất
đai Việt Nam. Corpus production hiện là Văn bản hợp nhất 133/VBHN-VPQH và sản
phẩm phục vụ demo, nghiên cứu và đánh giá retrieval.

## Khả năng hiện tại

- Tải và quản lý inventory nguồn văn bản.
- Trích xuất ba PDF, chuẩn hóa nhiễu và phân tích Chương/Mục/Điều/Khoản/Điểm.
- So sánh Character Chunker với Legal-aware Chunker.
- Embedding bằng `intfloat/multilingual-e5-small` và FAISS `IndexFlatIP`.
- Dense retrieval và hybrid retrieval có tăng trọng số tiêu đề pháp lý.
- Query rewriting, nhận diện ý định và clarification.
- Citation Engine, Gemini/Qwen provider và chế độ trích xuất local không cần API key.
- Guardrails cho prompt injection, bằng chứng yếu và citation không hợp lệ.
- FastAPI, giao diện chat responsive và JSONL logging.
- Bộ 30 câu ground truth cùng Hit@k, Recall@k và MRR.

Kết quả hybrid retrieval v1: Hit@1 `96,7%`, Recall@3 `100%`, Recall@5 `100%`,
MRR `0,978`. Đây là baseline kỹ thuật trên 30 câu hỏi, chưa phải đánh giá pháp lý
bởi chuyên gia.

Vòng sửa ngày 16/11/2026: routing tách dữ kiện thiếu/nguồn thiếu, extractive trả
tối đa 3 block căn cứ, evaluator schema 2 có cohort và khoảng Wilson. V1/V2 hiện
là dev đã quan sát; xem `docs/evaluation/DATASET_ROLES.md`. Trên V2 dev sau sửa:
Hit@1 39/50, Hit@k 46/50, broad refusal-route match 10/10 (8 làm rõ, 2 thiếu
nguồn). Nhãn AI chưa được người duyệt; số này chưa chứng minh hiệu quả trên câu mới.

## Cài đặt

Yêu cầu Python 3.11+ trên Windows/Linux/macOS.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Ứng dụng tự nạp `.env` cục bộ nhưng không ghi đè biến môi trường đã được đặt
trong tiến trình. `.env` nằm trong `.gitignore`; không gửi hoặc commit file này.

Mặc định `LLM_PROVIDER=none`, hệ thống chạy local và trả đoạn căn cứ gần nhất.
Để dùng Gemini, đặt:

```text
LLM_PROVIDER=gemini
GEMINI_API_KEY=<your-key>
GEMINI_MODEL=gemini-3.5-flash
```

Không commit `.env` hoặc API key vào Git.

Để dùng Qwen qua API tương thích OpenAI của Alibaba Cloud Model Studio:

```text
LLM_PROVIDER=qwen
QWEN_API_KEY=<your-key>
QWEN_MODEL=qwen-plus
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

Endpoint workspace-specific được khuyến nghị khi tài khoản Model Studio cung
cấp. Hosted provider có timeout, giới hạn output và một lần retry cho timeout,
HTTP 429 hoặc lỗi 5xx; lỗi dự kiến sẽ fallback về extractive.

## Chạy ứng dụng

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Mở `http://127.0.0.1:8000`. API docs ở `http://127.0.0.1:8000/docs`.

## Tái tạo Knowledge Base

Chạy nhanh đến bước chunk:

```powershell
.\.venv\Scripts\python.exe scripts\run_pipeline.py --skip-embeddings
```

Chạy đầy đủ PDF → FAISS:

```powershell
.\.venv\Scripts\python.exe scripts\run_pipeline.py
```

Lần đầu embedding cần tải model từ Hugging Face và có thể mất vài phút trên CPU.

## Kiểm thử và đánh giá

```powershell
.\.venv\Scripts\python.exe -m pytest -q
$env:HF_HUB_OFFLINE='1'
.\.venv\Scripts\python.exe scripts\evaluate_retrieval.py --mode hybrid --output data\evaluation\retrieval_eval_hybrid_v1.json
.\.venv\Scripts\python.exe scripts\calibrate_evidence_threshold.py
```

Dataset retrieval: `data/evaluation/test_questions_v1.json`. Bộ câu âm tại
`data/evaluation/evidence_negative_queries_v1.json` chỉ phục vụ diagnostic.
Calibration chọn và chấm ngưỡng trên cùng dữ liệu nên không phải held-out
validation và không được dùng như bằng chứng pháp lý.

Bộ candidate v2 tại `data/evaluation/candidate_questions_v2_blind.json` được
tạo sau baseline `73d3a14` rồi khóa bằng manifest SHA-256. Bộ này có 60 câu
tổng hợp, toàn bộ nhãn đang chờ người rà soát và không phải independent/expert
held-out evaluation. Kết quả baseline extractive trước vòng sửa là: answer success
`98%`, expected-article Hit@1 `76%`, Hit@k `90%`, MRR `0,825`, refusal
correctness `30%` và grounded behavior `68,33%`. Hit@k không được diễn giải
thành độ đúng của câu trả lời. Không dùng kết quả này để chỉnh rule rồi chấm lại
trên cùng phiên bản như một phép đo độc lập. Artifact baseline gốc giữ nguyên;
vòng sửa hiện tại chuyển V2 thành dev theo `docs/evaluation/DATASET_ROLES.md`.

```powershell
.\.venv\Scripts\python.exe scripts\validate_candidate_questions_v2_blind.py
.\.venv\Scripts\python.exe scripts\evaluate_system_behavior.py `
  --questions data\evaluation\candidate_questions_v2_blind.json `
  --manifest data\evaluation\candidate_questions_v2_blind_manifest.json `
  --output data\evaluation\runs\system_behavior_v2_recheck.json `
  --dataset-role development_observed --allow-code-drift --require-clean
.\.venv\Scripts\python.exe scripts\compare_answer_providers.py `
  --questions data\evaluation\candidate_questions_v2_blind.json `
  --providers extractive
```

So sánh Gemini/Qwen chỉ có ý nghĩa runtime khi cấu hình key cục bộ; độ đúng
pháp lý vẫn cần human review. Output so sánh nằm trong
`data/evaluation/runs/` và không được commit.

`--require-clean` yêu cầu source/artifact đã commit và không thay đổi trong lúc
đo. Kết quả gốc và sau sửa lưu ở path riêng trong `data/evaluation/`. BM25/RRF
và article diversity chỉ là thí nghiệm; hybrid mặc định giữ nguyên vì các thử
nghiệm có giảm điểm hoặc mất nội dung khoản. Vòng routing trước đạt 116 passed;
pytest cache đã chuyển vào runtime dir. Vòng sửa chat hiện đạt 171 passed
(bao gồm wrapper chạy 11 Node tests). Cần Node.js để chạy các test JS; nếu thiếu
Node, pytest báo skip phần đó chứ không tính là đã xác minh UI.

`GET /api/health` chỉ trả `ready` sau startup local-retrieval probe thành công;
trong lúc nạp trả `warming_up`, thất bại trả `failed` hoặc `degraded`. Health
không gọi hosted API và không xác nhận chất lượng pháp lý. UI polling có giới
hạn, timeout phía trình duyệt 90 giây không bảo đảm hủy computation phía server.

`POST /api/chat` vẫn nhận `question` như trước, thêm tùy chọn
`clarification_context: {question, answers}` từ `continuation_context` của
response trước. Mỗi chuỗi tối đa 2000 ký tự, tối đa 3 câu bổ sung, tổng 6000 ký
tự. Không lưu history trên server hoặc localStorage. Dùng nút gợi ý hoặc tiền
tố `Câu hỏi mới:` để bắt đầu chủ đề khác.

## Cấu trúc chính

```text
app/
  agent/             Query Understanding + Clarification
  citation/          Citation Engine
  guardrails/        Input, evidence, output gates
  kb/                Parser, normalizer, chunker, embedding
  llm_provider/      Extractive + Gemini + OpenAI-compatible/Qwen provider
  rag/               FAISS Vector Store + Retriever
  services/          End-to-end Legal Assistant orchestration
  static/            Web chat
data/
  raw/               Văn bản nguồn
  processed/         Text, legal tree, chunks, embeddings
  vector_db/         FAISS index và metadata
  evaluation/        Ground truth và báo cáo đo lường
scripts/             Pipeline, build, search, evaluation
tests/               Unit/integration tests
```

## Giới hạn sử dụng

Sản phẩm không thay thế luật sư hoặc cơ quan nhà nước. Trước khi áp dụng cần
kiểm tra tình trạng hiệu lực văn bản, văn bản sửa đổi và tình tiết cụ thể. Kho
dữ liệu hiện chưa bao phủ toàn bộ pháp luật đất đai Việt Nam.
