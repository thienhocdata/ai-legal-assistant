from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Any

from .models import BaselineChunk


class CharacterChunker:
    """
    Baseline chunker chia văn bản theo số ký tự cố định.

    Module này cố ý không hiểu:
    - Chương;
    - Mục;
    - Điều;
    - Khoản;
    - Điểm.

    Mục đích là tạo baseline để so sánh với Legal Chunker.
    """

    def __init__(
        self,
        *,
        chunk_size: int = 1000,
        overlap_chars: int = 150,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size phải lớn hơn 0.")

        if overlap_chars < 0:
            raise ValueError("overlap_chars không được âm.")

        if overlap_chars >= chunk_size:
            raise ValueError(
                "overlap_chars phải nhỏ hơn chunk_size."
            )

        self.chunk_size = chunk_size
        self.overlap_chars = overlap_chars

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Chuẩn hóa khoảng trắng cho baseline embedding.
        """
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def split_text(
        self,
        text: str,
        *,
        document_id: str,
        source_file: str,
    ) -> list[dict[str, Any]]:
        """
        Chia text thành các chunk theo cửa sổ ký tự cố định.
        """
        clean_text = self.normalize_text(text)

        if not clean_text:
            raise ValueError("Văn bản đầu vào rỗng.")

        step = self.chunk_size - self.overlap_chars
        chunks: list[dict[str, Any]] = []

        start_char = 0
        chunk_index = 1

        while start_char < len(clean_text):
            end_char = min(
                start_char + self.chunk_size,
                len(clean_text),
            )

            chunk_text = clean_text[start_char:end_char].strip()

            if chunk_text:
                chunk = BaselineChunk(
                    chunk_id=(
                        f"{document_id}_baseline_"
                        f"{chunk_index:04d}"
                    ),
                    document_id=document_id,
                    chunk_index=chunk_index,
                    chunk_type="character",
                    start_char=start_char,
                    end_char=end_char,
                    chunk_size=self.chunk_size,
                    overlap_chars=self.overlap_chars,
                    text=chunk_text,
                    source_file=source_file,
                )
                chunks.append(chunk.to_dict())
                chunk_index += 1

            if end_char >= len(clean_text):
                break

            start_char += step

        return chunks

    def split_file(
        self,
        input_path: str | Path,
        *,
        document_id: str,
    ) -> list[dict[str, Any]]:
        path = Path(input_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy file đầu vào: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Đường dẫn đầu vào không phải file: {path}"
            )

        text = path.read_text(encoding="utf-8")

        return self.split_text(
            text,
            document_id=document_id,
            source_file=str(path),
        )

    def validate_chunks(
        self,
        chunks: list[dict[str, Any]],
    ) -> dict[str, float | int]:
        if not chunks:
            raise ValueError("Không tạo được chunk nào.")

        chunk_ids = [chunk["chunk_id"] for chunk in chunks]

        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError("Phát hiện chunk_id bị trùng.")

        expected_indexes = list(range(1, len(chunks) + 1))
        actual_indexes = [
            chunk["chunk_index"] for chunk in chunks
        ]

        if actual_indexes != expected_indexes:
            raise ValueError(
                "chunk_index không liên tục từ 1."
            )

        for chunk in chunks:
            text = chunk.get("text", "")

            if not text.strip():
                raise ValueError(
                    f"Chunk rỗng: {chunk['chunk_id']}"
                )

            if len(text) > self.chunk_size:
                raise ValueError(
                    f"Chunk vượt quá chunk_size: "
                    f"{chunk['chunk_id']}"
                )

            if chunk["end_char"] <= chunk["start_char"]:
                raise ValueError(
                    f"Vị trí ký tự không hợp lệ: "
                    f"{chunk['chunk_id']}"
                )

        lengths = [len(chunk["text"]) for chunk in chunks]

        return {
            "count": len(chunks),
            "average_length": sum(lengths) / len(lengths),
            "shortest_length": min(lengths),
            "longest_length": max(lengths),
        }

    @staticmethod
    def write_json(
        chunks: list[dict[str, Any]],
        output_path: str | Path,
    ) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(
            json.dumps(
                chunks,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return path
