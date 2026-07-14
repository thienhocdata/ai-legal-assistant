from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


# File này nằm trong thư mục scripts/
# ROOT sẽ tự lùi lên thư mục gốc project:
# AI - Agent pháp luật/
ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data"
METADATA_DIR = DATA_DIR / "metadata"
DOCUMENTS_METADATA_DIR = METADATA_DIR / "documents"

SOURCE_INVENTORY_PATH = METADATA_DIR / "source_inventory.csv"
PROCESSING_MANIFEST_PATH = METADATA_DIR / "processing_manifest.json"

CREATED_AT = datetime.now().isoformat(timespec="seconds")


def ensure_directories() -> None:
    directories = [
        DATA_DIR / "raw" / "laws",
        DATA_DIR / "raw" / "decrees",
        DATA_DIR / "raw" / "circulars",
        DATA_DIR / "raw" / "procedures",
        DATA_DIR / "raw" / "local",
        DATA_DIR / "processed",
        DATA_DIR / "chunks",
        DATA_DIR / "embeddings",
        DATA_DIR / "evaluation",
        DATA_DIR / "vector_db",
        METADATA_DIR,
        DOCUMENTS_METADATA_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"OK folder: {directory.relative_to(ROOT)}")


def write_json_if_not_exists(path: Path, content: dict[str, Any]) -> None:
    if path.exists():
        print(f"SKIP existing file: {path.relative_to(ROOT)}")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(content, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"CREATED file: {path.relative_to(ROOT)}")


def write_csv_if_not_exists(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    if path.exists():
        print(f"SKIP existing file: {path.relative_to(ROOT)}")
        return

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        # Use semicolon consistently because source URLs may contain commas and
        # this format opens cleanly in Vietnamese Excel installations.
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            delimiter=";",
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"CREATED file: {path.relative_to(ROOT)}")


def create_source_inventory() -> None:
    fieldnames = [
        "source_id",
        "document_id",
        "document_title",
        "document_number",
        "document_type",
        "official_source",
        "source_url",
        "source_type",
        "expected_format",
        "raw_target_path",
        "metadata_path",
        "priority",
        "language",
        "jurisdiction",
        "crawl_status",
        "crawl_date",
        "last_checked_at",
        "document_hash",
        "content_length",
        "error_message",
        "notes",
    ]

    rows = [
        {
            "source_id": "src_luat_dat_dai_2024",
            "document_id": "luat_dat_dai_2024",
            "document_title": "Luật Đất đai 2024",
            "document_number": "31/2024/QH15",
            "document_type": "Luật",
            "official_source": "Cổng văn bản Chính phủ",
            "source_url": "",
            "source_type": "official",
            "expected_format": "pdf/html",
            "raw_target_path": "data/raw/laws/luat_dat_dai_2024",
            "metadata_path": "data/metadata/documents/luat_dat_dai_2024.json",
            "priority": "1",
            "language": "vi",
            "jurisdiction": "Việt Nam",
            "crawl_status": "pending",
            "crawl_date": "",
            "last_checked_at": "",
            "document_hash": "",
            "content_length": "",
            "error_message": "",
            "notes": "Văn bản lõi để test Legal Structure Parser, Legal Chunker và Citation Engine.",
        },
        {
            "source_id": "src_luat_43_2024",
            "document_id": "luat_43_2024",
            "document_title": "Luật sửa đổi, bổ sung một số điều của Luật Đất đai",
            "document_number": "43/2024/QH15",
            "document_type": "Luật",
            "official_source": "Cổng văn bản Chính phủ",
            "source_url": "",
            "source_type": "official",
            "expected_format": "pdf/html",
            "raw_target_path": "data/raw/laws/luat_43_2024",
            "metadata_path": "data/metadata/documents/luat_43_2024.json",
            "priority": "1",
            "language": "vi",
            "jurisdiction": "Việt Nam",
            "crawl_status": "pending",
            "crawl_date": "",
            "last_checked_at": "",
            "document_hash": "",
            "content_length": "",
            "error_message": "",
            "notes": "Dùng để kiểm soát quan hệ sửa đổi, hiệu lực của Luật Đất đai 2024.",
        },
        {
            "source_id": "src_tthc_dang_ky_dat_dai",
            "document_id": "tthc_dang_ky_dat_dai",
            "document_title": "Thủ tục đăng ký đất đai, tài sản gắn liền với đất, cấp Giấy chứng nhận",
            "document_number": "",
            "document_type": "Thủ tục hành chính",
            "official_source": "Cổng Dịch vụ công Quốc gia",
            "source_url": "",
            "source_type": "official",
            "expected_format": "html",
            "raw_target_path": "data/raw/procedures/tthc_dang_ky_dat_dai",
            "metadata_path": "data/metadata/documents/tthc_dang_ky_dat_dai.json",
            "priority": "1",
            "language": "vi",
            "jurisdiction": "Việt Nam",
            "crawl_status": "pending",
            "crawl_date": "",
            "last_checked_at": "",
            "document_hash": "",
            "content_length": "",
            "error_message": "",
            "notes": "Dữ liệu thủ tục hành chính mẫu cho nhóm câu hỏi hồ sơ, trình tự, thời hạn.",
        },
    ]

    write_csv_if_not_exists(SOURCE_INVENTORY_PATH, fieldnames, rows)


