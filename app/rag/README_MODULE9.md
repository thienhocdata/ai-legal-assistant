# Module 9 — Retriever

## Chỉ thêm đúng 3 file

```text
app/rag/retriever.py
scripts/search_retriever.py
tests/test_retriever.py
```

## Dữ liệu sử dụng

```text
data/vector_db/legal_chunks.faiss
data/vector_db/legal_chunks_metadata.json
data/processed/legal_embeddings_manifest.json
data/processed/legal_chunks.json
```

## Chạy kiểm tra

```powershell
python tests\test_retriever.py
```

## Tìm kiếm thủ công

```powershell
python scripts\search_retriever.py
```

Lần đầu chạy có thể mất thời gian tải hoặc mở model embedding từ cache.
