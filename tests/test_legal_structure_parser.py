from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.kb.legal_parser import LegalStructureParser


INPUT_PATH = (
    ROOT
    / "data"
    / "processed"
    / "luat_dat_dai_2024_normalized.txt"
)

OUTPUT_PATH = (
    ROOT
    / "data"
    / "processed"
    / "luat_dat_dai_2024.json"
)


def _articles_by_number(document) -> dict[int, object]:
    parser = LegalStructureParser()
    return {
        int(article.article_no): article
        for article in parser.collect_articles(document)
    }


def test_title_tail_and_opening_body_are_separated() -> None:
    sample = """Chương I
QUY ĐỊNH CHUNG
Điều 1. Giải thích từ ngữ Trong Luật này, các từ ngữ được hiểu như sau:
1. Nội dung khoản một.
Điều 2. Thu hồi đất vì lợi ích quốc gia,
công cộng Nhà nước thu hồi đất trong các trường hợp sau đây:
1. Nội dung khoản một.
"""
    parser = LegalStructureParser()
    document = parser.parse_text(sample, source_file="sample.txt")
    articles = _articles_by_number(document)

    assert articles[1].article_title == "Giải thích từ ngữ"
    assert articles[1].article_text.startswith("Trong Luật này")
    assert articles[2].article_title == "Thu hồi đất vì lợi ích quốc gia, công cộng"
    assert articles[2].article_text.startswith("Nhà nước thu hồi đất")


def test_real_document_has_clean_article_titles() -> None:
    parser = LegalStructureParser()
    document = parser.parse_file(INPUT_PATH)
    stats = parser.validate(document)
    articles = _articles_by_number(document)

    assert stats["suspicious_titles"] == 0
    assert articles[3].article_title == "Giải thích từ ngữ"
    assert articles[45].article_title.endswith("nhận tặng cho quyền sử dụng đất")
    assert articles[78].article_title == "Thu hồi đất vì mục đích quốc phòng, an ninh"
    assert articles[79].article_title.endswith("lợi ích quốc gia, công cộng")
    assert articles[93].article_title.endswith("đối với dự án đầu tư")
    assert articles[93].article_text.startswith("Trường hợp dự án")
    assert articles[106].article_text.startswith("Khi xây dựng")
    assert articles[117].article_text.startswith("Việc quyết định giao đất")
    assert articles[138].article_text.startswith("Việc cấp Giấy chứng nhận")
    assert articles[140].article_text.startswith("Đất được giao không đúng thẩm quyền")
    assert articles[228].article_text.startswith("Các trường hợp Nhà nước")
    assert articles[230].article_text.startswith("Quốc hội, Mặt trận Tổ quốc")
    assert articles[246].article_text.startswith("Sửa đổi, bổ sung khoản 4")


def main() -> None:
    parser = LegalStructureParser()

    document = parser.parse_file(INPUT_PATH)
    stats = parser.validate(document)
    if stats["suspicious_titles"]:
        raise ValueError(
            f"Còn {stats['suspicious_titles']} tiêu đề Điều đáng ngờ."
        )
    parser.write_json(document, OUTPUT_PATH)

    print("=" * 80)
    print("MODULE 4 - LEGAL STRUCTURE PARSER")
    print("=" * 80)
    print(f"Input file       : {INPUT_PATH}")
    print(f"Output file      : {OUTPUT_PATH}")
    print(f"Chapters         : {stats['chapters']}")
    print(f"Articles         : {stats['articles']}")
    print(f"Clauses          : {stats['clauses']}")
    print(f"Points           : {stats['points']}")
    print(f"Suspicious titles: {stats['suspicious_titles']}")
    print("Status           : SUCCESS")


if __name__ == "__main__":
    main()
