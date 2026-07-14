from __future__ import annotations

import re
from enum import StrEnum


class NoiseKind(StrEnum):
    HEADER = "header"
    FOOTER = "footer"
    PAGE_NUMBER = "page_number"
    DIGITAL_SIGNATURE = "digital_signature"
    DOCUMENT_BANNER = "document_banner"
    UNKNOWN = "unknown"


class NoiseDetector:
    """Nhận diện các dòng rác thường gặp trong PDF văn bản pháp luật."""

    HEADER_PATTERNS = (
        re.compile(r"^CÔNG BÁO/Số\b", re.IGNORECASE),
        re.compile(r"^Số\s+\d+\s*-\s*CÔNG BÁO\b", re.IGNORECASE),
    )

    DOCUMENT_BANNER_PATTERNS = (
        re.compile(r"^VĂN BẢN QUY PHẠM PHÁP LUẬT$", re.IGNORECASE),
        re.compile(r"^CHỦ TỊCH NƯỚC\s*-\s*QUỐC HỘI$", re.IGNORECASE),
    )

    DIGITAL_SIGNATURE_PATTERNS = (
        re.compile(r"^Người ký:", re.IGNORECASE),
        re.compile(r"^Email:", re.IGNORECASE),
        re.compile(r"^Cơ quan:", re.IGNORECASE),
        re.compile(r"^Thời gian ký:", re.IGNORECASE),
    )

    # Four-digit values are commonly standalone years (for example 2024).
    # Treating them as page numbers silently removes legal facts.
    PAGE_NUMBER_RE = re.compile(r"^\d{1,3}$")

    def classify(self, line: str) -> NoiseKind | None:
        stripped = line.strip()

        if not stripped:
            return None
        if self.PAGE_NUMBER_RE.fullmatch(stripped):
            return NoiseKind.PAGE_NUMBER
        if any(pattern.match(stripped) for pattern in self.HEADER_PATTERNS):
            return NoiseKind.HEADER
        if any(pattern.match(stripped) for pattern in self.DOCUMENT_BANNER_PATTERNS):
            return NoiseKind.DOCUMENT_BANNER
        if any(pattern.match(stripped) for pattern in self.DIGITAL_SIGNATURE_PATTERNS):
            return NoiseKind.DIGITAL_SIGNATURE
        return None

    def is_noise(self, line: str) -> bool:
        return self.classify(line) is not None
