from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.kb.baseline_chunker import CharacterChunker
from app.kb.chunk_validator import ChunkValidator
from app.kb.chunker import LegalChunker
from app.kb.legal_parser import LegalStructureParser
from app.kb.normalizer import TextNormalizer
from app.kb.parser.pdf_parser import PDFParser


RAW_TEXT = ROOT / "data" / "processed" / "luat_dat_dai_2024.txt"
NORMALIZED_TEXT = ROOT / "data" / "processed" / "luat_dat_dai_2024_normalized.txt"
NORMALIZER_REPORT = ROOT / "data" / "processed" / "luat_dat_dai_2024_normalizer_report.json"
LEGAL_TREE = ROOT / "data" / "processed" / "luat_dat_dai_2024.json"
BASELINE_CHUNKS = ROOT / "data" / "processed" / "baseline_chunks.json"
LEGAL_CHUNKS = ROOT / "data" / "processed" / "legal_chunks.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild the land-law knowledge base.")
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Stop after chunk validation (useful for quick parser development).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdfs = sorted(
        (ROOT / "data" / "raw" / "laws" / "luat_dat_dai_2024").glob("*.pdf")
    )
    if len(pdfs) != 3:
        raise FileNotFoundError(f"Cần đúng 3 PDF nguồn, hiện có {len(pdfs)}.")

    parser = PDFParser()
    raw_text = "\n".join(parser.extract_text(path) for path in pdfs)
    RAW_TEXT.parent.mkdir(parents=True, exist_ok=True)
    RAW_TEXT.write_text(raw_text, encoding="utf-8")
    print(f"[2/10] PDF Parser: {len(raw_text):,} ký tự")

    TextNormalizer().normalize_file(
        RAW_TEXT,
        NORMALIZED_TEXT,
        NORMALIZER_REPORT,
        document_id="luat_dat_dai_2024",
    )
    print("[3/10] Text Normalizer: SUCCESS")

    structure_parser = LegalStructureParser()
    document = structure_parser.parse_file(NORMALIZED_TEXT)
    structure_stats = structure_parser.validate(document)
    structure_parser.write_json(document, LEGAL_TREE)
    print(f"[4/10] Legal Structure: {structure_stats['articles']} Điều")

    baseline = CharacterChunker(chunk_size=1000, overlap_chars=150)
    baseline_chunks = baseline.split_file(
        NORMALIZED_TEXT, document_id="luat_dat_dai_2024"
    )
    baseline.validate_chunks(baseline_chunks)
    baseline.write_json(baseline_chunks, BASELINE_CHUNKS)
    print(f"[5/10] Baseline Chunker: {len(baseline_chunks)} chunks")

    legal = LegalChunker(max_chars=5000, overlap_chars=200)
    legal_document = legal.load_legal_tree(LEGAL_TREE)
    legal_chunks = legal.build_chunks(legal_document)
    legal.validate_chunks(legal_document, legal_chunks)
    legal.write_json(legal_chunks, LEGAL_CHUNKS)
    report = ChunkValidator(max_chars=5000).validate(
        legal_chunks, require_legal_metadata=True
    )
    if not report.valid:
        raise ValueError(f"Chunk validation thất bại: {report.to_dict()}")
    print(f"[6-7/10] Legal Chunker + Validator: {len(legal_chunks)} chunks")

    if not args.skip_embeddings:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build_embeddings.py")],
            cwd=ROOT,
            check=True,
        )
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build_vector_db.py")],
            cwd=ROOT,
            check=True,
        )
        print("[8-10/10] Embedding + FAISS + Retriever artifacts: SUCCESS")


if __name__ == "__main__":
    main()
