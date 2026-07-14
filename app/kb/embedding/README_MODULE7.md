# Module 7 — Embedding

## Input

```text
data/processed/legal_chunks.json
```

## Output

```text
data/processed/legal_embeddings.npy
data/processed/legal_embeddings_metadata.json
data/processed/legal_embeddings_manifest.json
```

## Cài thư viện

```bat
pip install -r requirements_module7.txt
```

## Chạy

```bat
python scripts\build_embeddings.py
python tests\test_embeddings.py
```

Lần đầu chạy, model sẽ được tải về máy. Những lần sau sẽ dùng cache cục bộ.

## Model mặc định

```text
intfloat/multilingual-e5-small
```

Văn bản được thêm prefix `passage: ` và câu hỏi sau này dùng prefix `query: `.
