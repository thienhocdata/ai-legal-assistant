# Minh Long — AI Legal Assistant

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

## Cài đặt

Yêu cầu Python 3.11+ trên Windows/Linux/macOS.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

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