def create_processing_manifest() -> None:
    manifest = {
        "project": "AI Legal Assistant - Vietnamese Land Law",
        "pipeline_name": "Knowledge Base Builder",
        "pipeline_version": "0.1.0",
        "created_at": CREATED_AT,
        "default_parser": "pymupdf",
        "default_chunk_strategy": "legal_structure",
        "default_embedding_model": "intfloat/multilingual-e5-small",
        "vector_database": "faiss",
        "processing_stages": [
            "metadata_created",
            "downloaded",
            "parsed",
            "structure_extracted",
            "chunked",
            "embedded",
            "indexed",
        ],
        "notes": "Manifest quản lý cấu hình xử lý dữ liệu cho Knowledge Base Builder.",
    }

    write_json_if_not_exists(PROCESSING_MANIFEST_PATH, manifest)


def document_metadata_template(
    *,
    document_id: str,
    document_title: str,
    document_number: str,
    document_type: str,
    tags: list[str],
    raw_file_path: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "document_id": document_id,
        "document_title": document_title,
        "document_number": document_number,
        "document_type": document_type,
        "version": "1.0",
        "language": "vi",
        "issuing_authority": "",
        "issued_date": "",
        "original_effective_date": "",
        "current_effective_date": "",
        "expiry_date": None,
        "legal_status": "unknown",
        "scope": "Toàn quốc",
        "jurisdiction": "Việt Nam",
        "legal_domain": "Đất đai",
        "tags": tags,
        "relations": {
            "amended_by": [],
            "amends": [],
            "replaces": [],
            "replaced_by": [],
            "related_documents": [],
        },
        "source": {
            "source_type": "official",
            "source_name": "",
            "source_url": "",
            "raw_file_path": raw_file_path,
            "sha256": None,
        },
        "processing": {
            "processing_status": "metadata_created",
            "parser": None,
            "chunk_strategy": None,
            "embedding_model": None,
            "indexed": False,
            "last_processed_at": None,
        },
        "notes": notes,
    }


def create_document_metadata_files() -> None:
    documents = {
        "luat_dat_dai_2024.json": document_metadata_template(
            document_id="luat_dat_dai_2024",
            document_title="Luật Đất đai 2024",
            document_number="31/2024/QH15",
            document_type="Luật",
            tags=[
                "dat_dai",
                "cap_gcn",
                "dang_ky_dat_dai",
                "tach_thua",
                "hop_thua",
                "chuyen_muc_dich",
                "chuyen_nhuong",
                "boi_thuong",
                "thu_hoi_dat",
            ],
            raw_file_path="data/raw/laws/luat_dat_dai_2024",
            notes="Văn bản lõi dùng để xây dựng Legal Structure Parser, Legal Chunker và Citation Engine.",
        ),
        "luat_43_2024.json": document_metadata_template(
            document_id="luat_43_2024",
            document_title="Luật sửa đổi, bổ sung một số điều của Luật Đất đai",
            document_number="43/2024/QH15",
            document_type="Luật",
            tags=[
                "dat_dai",
                "sua_doi",
                "hieu_luc",
                "quan_he_van_ban",
            ],
            raw_file_path="data/raw/laws/luat_43_2024",
            notes="Văn bản dùng để kiểm soát quan hệ sửa đổi và hiệu lực liên quan đến Luật Đất đai 2024.",
        ),
        "tthc_dang_ky_dat_dai.json": document_metadata_template(
            document_id="tthc_dang_ky_dat_dai",
            document_title="Thủ tục đăng ký đất đai, tài sản gắn liền với đất, cấp Giấy chứng nhận",
            document_number="",
            document_type="Thủ tục hành chính",
            tags=[
                "thu_tuc_hanh_chinh",
                "dang_ky_dat_dai",
                "cap_gcn",
                "ho_so",
                "trinh_tu",
                "thoi_han",
            ],
            raw_file_path="data/raw/procedures/tthc_dang_ky_dat_dai",
            notes="Dữ liệu thủ tục hành chính dùng để test nhóm câu hỏi về hồ sơ, trình tự và thời hạn giải quyết.",
        ),
    }

    for filename, content in documents.items():
        write_json_if_not_exists(DOCUMENTS_METADATA_DIR / filename, content)


def main() -> None:
    print("Initializing Knowledge Base scaffold...")
    print(f"Project root: {ROOT}")

    ensure_directories()
    create_source_inventory()
    create_processing_manifest()
    create_document_metadata_files()

    print("\nDone.")
    print("Created/checked:")
    print("- data/metadata/source_inventory.csv")
    print("- data/metadata/processing_manifest.json")
    print("- data/metadata/documents/*.json")


if __name__ == "__main__":
    main()
