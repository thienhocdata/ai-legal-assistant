# Kiến trúc hệ thống

```text
Official Sources
  -> Download Manager + Inventory
  -> PDF Parser
  -> Text Normalizer
  -> Legal Structure Parser
  -> Character / Legal-aware Chunker
  -> Chunk Validator
  -> multilingual-e5-small
  -> FAISS IndexFlatIP
  -> Dense + Legal-title Hybrid Retriever
  -> Query Understanding
  -> Clarification Engine
  -> Citation Engine
  -> Extractive or Gemini Answer Provider
  -> Guardrails
  -> FastAPI + Web UI + Evaluation Logs
```

## Ranh giới tin cậy

1. Dữ liệu nguồn phải có URL, hash, trạng thái tải và metadata hiệu lực.
2. Parser phải giữ đủ 260 Điều và vượt qua regression tests tiêu đề.
3. Chunk không được rỗng, trùng ID hoặc vượt hard limit 5.000 ký tự.
4. Embedding, metadata và FAISS manifest phải có cùng số lượng/dimension.
5. Answering chỉ dùng context đã truy hồi và phải có citation `[n]` hợp lệ.
6. Retrieval score thấp, câu hỏi ngoài phạm vi hoặc prompt injection bị chặn.
7. Log kỹ thuật không lưu API key; dữ liệu cá nhân cần được hạn chế ở production.

## Trạng thái 15 module

| # | Module | Trạng thái |
|---|---|---|
| 01 | Data Acquisition | Có inventory, downloader, retry, hash, atomic write |
| 02 | Source Parser | PDF gốc và Công báo Word của VBHN 133 |
| 03 | Text Normalizer | Noise removal, wrapped-line repair, report |
| 04 | Legal Structure Parser | 16 Chương, 260 Điều, regression title repair |
| 05 | Character Chunker | 618 chunks, baseline |
| 06 | Legal-aware Chunker | 441 chunks, legal boundary first |
| 07 | Chunk Validator | Shared validation gate |
| 08 | Embedding Service | E5-small, 441×384, L2 normalized |
| 09 | Vector Store | FAISS IndexFlatIP |
| 10 | Retriever | Dense + hybrid title boost |
| 11 | Query Understanding | Intent, refs, synonym rewriting |
| 12 | Clarification | Out-of-scope and missing-context questions |
| 13 | Citation & Answering | Citation Engine, local/Gemini providers |
| 14 | Guardrails | Injection, confidence and citation gates |
| 15 | Evaluation & Logging | 30 questions, metrics, JSONL event log |
