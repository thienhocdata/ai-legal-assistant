from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.kb.normalizer.text_normalizer import TextNormalizer


INPUT_PATH = ROOT / "data" / "processed" / "luat_dat_dai_2024.txt"
OUTPUT_PATH = ROOT / "data" / "processed" / "luat_dat_dai_2024_normalized.txt"
REPORT_PATH = ROOT / "data" / "processed" / "luat_dat_dai_2024_normalizer_report.json"


def test_general_wrapped_line_repair() -> None:
    sample = """LUẬT
ĐẤT ĐAI

Điều 1. Phạm vi điều chỉnh
Luật này quy định về chế độ sở hữu
toàn dân về đất đai.
"""

    normalized = TextNormalizer().normalize_text(sample)

    assert "LUẬT ĐẤT ĐAI" in normalized
    assert "chế độ sở hữu toàn dân về đất đai." in normalized


def test_article_title_repair() -> None:
    sample = """Điều 7. Người chịu trách nhiệm trước Nhà nước đối với đất được giao
quản lý
1. Nội dung khoản một.
"""

    normalized = TextNormalizer().normalize_text(sample)

    assert (
        "Điều 7. Người chịu trách nhiệm trước Nhà nước "
        "đối với đất được giao quản lý"
    ) in normalized


def test_standalone_year_is_not_removed_as_page_number() -> None:
    sample = """Chương I
2024
15
Điều 1. Phạm vi điều chỉnh
Nội dung.
"""
    normalized = TextNormalizer().normalize_text(sample)
    assert "2024" in normalized.splitlines()
    assert "15" not in normalized.splitlines()


def test_text_normalizer_integration() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Chưa có file đầu vào: {INPUT_PATH}\nHãy chạy Module 2 trước."
        )

    output_path, report_path = TextNormalizer().normalize_file(
        INPUT_PATH,
        OUTPUT_PATH,
        REPORT_PATH,
        document_id="luat_dat_dai_2024",
    )

    raw_text = INPUT_PATH.read_text(encoding="utf-8")
    normalized_text = output_path.read_text(encoding="utf-8")
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert normalized_text.strip()
    assert "Điều 1." in normalized_text
    assert "Điều 260." in normalized_text
    assert len(normalized_text) >= len(raw_text) * 0.85
    assert report["status"] == "success"
    assert report["wrapped_lines_merged"] > 0


def main() -> None:
    output_path, report_path = TextNormalizer().normalize_file(
        INPUT_PATH,
        OUTPUT_PATH,
        REPORT_PATH,
        document_id="luat_dat_dai_2024",
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))

    print("=" * 72)
    print("MODULE 3 - TEXT NORMALIZER V2")
    print("=" * 72)
    print(f"Input             : {INPUT_PATH}")
    print(f"Output            : {output_path}")
    print(f"Report            : {report_path}")
    print(f"Raw characters    : {report['raw_characters']:,}")
    print(f"Clean characters  : {report['normalized_characters']:,}")
    print(f"Removed lines     : {report['removed_lines']:,}")
    print(f"Wrapped lines     : {report['wrapped_lines_merged']:,}")
    print(f"Titles merged     : {report['wrapped_titles_merged']:,}")
    print(f"Retention ratio   : {report['retention_ratio']:.2%}")
    print(f"Status            : {report['status'].upper()}")


if __name__ == "__main__":
    main()
