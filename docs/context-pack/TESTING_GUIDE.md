# Hướng dẫn kiểm thử

## Bộ test mặc định

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Baseline sau promotion ngày 08/08/2026: 38 test đạt. Sau quality hardening ngày
15/11/2026: 54 test đạt. Ngày 16/11/2026, bộ test đầy đủ đạt 70 test. Pytest
vẫn cảnh báo không ghi được `.pytest_cache`; đây không phải test failure.

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

## Đánh giá V2 hậu baseline

Bộ `candidate_questions_v2_blind.json` gồm 60 câu ứng viên do AI sinh và đang
chờ người duyệt: 50 câu kỳ vọng trả lời, 10 câu kỳ vọng từ chối/làm rõ. Manifest
khóa dataset ghi baseline commit
`73d3a141e51c7348763ead7379bf56bf36b54586` và SHA-256
`fc892269eae03256ce8a2808c444c89a98af7ac3a16d62a97fabb452e8bef363` trước
khi chạy evaluator.

Lần chạy `extractive_offline` đạt answer success `98%` (49/50),
expected-article Hit@1 `76%` (38/50), Hit@k `90%` (45/50), MRR `0,825`, refusal
correctness `30%` (3/10) và grounded behavior `68,33%` (41/60). Hit@k chỉ cho
biết Điều kỳ vọng xuất hiện trong danh sách citation; vì extractive dùng evidence
`[1]`, grounded behavior yêu cầu Hit@1. Không điều chỉnh rule retrieval/query
sau khi xem kết quả này; sửa nhãn phải tạo phiên bản dataset và manifest mới.

Đây không phải đánh giá độc lập, không phải expert-held-out và không xác nhận độ
đúng pháp lý. Xem giao thức, provenance và giới hạn diễn giải tại
`docs/evaluation/EVALUATION_V2_2026-11-16.md`.

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_system_behavior.py `
  --questions data\evaluation\candidate_questions_v2_blind.json `
  --manifest data\evaluation\candidate_questions_v2_blind_manifest.json `
  --output data\evaluation\runs\system_behavior_v2_recheck.json
```

Evaluator kiểm tra SHA/path với manifest và mặc định không ghi đè output.

## Evidence calibration diagnostic

```powershell
.\.venv\Scripts\python.exe scripts\calibrate_evidence_threshold.py
```

Báo cáo sinh tại `data/evaluation/evidence_calibration_v1.json`. Đây là
in-sample diagnostic, không phải held-out validation; không tự động thay đổi
`MINIMUM_DENSE_SCORE`. Xem cách diễn giải và giới hạn tại
`docs/evaluation/QUALITY_HARDENING_2026-11-15.md`.
