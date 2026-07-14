from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.kb.parser.pdf_parser import PDFParser


EXPECTED_START_MARKERS = {
    1: "Điều 1.",
    2: "Điều 91.",
    3: "Điều 171.",
}


def find_pdf(part: int) -> Path:
    """
    Tìm file PDF theo cấu trúc thư mục hiện tại.

    Ưu tiên đường dẫn chuẩn:
    data/raw/laws/luat_dat_dai_2024/
    """
    file_name = f"luat_dat_dai_2024_part{part}.pdf"

    candidates = [
        ROOT / "data" / "raw" / "laws" / "luat_dat_dai_2024" / file_name,
        # Giữ tương thích với cây thư mục cũ nếu vẫn còn thư mục laws/laws.
        ROOT / "data" / "raw" / "laws" / "laws" / "luat_dat_dai_2024" / file_name,
    ]

    pdf_path = next((path for path in candidates if path.is_file()), None)

    if pdf_path is None:
        raise FileNotFoundError(
            f"Không tìm thấy {file_name} tại các vị trí dự kiến:\n"
            + "\n".join(str(path) for path in candidates)
        )

    return pdf_path


def build_combined_text() -> str:
    parser = PDFParser()
    combined_text_parts: list[str] = []

    for part in (1, 2, 3):
        pdf_path = find_pdf(part)

        pages = parser.extract_pages(pdf_path)
        assert pages, f"{pdf_path.name} không có trang nào."

        text = "\n".join(pages).strip()
        assert text, f"{pdf_path.name} không trích xuất được nội dung."

        expected_marker = EXPECTED_START_MARKERS[part]
        assert expected_marker in text, (
            f"{pdf_path.name} không chứa marker mong đợi: {expected_marker}"
        )

        combined_text_parts.append(text)

        print(
            f"OK part {part}: {pdf_path.name} | "
            f"{len(pages)} trang | {len(text):,} ký tự"
        )

    combined_text = "\n\n".join(combined_text_parts)

    assert "Điều 1." in combined_text
    assert "Điều 91." in combined_text
    assert "Điều 171." in combined_text
    assert "Điều 260." in combined_text

    return combined_text


def test_pdf_parser_extracts_all_three_parts() -> None:
    """
    Kiểm thử tích hợp: đọc đủ 3 PDF và xác nhận các mốc chính.
    """
    combined_text = build_combined_text()
    assert len(combined_text) > 0


def main() -> None:
    combined_text = build_combined_text()

    output = ROOT / "data" / "processed" / "luat_dat_dai_2024.txt"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(combined_text, encoding="utf-8")

    print(f"Saved: {output}")
    print(f"Total characters: {len(combined_text):,}")


if __name__ == "__main__":
    main()