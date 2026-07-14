from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json


@dataclass(slots=True)
class NormalizerReport:
    document_id: str
    input_file: str
    output_file: str

    raw_characters: int = 0
    normalized_characters: int = 0
    raw_lines: int = 0
    normalized_lines: int = 0

    removed_lines: int = 0
    blank_lines_collapsed: int = 0
    wrapped_lines_merged: int = 0
    wrapped_titles_merged: int = 0

    removed_by_type: dict[str, int] = field(default_factory=dict)
    status: str = "pending"
    warnings: list[str] = field(default_factory=list)

    @property
    def removed_characters(self) -> int:
        return max(0, self.raw_characters - self.normalized_characters)

    @property
    def retention_ratio(self) -> float:
        if self.raw_characters == 0:
            return 0.0
        return self.normalized_characters / self.raw_characters

    def increment_removed(self, noise_type: str) -> None:
        self.removed_lines += 1
        self.removed_by_type[noise_type] = self.removed_by_type.get(noise_type, 0) + 1

    def to_dict(self) -> dict:
        data = asdict(self)
        data["removed_characters"] = self.removed_characters
        data["retention_ratio"] = round(self.retention_ratio, 6)
        return data

    def write_json(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path
