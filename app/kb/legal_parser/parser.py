from __future__ import annotations

from pathlib import Path
import json
import re

from .models import (
    Article,
    Chapter,
    Clause,
    LegalDocument,
    Point,
    Section,
)


class LegalStructureParser:
    EXPECTED_ARTICLES = 260

    CHAPTER_RE = re.compile(r"^Chương\s+([IVXLCDM]+)\s*$", re.IGNORECASE)
    SECTION_RE = re.compile(r"^Mục\s+(\d+)\s*$", re.IGNORECASE)
    ARTICLE_RE = re.compile(r"^Điều\s+(\d+)\.\s*(.*)$", re.IGNORECASE)
    CLAUSE_RE = re.compile(r"^(\d+)\.\s+(.*)$")
    POINT_RE = re.compile(r"^([a-zđ])\)\s+(.*)$", re.IGNORECASE)
    BODY_START_RE = re.compile(
        r"\s+(?=(?:Trong Luật này\b|(?<!khi )Nhà nước thu hồi\b|"
        r"Trường hợp dự án\b|Khi xây dựng\b|Đất được giao\b|"
        r"Các trường hợp Nhà nước\b|Việc\b|"
        r"Hộ gia đình, cá nhân đang sử dụng đất, tài sản\b|"
        r"Sửa đổi, bổ sung\b))"
    )
    INCOMPLETE_TITLE_RE = re.compile(
        r"\b(?:của|được|trước|với|về|do)$",
        re.IGNORECASE,
    )

    @classmethod
    def _split_title_and_body(cls, value: str) -> tuple[str, str]:
        """Split a title accidentally joined with its opening legal sentence."""
        clean = " ".join(value.split()).strip()

        # Some provisions repeat the title subject as the opening sentence.
        # Split at the second occurrence, never at the subject inside the title.
        repeated_marker = "Quốc hội, Mặt trận Tổ quốc Việt Nam"
        first = clean.find(repeated_marker)
        if first >= 0:
            second = clean.find(repeated_marker, first + len(repeated_marker))
            if second > first:
                return clean[:second].strip(), clean[second:].strip()

        match = cls.BODY_START_RE.search(clean)
        if match is None:
            return clean, ""
        return clean[: match.start()].strip(), clean[match.end() :].strip()

    def parse_file(self, input_path: str | Path) -> LegalDocument:
        path = Path(input_path)

        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy file đầu vào: {path}")

        text = path.read_text(encoding="utf-8")
        return self.parse_text(text, source_file=str(path))

    def parse_text(self, text: str, *, source_file: str) -> LegalDocument:
        document = LegalDocument(
            document_id="luat_dat_dai_2024",
            document_number="31/2024/QH15",
            document_name="Luật Đất đai 2024",
            document_type="Luật",
            source_file=source_file,
        )

        current_chapter: Chapter | None = None
        current_section: Section | None = None
        current_article: Article | None = None
        current_clause: Clause | None = None
        current_point: Point | None = None

        chapter_title_buffer: list[str] = []
        section_title_buffer: list[str] = []
        article_body_buffer: list[str] = []

        pending_chapter_title = False
        pending_section_title = False

        def finalize_chapter_title() -> None:
            nonlocal chapter_title_buffer, pending_chapter_title
            if current_chapter is not None and chapter_title_buffer:
                current_chapter.chapter_title = " ".join(chapter_title_buffer).strip()
            chapter_title_buffer = []
            pending_chapter_title = False

        def finalize_section_title() -> None:
            nonlocal section_title_buffer, pending_section_title
            if current_section is not None and section_title_buffer:
                current_section.section_title = " ".join(section_title_buffer).strip()
            section_title_buffer = []
            pending_section_title = False

        def finalize_article_body() -> None:
            nonlocal article_body_buffer
            if current_article is not None:
                body = " ".join(article_body_buffer).strip()

                # PDF line wrapping can leave the tail of a long title on the
                # line before Khoản 1. A lowercase first word is a strong signal
                # that this is a title continuation, not a new legal sentence.
                first_alpha = next((char for char in body if char.isalpha()), "")
                if body and first_alpha and first_alpha.islower():
                    combined = f"{current_article.article_title} {body}".strip()
                    complete_title, body_remainder = self._split_title_and_body(
                        combined
                    )
                    current_article.article_title = complete_title
                    body = body_remainder

                current_article.article_text = body
            article_body_buffer = []

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            chapter_match = self.CHAPTER_RE.match(line)
            section_match = self.SECTION_RE.match(line)
            article_match = self.ARTICLE_RE.match(line)
            clause_match = self.CLAUSE_RE.match(line)
            point_match = self.POINT_RE.match(line)

            if pending_chapter_title and not (
                chapter_match or section_match or article_match
            ):
                chapter_title_buffer.append(line)
                continue

            if pending_section_title and not (
                chapter_match or section_match or article_match
            ):
                section_title_buffer.append(line)
                continue

            if chapter_match:
                finalize_chapter_title()
                finalize_section_title()
                finalize_article_body()

                current_chapter = Chapter(
                    chapter_no=chapter_match.group(1).upper()
                )
                document.chapters.append(current_chapter)

                current_section = None
                current_article = None
                current_clause = None
                current_point = None

                pending_chapter_title = True
                continue

            if section_match:
                if current_chapter is None:
                    raise ValueError("Mục xuất hiện trước Chương.")

                finalize_chapter_title()
                finalize_section_title()
                finalize_article_body()

                current_section = Section(
                    section_no=section_match.group(1),
                    chapter_no=current_chapter.chapter_no,
                    chapter_title=current_chapter.chapter_title,
                )
                current_chapter.sections.append(current_section)

                current_article = None
                current_clause = None
                current_point = None

                pending_section_title = True
                continue

            if article_match:
                if current_chapter is None:
                    raise ValueError("Điều xuất hiện trước Chương.")

                finalize_chapter_title()
                finalize_section_title()
                finalize_article_body()

                article_title, opening_body = self._split_title_and_body(
                    article_match.group(2)
                )

                current_article = Article(
                    article_no=article_match.group(1),
                    article_title=article_title,
                    chapter_no=current_chapter.chapter_no,
                    chapter_title=current_chapter.chapter_title,
                    section_no=(
                        current_section.section_no
                        if current_section is not None
                        else ""
                    ),
                    section_title=(
                        current_section.section_title
                        if current_section is not None
                        else ""
                    ),
                )

                if current_section is not None:
                    current_section.articles.append(current_article)
                else:
                    current_chapter.articles.append(current_article)

                current_clause = None
                current_point = None
                if opening_body:
                    article_body_buffer.append(opening_body)
                continue

            if clause_match and current_article is not None:
                current_clause = Clause(
                    clause_no=clause_match.group(1),
                    clause_text=clause_match.group(2).strip(),
                    chapter_no=current_article.chapter_no,
                    chapter_title=current_article.chapter_title,
                    section_no=current_article.section_no,
                    section_title=current_article.section_title,
                    article_no=current_article.article_no,
                    article_title=current_article.article_title,
                )
                current_article.clauses.append(current_clause)
                current_point = None
                continue

            if point_match and current_clause is not None:
                current_point = Point(
                    point_no=point_match.group(1).lower(),
                    point_text=point_match.group(2).strip(),
                    chapter_no=current_clause.chapter_no,
                    chapter_title=current_clause.chapter_title,
                    section_no=current_clause.section_no,
                    section_title=current_clause.section_title,
                    article_no=current_clause.article_no,
                    article_title=current_clause.article_title,
                    clause_no=current_clause.clause_no,
                )
                current_clause.points.append(current_point)
                continue

            if current_point is not None:
                current_point.point_text = (
                    f"{current_point.point_text} {line}".strip()
                )
                continue

            if current_clause is not None:
                current_clause.clause_text = (
                    f"{current_clause.clause_text} {line}".strip()
                )
                continue

            if current_article is not None:
                article_body_buffer.append(line)

        finalize_chapter_title()
        finalize_section_title()
        finalize_article_body()

        return document

    def collect_articles(self, document: LegalDocument) -> list[Article]:
        articles: list[Article] = []

        for chapter in document.chapters:
            articles.extend(chapter.articles)

            for section in chapter.sections:
                articles.extend(section.articles)

        return sorted(articles, key=lambda item: int(item.article_no))

    def validate(self, document: LegalDocument) -> dict[str, int]:
        articles = self.collect_articles(document)
        article_numbers = [int(article.article_no) for article in articles]
        expected = list(range(1, self.EXPECTED_ARTICLES + 1))

        if len(articles) != self.EXPECTED_ARTICLES:
            raise ValueError(
                f"Dự kiến {self.EXPECTED_ARTICLES} Điều, "
                f"nhưng nhận được {len(articles)}."
            )

        if article_numbers != expected:
            missing = sorted(set(expected) - set(article_numbers))
            duplicated = sorted(
                number
                for number in set(article_numbers)
                if article_numbers.count(number) > 1
            )
            raise ValueError(
                f"Số Điều không liên tục. Thiếu: {missing}; trùng: {duplicated}."
            )

        empty_titles = [
            article.article_no
            for article in articles
            if not article.article_title.strip()
        ]

        if empty_titles:
            raise ValueError(f"Có Điều thiếu tiêu đề: {empty_titles}")

        suspicious_titles = []
        for article in articles:
            title = article.article_title.strip()
            has_embedded_body = self.BODY_START_RE.search(title) is not None
            if (
                title.endswith((",", ";", ":"))
                or self.INCOMPLETE_TITLE_RE.search(title)
                or has_embedded_body
                or len(title) > 500
            ):
                suspicious_titles.append(article.article_no)

        clause_count = sum(len(article.clauses) for article in articles)
        point_count = sum(
            len(clause.points)
            for article in articles
            for clause in article.clauses
        )

        return {
            "chapters": len(document.chapters),
            "articles": len(articles),
            "clauses": clause_count,
            "points": point_count,
            "suspicious_titles": len(suspicious_titles),
        }

    def write_json(
        self,
        document: LegalDocument,
        output_path: str | Path,
    ) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(document.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path
