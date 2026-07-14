from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
from typing import Any, Iterable


@dataclass(slots=True)
class InventoryRecord:
    """One source row from ``source_inventory.csv``."""

    values: dict[str, str]

    @property
    def source_id(self) -> str:
        return self.values.get("source_id", "").strip()

    @property
    def document_id(self) -> str:
        return self.values.get("document_id", "").strip()

    @property
    def source_urls(self) -> list[str]:
        raw = self.values.get("source_url", "")
        return [value.strip() for value in raw.split(",") if value.strip()]

    @property
    def raw_target_path(self) -> str:
        return self.values.get("raw_target_path", "").strip()


class SourceInventory:
    """Read and update the project source inventory without losing columns."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.fieldnames: list[str] = []
        self.records: list[InventoryRecord] = []
        self.delimiter = ";"

    def load(self) -> list[InventoryRecord]:
        if not self.path.exists():
            raise FileNotFoundError(f"Không tìm thấy inventory: {self.path}")

        with self.path.open("r", encoding="utf-8-sig", newline="") as file:
            sample = file.read(4096)
            file.seek(0)

            header = sample.splitlines()[0] if sample else ""
            self.delimiter = ";" if header.count(";") > header.count(",") else ","
            reader = csv.DictReader(file, delimiter=self.delimiter)
            self.fieldnames = list(reader.fieldnames or [])
            self.records = [
                InventoryRecord(
                    {
                        str(key): "" if value is None else str(value)
                        for key, value in row.items()
                        if key is not None
                    }
                )
                for row in reader
            ]

        self._validate()
        return list(self.records)

    def _validate(self) -> None:
        if not self.fieldnames:
            raise ValueError("Inventory không có header.")

        required = {"source_id", "document_id", "source_url", "raw_target_path"}
        missing = sorted(required - set(self.fieldnames))
        if missing:
            raise ValueError(f"Inventory thiếu cột bắt buộc: {missing}")

        ids = [record.source_id for record in self.records]
        if any(not value for value in ids):
            raise ValueError("Inventory có source_id rỗng.")
        if len(ids) != len(set(ids)):
            raise ValueError("Inventory có source_id trùng.")

    def get(self, source_id: str) -> InventoryRecord:
        if not self.records:
            self.load()
        for record in self.records:
            if record.source_id == source_id:
                return record
        raise KeyError(f"Không tìm thấy source_id: {source_id}")

    def update(self, source_id: str, **values: Any) -> InventoryRecord:
        record = self.get(source_id)
        unknown = sorted(set(values) - set(self.fieldnames))
        if unknown:
            raise KeyError(f"Cột inventory không tồn tại: {unknown}")
        for key, value in values.items():
            record.values[key] = "" if value is None else str(value)
        return record

    def save(self, records: Iterable[InventoryRecord] | None = None) -> Path:
        selected = list(records) if records is not None else self.records
        if not self.fieldnames:
            raise ValueError("Phải load inventory trước khi save.")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=self.fieldnames,
                delimiter=self.delimiter,
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(record.values for record in selected)
        temporary.replace(self.path)
        return self.path
