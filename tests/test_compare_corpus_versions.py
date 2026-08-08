from scripts.compare_corpus_versions import (
    build_changed_article_questions,
    compare_articles,
    group_articles,
)


def _chunk(article_no: int, title: str, text: str, index: int = 1) -> dict:
    return {
        "article_no": article_no,
        "article_title": title,
        "chunk_index": index,
        "text": text,
    }


def test_group_articles_ignores_repeated_article_headers_and_whitespace() -> None:
    grouped = group_articles(
        [
            _chunk(1, "Phạm vi", "Điều 1. Phạm vi\nNội dung đầu", 1),
            _chunk(1, "Phạm vi", "Điều 1. Phạm vi\n  nội dung sau", 2),
        ]
    )

    assert grouped[1]["text"] == "Nội dung đầu nội dung sau"
    assert grouped[1]["chunk_count"] == 2


def test_compare_articles_reports_changed_and_new_articles() -> None:
    production = group_articles([_chunk(1, "Cũ", "Điều 1. Cũ\nA")])
    experiment = group_articles(
        [
            _chunk(1, "Mới", "Điều 1. Mới\nB"),
            _chunk(2, "Thêm", "Điều 2. Thêm\nC"),
        ]
    )

    report = compare_articles(production, experiment)

    assert report["changed_article_count"] == 1
    assert report["new_in_experiment"] == [2]
    assert report["changed_articles"][0]["title_changed"] is True
    assert report["changed_articles"][0]["text_changed"] is True

    questions = build_changed_article_questions(report)
    assert questions[0]["expected_article_numbers"] == [1]
    assert questions[0]["question_id"] == "DIFF001"
