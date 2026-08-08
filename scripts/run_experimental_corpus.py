from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.kb.baseline_chunker import CharacterChunker
from app.kb.chunk_validator import ChunkValidator
from app.kb.chunker import LegalChunker
from app.kb.legal_parser import LegalStructureParser
from app.kb.normalizer import TextNormalizer
from app.kb.parser.pdf_parser import PDFParser
from app.kb.embedding import EmbeddingManifest, SentenceTransformerEmbedder
from app.rag.vector_store import FaissVectorStore
from scripts.build_embeddings import (
    atomic_save_numpy,
    atomic_write_json,
    build_metadata_rows,
    compute_chunks_sha256,
    validate_embeddings,
)


DOCUMENT_ID = "vbhn_133_2025_luat_dat_dai"
DOCUMENT_NUMBER = "133/VBHN-VPQH"
DOCUMENT_NAME = "Văn bản hợp nhất Luật Đất đai"
INPUT_PDF = ROOT / "data" / "raw" / "laws" / DOCUMENT_ID / "133-vbhn-vpqh.pdf"
GAZETTE_DIR = ROOT / "data" / "raw" / "laws" / DOCUMENT_ID / "official_gazette"
OUTPUT_DIR = ROOT / "data" / "experiments" / DOCUMENT_ID
GAZETTE_BOILERPLATE_PATTERNS = (
    re.compile(r"^\(Xem tiếp Công báo số .+\)$", re.IGNORECASE),
    re.compile(r"^\(Tiếp theo Công báo số .+\)$", re.IGNORECASE),
    re.compile(r"^VĂN BẢN KHÁC$", re.IGNORECASE),
    re.compile(r"^VĂN BẢN HỢP NHẤT\s*-\s*VĂN PHÒNG QUỐC HỘI$", re.IGNORECASE),
    re.compile(
        r"^Văn bản hợp nhất số 133/VBHN-VPQH ngày 03 tháng 9 năm 2025$",
        re.IGNORECASE,
    ),
    re.compile(r"^hợp nhất Luật Đất đai$", re.IGNORECASE),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an isolated corpus without replacing production artifacts."
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument(
        "--source",
        choices=("official-gazette-docx", "pdf"),
        default="official-gazette-docx",
    )
    parser.add_argument(
        "--with-embeddings",
        action="store_true",
        help="Build isolated embeddings and FAISS only after the quality gate passes.",
    )
    return parser.parse_args()


def _safe_output_dir(value: Path) -> Path:
    path = (value if value.is_absolute() else ROOT / value).resolve()
    forbidden = {
        (ROOT / "data" / "processed").resolve(),
        (ROOT / "data" / "vector_db").resolve(),
    }
    if path in forbidden:
        raise ValueError("Experiment must not replace production artifact directories.")
    if ROOT.resolve() not in path.parents:
        raise ValueError("Experiment output must stay inside the repository.")
    return path


def _is_gazette_boilerplate(text: str) -> bool:
    normalized = " ".join(text.split())
    return any(pattern.fullmatch(normalized) for pattern in GAZETTE_BOILERPLATE_PATTERNS)


def _extract_gazette_docx() -> tuple[str, list[str]]:
    paths = sorted(GAZETTE_DIR.glob("part*.docx"))
    if len(paths) != 3:
        raise FileNotFoundError(f"Expected 3 Gazette DOCX parts, found {len(paths)}")
    parts: list[str] = []
    for path in paths:
        document = Document(path)
        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
            if not _is_gazette_boilerplate(paragraph.text)
        ]
        parts.append("\n".join(paragraphs))
    return "\n".join(parts), [str(path.relative_to(ROOT)) for path in paths]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    args = parse_args()
    output_dir = _safe_output_dir(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_text_path = output_dir / "raw.txt"
    normalized_path = output_dir / "normalized.txt"
    normalizer_report_path = output_dir / "normalizer_report.json"
    legal_tree_path = output_dir / "legal_tree.json"
    baseline_chunks_path = output_dir / "baseline_chunks.json"
    legal_chunks_path = output_dir / "legal_chunks.json"

    if args.source == "official-gazette-docx":
        raw_text, source_files = _extract_gazette_docx()
        pages: list[str] = []
    else:
        pages = PDFParser().extract_pages(INPUT_PDF)
        raw_text = "\n".join(pages)
        source_files = [str(INPUT_PDF.relative_to(ROOT))]
    raw_text_path.write_text(raw_text, encoding="utf-8")
    TextNormalizer().normalize_file(
        raw_text_path,
        normalized_path,
        normalizer_report_path,
        document_id=DOCUMENT_ID,
    )

    structure_parser = LegalStructureParser(
        document_id=DOCUMENT_ID,
        document_number=DOCUMENT_NUMBER,
        document_name=DOCUMENT_NAME,
        document_type="Văn bản hợp nhất",
        expected_articles=260,
        enforce_article_sequence=True,
    )
    document = structure_parser.parse_file(normalized_path)
    structure_stats = structure_parser.validate(document)
    structure_parser.write_json(document, legal_tree_path)

    low_text_pages = [
        index + 1 for index, page_text in enumerate(pages) if len(page_text.strip()) < 100
    ]
    quality_reasons: list[str] = []
    if low_text_pages:
        quality_reasons.append(
            f"Pages with insufficient extractable text: {low_text_pages}"
        )
    if structure_stats["suspicious_titles"]:
        quality_reasons.append(
            f"Suspicious article titles: {structure_stats['suspicious_titles']}"
        )
    remaining_boilerplate = sorted(
        {
            line.strip()
            for line in raw_text.splitlines()
            if _is_gazette_boilerplate(line)
        }
    )
    if remaining_boilerplate:
        quality_reasons.append(
            f"Gazette boilerplate remains in extracted text: {remaining_boilerplate}"
        )

    baseline = CharacterChunker(chunk_size=1000, overlap_chars=150)
    baseline_chunks = baseline.split_file(normalized_path, document_id=DOCUMENT_ID)
    baseline.validate_chunks(baseline_chunks)
    baseline.write_json(baseline_chunks, baseline_chunks_path)

    legal = LegalChunker(max_chars=5000, overlap_chars=200)
    legal_document = legal.load_legal_tree(legal_tree_path)
    legal_chunks = legal.build_chunks(legal_document)
    legal_stats = legal.validate_chunks(legal_document, legal_chunks)
    legal.write_json(legal_chunks, legal_chunks_path)
    validation = ChunkValidator(max_chars=5000).validate(
        legal_chunks, require_legal_metadata=True
    )
    if not validation.valid:
        raise ValueError(f"Experimental chunks failed validation: {validation.to_dict()}")

    manifest = {
        "status": (
            "parser_validated" if not quality_reasons else "structural_review_required"
        ),
        "production_replaced": False,
        "eligible_for_embeddings": not quality_reasons,
        "document_id": DOCUMENT_ID,
        "document_number": DOCUMENT_NUMBER,
        "source_mode": args.source,
        "source_files": source_files,
        "structure": structure_stats,
        "extraction": {
            "page_count": len(pages) or None,
            "low_text_pages": low_text_pages,
            "gazette_boilerplate_remaining": remaining_boilerplate,
        },
        "quality_gate": {
            "passed": not quality_reasons,
            "reasons": quality_reasons,
        },
        "legal_chunks": legal_stats,
        "baseline_chunk_count": len(baseline_chunks),
        "outputs": {
            "raw_text": str(raw_text_path.relative_to(ROOT)),
            "normalized_text": str(normalized_path.relative_to(ROOT)),
            "legal_tree": str(legal_tree_path.relative_to(ROOT)),
            "baseline_chunks": str(baseline_chunks_path.relative_to(ROOT)),
            "legal_chunks": str(legal_chunks_path.relative_to(ROOT)),
        },
        "notes": (
            "Isolated experiment; production artifacts are never replaced."
        ),
    }

    if args.with_embeddings:
        if quality_reasons:
            raise ValueError("Embeddings blocked because the quality gate did not pass.")

        embedder = SentenceTransformerEmbedder(
            model_name="intfloat/multilingual-e5-small",
            device="cpu",
            normalize_embeddings=True,
            document_prefix="passage: ",
            query_prefix="query: ",
        )
        embeddings = embedder.encode_documents(
            [str(chunk["clean_text"]) for chunk in legal_chunks], batch_size=32
        )
        embedding_stats = validate_embeddings(
            embeddings,
            expected_count=len(legal_chunks),
            expected_dimension=embedder.dimension,
        )
        embedding_path = output_dir / "legal_embeddings.npy"
        embedding_metadata_path = output_dir / "legal_embeddings_metadata.json"
        embedding_manifest_path = output_dir / "legal_embeddings_manifest.json"
        vector_index_path = output_dir / "legal_chunks.faiss"
        vector_metadata_path = output_dir / "legal_chunks_metadata.json"
        vector_manifest_path = output_dir / "vector_store_manifest.json"

        embedding_metadata = build_metadata_rows(legal_chunks)
        embedding_manifest = EmbeddingManifest(
            document_id=DOCUMENT_ID,
            source_chunks_file=str(legal_chunks_path),
            embeddings_file=str(embedding_path),
            metadata_file=str(embedding_metadata_path),
            model_name=embedder.model_name,
            device="cpu",
            normalize_embeddings=True,
            chunk_count=int(embedding_stats["count"]),
            embedding_dimension=int(embedding_stats["dimension"]),
            dtype=str(embeddings.dtype),
            text_field="clean_text",
            document_prefix="passage: ",
            query_prefix="query: ",
            source_chunks_sha256=compute_chunks_sha256(legal_chunks),
        )
        atomic_save_numpy(embeddings, embedding_path)
        atomic_write_json(embedding_metadata, embedding_metadata_path)
        atomic_write_json(embedding_manifest.to_dict(), embedding_manifest_path)

        store = FaissVectorStore()
        store.build(embeddings, embedding_metadata)
        store.save(vector_index_path, vector_metadata_path)
        vector_manifest = {
            "provider": "faiss",
            "index_type": "IndexFlatIP",
            "metric": "cosine_similarity",
            "vector_count": int(store.index.ntotal),
            "dimension": store.dimension,
            "model_name": embedder.model_name,
            "index_file": str(vector_index_path),
            "metadata_file": str(vector_metadata_path),
            "production_replaced": False,
        }
        atomic_write_json(vector_manifest, vector_manifest_path)
        manifest["status"] = "experimental_index_built"
        manifest["embeddings"] = embedding_manifest.to_dict()
        manifest["vector_store"] = vector_manifest

    (output_dir / "experiment_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
