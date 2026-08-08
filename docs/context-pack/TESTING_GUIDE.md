# Hướng dẫn kiểm thử

## Bộ test mặc định

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Baseline sau promotion ngày 08/08/2026: 38 test đạt; pytest cảnh báo không ghi được `.pytest_cache`, không phải test failure.

## Theo loại thay đổi

- Parser/normalizer/chunker: chạy test module, validator chunks và kiểm tra đủ cấu trúc pháp lý.
- Embedding/vector DB: kiểm tra count, dimension, dtype, norm, model và hash/manifest.
- Retriever/query rewriting: chạy retriever/evaluator tests và đánh giá trên ground truth.
- Citation/provider/guardrail: kiểm tra citation index hợp lệ, fallback local và các nhánh bị chặn.
- API/UI: kiểm tra `/api/health`, request hợp lệ/không hợp lệ của `/api/chat` và giao diện thực tế.

## Corpus thử nghiệm

```powershell
.\.venv\Scripts\python.exe scripts\run_experimental_corpus.py
.\.venv\Scripts\python.exe scripts\run_experimental_corpus.py --with-embeddings
```

Script chỉ ghi vào `data/experiments/` và từ chối `data/processed/` hoặc `data/vector_db/`. Chỉ được chuyển sang embeddings khi manifest có `quality_gate.passed: true` và `eligible_for_embeddings: true`.

Promotion production phải chạy validation trước và tự tạo backup cục bộ:

```powershell
.\.venv\Scripts\python.exe scripts\promote_experimental_corpus.py --validate-only
.\.venv\Scripts\python.exe scripts\promote_experimental_corpus.py --confirm
```

## Đánh giá retrieval

```powershell
$env:HF_HUB_OFFLINE='1'
.\.venv\Scripts\python.exe scripts\evaluate_retrieval.py --mode hybrid --output data\evaluation\retrieval_eval_hybrid_v1.json
.\.venv\Scripts\python.exe scripts\evaluate_retrieval.py --mode hybrid --artifact-dir data\experiments\vbhn_133_2025_luat_dat_dai --output data\experiments\vbhn_133_2025_luat_dat_dai\retrieval_eval_hybrid.json
```

Không diễn giải Hit@k, Recall@k hoặc MRR trên 30 câu như độ chính xác pháp lý tổng quát. Mọi tuyên bố chất lượng pháp lý cần tập dữ liệu đại diện và chuyên gia duyệt.

Kết quả production VBHN 133 ngày 08/08/2026 trên 30 câu, hybrid: Hit@1 `0,9667`, Recall@3/5 `1,0`, MRR `0,9778`. API chat thử nghiệm trả về citation `vbhn_133_2025_luat_dat_dai`, Điều 159.
