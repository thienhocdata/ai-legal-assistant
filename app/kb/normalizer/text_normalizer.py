from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from .noise_detector import NoiseDetector
from .normalizer_report import NormalizerReport


class TextNormalizer:
    """
    Chuẩn hóa văn bản sau PDF Parser.

    Bản v2:
    - loại dòng rác;
    - chuẩn hóa Unicode/khoảng trắng;
    - ghép tiêu đề Điều bị ngắt dòng;
    - ghép các dòng văn bản bị xuống dòng do bố cục PDF;
    - vẫn giữ nguyên các mốc Chương/Mục/Điều/Khoản/Điểm.
    """

    ARTICLE_RE = re.compile(r"^Điều\s+\d+\.\s+.+$", re.IGNORECASE)
    CHAPTER_RE = re.compile(r"^Chương\s+[IVXLCDM]+\s*$", re.IGNORECASE)
    SECTION_RE = re.compile(r"^Mục\s+\d+\s*$", re.IGNORECASE)
    CLAUSE_RE = re.compile(r"^\d+\.\s+")
    POINT_RE = re.compile(r"^[a-zđ]\)\s+", re.IGNORECASE)

    MULTI_SPACE_RE = re.compile(r"[ \t]+")
    MULTI_BLANK_RE = re.compile(r"\n{3,}")

    def __init__(self, noise_detector: NoiseDetector | None = None) -> None:
        self.noise_detector = noise_detector or NoiseDetector()

    def normalize_line(self, line: str) -> str:
        line = unicodedata.normalize("NFC", line)
        line = line.replace("\u00a0", " ")
        line = line.replace("\u200b", "")
        line = line.replace("\ufeff", "")
        line = self.MULTI_SPACE_RE.sub(" ", line)
        return line.strip()

    def is_structural_line(self, line: str) -> bool:
        return bool(
            self.CHAPTER_RE.match(line)
            or self.SECTION_RE.match(line)
            or self.ARTICLE_RE.match(line)
            or self.CLAUSE_RE.match(line)
            or self.POINT_RE.match(line)
        )

    @staticmethod
    def _is_all_caps_text(line: str) -> bool:
        letters = [char for char in line if char.isalpha()]
        return bool(letters) and all(char.isupper() for char in letters)

    def _should_merge_wrapped_lines(self, current: str, next_line: str) -> bool:
        if not current or not next_line:
            return False
        if self.is_structural_line(current) or self.is_structural_line(next_line):
            return False

        # Ghép các tiêu đề viết hoa như "LUẬT" + "ĐẤT ĐAI".
        if self._is_all_caps_text(current) and self._is_all_caps_text(next_line):
            return True

        # Dòng kế tiếp bắt đầu bằng chữ thường gần như chắc chắn là dòng bị wrap.
        first_alpha = next((c for c in next_line if c.isalpha()), "")
        if first_alpha and first_alpha.islower():
            return True

        # Nếu dòng hiện tại chưa kết thúc câu, coi dòng sau là phần tiếp nối.
        if not current.endswith((".", "?", "!", ";", ":")):
            return True

        return False

    def _merge_wrapped_article_titles(
        self,
        lines: list[str],
        report: NormalizerReport,
    ) -> list[str]:
        merged: list[str] = []
        index = 0

        while index < len(lines):
            current = lines[index]

            if not self.ARTICLE_RE.match(current) or index + 1 >= len(lines):
                merged.append(current)
                index += 1
                continue

            next_line = lines[index + 1]
            if not next_line or self.is_structural_line(next_line):
                merged.append(current)
                index += 1
                continue

            after_next = lines[index + 2] if index + 2 < len(lines) else ""
            likely_title_tail = (
                len(next_line) <= 120
                and (
                    not after_next
                    or self.is_structural_line(after_next)
                    or after_next == ""
                )
            )

            if likely_title_tail:
                merged.append(f"{current} {next_line}".strip())
                report.wrapped_titles_merged += 1
                report.wrapped_lines_merged += 1
                index += 2
                continue

            merged.append(current)
            index += 1

        return merged

    def _merge_general_wrapped_lines(
        self,
        lines: list[str],
        report: NormalizerReport,
    ) -> list[str]:
        """
        Ghép các dòng bị xuống dòng do chiều rộng trang PDF.

        Không ghép qua các mốc cấu trúc pháp lý hoặc dòng trống.
        """
        if not lines:
            return []

        merged: list[str] = []
        index = 0

        while index < len(lines):
            current = lines[index]

            if not current:
                merged.append("")
                index += 1
                continue

            while index + 1 < len(lines):
                next_line = lines[index + 1]

                if not next_line:
                    break
                if self.is_structural_line(next_line):
                    break
                if self._should_merge_wrapped_lines(current, next_line):
                    current = f"{current} {next_line}".strip()
                    report.wrapped_lines_merged += 1
                    index += 1
                    continue
                break

            merged.append(current)
            index += 1

        return merged

    def normalize_text_with_report(
        self,
        text: str,
        *,
        document_id: str,
        input_file: str,
        output_file: str,
    ) -> tuple[str, NormalizerReport]:
        if not isinstance(text, str):
            raise TypeError("text phải là chuỗi.")

        report = NormalizerReport(
            document_id=document_id,
            input_file=input_file,
            output_file=output_file,
            raw_characters=len(text),
            raw_lines=len(text.splitlines()),
        )

        cleaned_lines: list[str] = []
        previous_was_blank = False

        for raw_line in text.splitlines():
            line = self.normalize_line(raw_line)
            noise_kind = self.noise_detector.classify(line)

            if noise_kind is not None:
                report.increment_removed(noise_kind.value)
                continue

            if not line:
                if cleaned_lines and not previous_was_blank:
                    cleaned_lines.append("")
                else:
                    report.blank_lines_collapsed += 1
                previous_was_blank = True
                continue

            cleaned_lines.append(line)
            previous_was_blank = False

        while cleaned_lines and cleaned_lines[-1] == "":
            cleaned_lines.pop()

        cleaned_lines = self._merge_wrapped_article_titles(cleaned_lines, report)
        cleaned_lines = self._merge_general_wrapped_lines(cleaned_lines, report)

        normalized_text = "\n".join(cleaned_lines)
        normalized_text = self.MULTI_BLANK_RE.sub("\n\n", normalized_text)
        if normalized_text:
            normalized_text += "\n"

        report.normalized_characters = len(normalized_text)
        report.normalized_lines = len(normalized_text.splitlines())
        report.status = "success"

        if report.retention_ratio < 0.85:
            report.warnings.append(
                "Tỷ lệ giữ lại nội dung dưới 85%; cần kiểm tra quy tắc làm sạch."
            )

        return normalized_text, report

    def normalize_text(self, text: str) -> str:
        normalized_text, _ = self.normalize_text_with_report(
            text,
            document_id="unknown",
            input_file="",
            output_file="",
        )
        return normalized_text

    def normalize_file(
        self,
        input_path: str | Path,
        output_path: str | Path,
        report_path: str | Path,
        *,
        document_id: str,
    ) -> tuple[Path, Path]:
        source = Path(input_path)
        destination = Path(output_path)
        report_destination = Path(report_path)

        if not source.exists():
            raise FileNotFoundError(f"Không tìm thấy file đầu vào: {source}")
        if not source.is_file():
            raise ValueError(f"Đường dẫn đầu vào không phải file: {source}")

        raw_text = source.read_text(encoding="utf-8")
        normalized_text, report = self.normalize_text_with_report(
            raw_text,
            document_id=document_id,
            input_file=str(source),
            output_file=str(destination),
        )

        if not normalized_text.strip():
            raise ValueError("Kết quả chuẩn hóa bị rỗng.")

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(normalized_text, encoding="utf-8")
        report.write_json(report_destination)
        return destination, report_destination
