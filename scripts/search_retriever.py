from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rag.retriever import LegalRetriever


INDEX_PATH = (
    ROOT
    / "data"
    / "vector_db"
    / "legal_chunks.faiss"
)

VECTOR_METADATA_PATH = (
    ROOT
    / "data"
    / "vector_db"
    / "legal_chunks_metadata.json"
)

EMBEDDING_MANIFEST_PATH = (
    ROOT
    / "data"
    / "processed"
    / "legal_embeddings_manifest.json"
)

CHUNKS_PATH = (
    ROOT
    / "data"
    / "processed"
    / "legal_chunks.json"
)


def main() -> None:
    retriever = LegalRetriever(
        index_path=INDEX_PATH,
        vector_metadata_path=VECTOR_METADATA_PATH,
        embedding_manifest_path=EMBEDDING_MANIFEST_PATH,
        chunks_path=CHUNKS_PATH,
        device="cpu",
    )

    question = input(
        "Nhập câu hỏi pháp luật đất đai: "
    ).strip()

    results = retriever.retrieve(
        question,
        top_k=5,
    )

    print("=" * 80)
    print("MODULE 9 - RETRIEVER")
    print("=" * 80)

    for result in results:
        print(
            f"{result['rank']}. "
            f"Điều {result['article_no']} - "
            f"{result['article_title']}"
        )
        print(
            f"   Score : {result['score']:.4f}"
        )
        print(
            f"   Khoản : {result['clause_nos']}"
        )
        print(
            f"   Điểm  : {result['point_nos']}"
        )
        print(
            f"   Chunk : {result['chunk_id']}"
        )

        preview = str(
            result["clean_text"]
        )[:500]

        print(f"   Text  : {preview}")
        print("-" * 80)

    print("Status : SUCCESS")


if __name__ == "__main__":
    main()
