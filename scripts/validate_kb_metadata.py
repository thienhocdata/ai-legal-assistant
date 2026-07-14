from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pydantic import ValidationError

from app.schemas.kb_schemas import DocumentMetadata, SourceInventoryRow

SOURCE_INVENTORY_PATH = ROOT / "data" / "metadata" / "source_inventory.csv"
DOCUMENTS_METADATA_DIR = ROOT / "data" / "metadata" / "documents"


def validate_document_metadata_files() -> bool:
    print("\nValidating document metadata JSON files...")

    is_valid = True
    json_files = sorted(DOCUMENTS_METADATA_DIR.glob("*.json"))

    if not json_files:
        print("ERROR: Không tìm thấy file metadata JSON nào.")
        return False

    for json_file in json_files:
        try:
            raw_json = json_file.read_text(encoding="utf-8")
            metadata = DocumentMetadata.model_validate_json(raw_json)

            print(f"OK: {json_file.relative_to(ROOT)} -> {metadata.document_id}")

        except ValidationError as error:
            is_valid = False
            print(f"\nERROR in {json_file.relative_to(ROOT)}")
            print(error)

    return is_valid


def validate_source_inventory() -> bool:
    print("\nValidating source_inventory.csv...")

    if not SOURCE_INVENTORY_PATH.exists():
        print(f"ERROR: Không tìm thấy {SOURCE_INVENTORY_PATH}")
        return False

    is_valid = True

    with SOURCE_INVENTORY_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        sample = file.read(4096)
        file.seek(0)

        header = sample.splitlines()[0] if sample else ""
        delimiter = ";" if header.count(";") > header.count(",") else ","
        reader = csv.DictReader(file, delimiter=delimiter)

        for index, row in enumerate(reader, start=2):
            try:
                SourceInventoryRow.model_validate(row)
                print(f"OK: row {index} -> {row.get('source_id')}")

            except ValidationError as error:
                is_valid = False
                print(f"\nERROR in source_inventory.csv row {index}")
                print(error)

    return is_valid


def main() -> None:
    metadata_ok = validate_document_metadata_files()
    inventory_ok = validate_source_inventory()

    print("\nValidation result:")

    if metadata_ok and inventory_ok:
        print("SUCCESS: Knowledge Base metadata hợp lệ.")
    else:
        print("FAILED: Metadata còn lỗi, cần sửa trước khi chạy pipeline.")


if __name__ == "__main__":
    main()
