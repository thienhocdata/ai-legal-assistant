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

    question = (
        "Điều kiện chuyển nhượng "
        "quyền sử dụng đất là gì?"
    )

    results = retriever.retrieve(
        question,
        top_k=5,
    )

    if len(results) != 5:
        raise ValueError(
            "Retriever không trả đủ 5 kết quả."
        )

    chunk_ids = [
        result["chunk_id"]
        for result in results
    ]

    if len(chunk_ids) != len(
        set(chunk_ids)
    ):
        raise ValueError(
            "Retriever trả chunk_id bị trùng."
        )

    previous_score = None

    for result in results:
        if not result["chunk_id"]:
            raise ValueError(
                "Kết quả thiếu chunk_id."
            )

        if not result["clean_text"]:
            raise ValueError(
                "Kết quả thiếu nội dung chunk."
            )

        score = float(
            result["score"]
        )

        if (
            previous_score is not None
            and score > previous_score
        ):
            raise ValueError(
                "Kết quả không được sắp theo score giảm dần."
            )

        previous_score = score

    context = retriever.retrieve_context(
        question,
        top_k=3,
    )

    if not context.strip():
        raise ValueError(
            "retrieve_context trả về rỗng."
        )

    hybrid_results = retriever.retrieve_hybrid(
        question,
        top_k=5,
    )

    if len(hybrid_results) != 5:
        raise ValueError("Hybrid retriever không trả đủ kết quả.")

    if not all(
        "dense_score" in item and "lexical_score" in item
        for item in hybrid_results
    ):
        raise ValueError("Hybrid result thiếu thành phần score.")

    print("=" * 80)
    print("MODULE 9 - RETRIEVER VALIDATION")
    print("=" * 80)
    print(f"Question          : {question}")
    print(f"Results           : {len(results)}")
    print(
        f"Top chunk         : "
        f"{results[0]['chunk_id']}"
    )
    print(
        f"Top score         : "
        f"{results[0]['score']:.4f}"
    )
    print(
        f"Top article       : "
        f"{results[0]['article_no']}"
    )
    print("Status            : SUCCESS")


if __name__ == "__main__":
    main()
