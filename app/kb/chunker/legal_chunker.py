from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Any

from .models import LegalChunk, LegalChunkMetadata


class LegalChunker:
    """
    Legal-boundary-first chunker.

    Thứ tự ưu tiên:
    Điều -> Khoản -> Điểm -> câu -> ký tự.

    max_chars là hard limit: không chunk nào được phép vượt giới hạn.
    """

    def __init__(
        self,
        *,
        max_chars: int = 5000,
        overlap_chars: int = 200,
    ) -> None:
        if max_chars < 500:
            raise ValueError("max_chars phải từ 500 trở lên.")
        if overlap_chars < 0:
            raise ValueError("overlap_chars không được âm.")
        if overlap_chars >= max_chars:
            raise ValueError(
                "overlap_chars phải nhỏ hơn max_chars."
            )

        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    @staticmethod
    def load_legal_tree(
        input_path: str | Path,
    ) -> dict[str, Any]:
        path = Path(input_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy legal tree: {path}"
            )

        data = json.loads(path.read_text(encoding="utf-8"))

        if not isinstance(data, dict):
            raise ValueError("Legal tree phải là JSON object.")

        return data

    @staticmethod
    def normalize_text(text: str) -> str:
        text = re.sub(r"\s+", " ", str(text))
        text = re.sub(r"\s+([,.;:!?])", r"\1", text)
        text = re.sub(r"\(\s+", "(", text)
        text = re.sub(r"\s+\)", ")", text)
        return text.strip()

    @staticmethod
    def _namespace(document: dict[str, Any]) -> str:
        source = (
            document.get("document_id")
            or document.get("document_number")
            or "document"
        )

        namespace = re.sub(
            r"[^0-9A-Za-z]+",
            "_",
            str(source),
        ).strip("_").lower()

        return namespace or "document"

    @staticmethod
    def _safe_int(
        value: Any,
        *,
        default: int = 0,
    ) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _section_no(
        section: dict[str, Any] | None,
    ) -> int | None:
        if section is None:
            return None

        value = section.get("section_no")
        if value in (None, ""):
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def collect_articles(
        self,
        document: dict[str, Any],
    ) -> list[
        tuple[
            dict[str, Any],
            dict[str, Any],
            dict[str, Any] | None,
        ]
    ]:
        collected = []

        for chapter in document.get("chapters", []):
            for article in chapter.get("articles", []):
                collected.append((article, chapter, None))

            for section in chapter.get("sections", []):
                for article in section.get("articles", []):
                    collected.append(
                        (article, chapter, section)
                    )

        collected.sort(
            key=lambda item: self._safe_int(
                item[0].get("article_no")
            )
        )

        return collected

    @staticmethod
    def _article_header(
        article: dict[str, Any],
    ) -> str:
        article_no = article.get("article_no", "")
        article_title = article.get("article_title", "")

        return (
            f"Điều {article_no}. {article_title}"
        ).strip()

    @staticmethod
    def _context_header(
        chapter: dict[str, Any],
        section: dict[str, Any] | None,
        article: dict[str, Any],
    ) -> str:
        lines = []

        chapter_no = chapter.get("chapter_no", "")
        chapter_title = chapter.get("chapter_title", "")
        if chapter_no or chapter_title:
            lines.append(
                f"Chương {chapter_no}. {chapter_title}".strip()
            )

        if section is not None:
            section_no = section.get("section_no", "")
            section_title = section.get("section_title", "")
            lines.append(
                f"Mục {section_no}. {section_title}".strip()
            )

        lines.append(
            LegalChunker._article_header(article)
        )

        return "\n".join(
            line for line in lines if line.strip()
        )

    @staticmethod
    def _point_text(point: dict[str, Any]) -> str:
        point_no = str(point.get("point_no", "")).strip()
        point_text = str(point.get("point_text", "")).strip()

        if point_no:
            return f"{point_no}) {point_text}".strip()

        return point_text

    @staticmethod
    def _clause_header(
        clause: dict[str, Any],
    ) -> str:
        clause_no = str(clause.get("clause_no", "")).strip()
        clause_text = str(clause.get("clause_text", "")).strip()

        if clause_no:
            return f"{clause_no}. {clause_text}".strip()

        return clause_text

    def _clause_text(
        self,
        clause: dict[str, Any],
    ) -> str:
        lines = [self._clause_header(clause)]

        for point in clause.get("points", []):
            lines.append(self._point_text(point))

        return "\n".join(
            line for line in lines if line.strip()
        )

    def _full_article_text(
        self,
        article: dict[str, Any],
    ) -> str:
        lines = [self._article_header(article)]

        article_text = str(
            article.get("article_text", "")
        ).strip()

        if article_text:
            lines.append(article_text)

        for clause in article.get("clauses", []):
            lines.append(self._clause_text(clause))

        return "\n".join(
            line for line in lines if line.strip()
        )

    def _fits(
        self,
        text: str,
    ) -> bool:
        return len(self.normalize_text(text)) <= self.max_chars

    def _join_context(
        self,
        context: str,
        body: str,
    ) -> str:
        if body.strip():
            return f"{context}\n{body}".strip()
        return context.strip()

    def _sentence_units(
        self,
        text: str,
    ) -> list[str]:
        clean = self.normalize_text(text)

        if not clean:
            return []

        parts = re.split(
            r"(?<=[.!?;:])\s+",
            clean,
        )

        return [
            part.strip()
            for part in parts
            if part.strip()
        ]

    def _hard_split_body(
        self,
        body: str,
        *,
        context: str,
    ) -> list[str]:
        """
        Fallback cuối cùng.

        Ưu tiên gom theo câu. Nếu một câu vẫn quá dài thì cắt theo
        cửa sổ ký tự. Mỗi phần đầu ra luôn <= max_chars.
        """
        context_clean = self.normalize_text(context)
        body_clean = self.normalize_text(body)

        separator = " "
        budget = (
            self.max_chars
            - len(context_clean)
            - len(separator)
        )

        if budget < 100:
            raise ValueError(
                "Context pháp lý quá dài so với max_chars."
            )

        sentences = self._sentence_units(body_clean)
        sentence_groups: list[str] = []
        current: list[str] = []

        def flush_current() -> None:
            nonlocal current

            if current:
                sentence_groups.append(
                    " ".join(current).strip()
                )
                current = []

        for sentence in sentences:
            if len(sentence) <= budget:
                candidate = " ".join(
                    current + [sentence]
                ).strip()

                if current and len(candidate) > budget:
                    flush_current()

                current.append(sentence)
                continue

            flush_current()

            step = max(
                1,
                budget - min(
                    self.overlap_chars,
                    max(0, budget // 5),
                ),
            )

            start = 0
            while start < len(sentence):
                end = min(start + budget, len(sentence))
                piece = sentence[start:end].strip()

                if piece:
                    sentence_groups.append(piece)

                if end >= len(sentence):
                    break

                start += step

        flush_current()

        results = []

        for group in sentence_groups:
            combined = self.normalize_text(
                f"{context_clean}{separator}{group}"
            )

            if len(combined) > self.max_chars:
                allowed = self.max_chars - len(
                    context_clean
                ) - len(separator)

                group = group[:allowed].rstrip()
                combined = self.normalize_text(
                    f"{context_clean}{separator}{group}"
                )

            if not combined:
                continue

            if len(combined) > self.max_chars:
                raise ValueError(
                    "Hard limit thất bại khi chia fallback."
                )

            results.append(combined)

        if not results:
            raise ValueError(
                "Không tạo được fallback chunk."
            )

        return results

    def _split_point(
        self,
        point: dict[str, Any],
        *,
        context: str,
        clause_header: str,
        clause_no: int,
    ) -> list[dict[str, Any]]:
        point_no = str(
            point.get("point_no", "")
        ).strip()

        body = (
            f"{clause_header}\n"
            f"{self._point_text(point)}"
        ).strip()

        full = self._join_context(
            context,
            body,
        )

        if self._fits(full):
            return [
                {
                    "text": full,
                    "strategy": "point",
                    "clause_nos": [clause_no],
                    "point_nos": [point_no]
                    if point_no
                    else [],
                }
            ]

        pieces = self._hard_split_body(
            body,
            context=context,
        )

        return [
            {
                "text": piece,
                "strategy": "sentence_fallback",
                "clause_nos": [clause_no],
                "point_nos": [point_no]
                if point_no
                else [],
            }
            for piece in pieces
        ]

    def _split_clause(
        self,
        clause: dict[str, Any],
        *,
        context: str,
    ) -> list[dict[str, Any]]:
        clause_no = self._safe_int(
            clause.get("clause_no")
        )
        clause_text = self._clause_text(clause)
        full = self._join_context(
            context,
            clause_text,
        )

        if self._fits(full):
            return [
                {
                    "text": full,
                    "strategy": "clause",
                    "clause_nos": [clause_no]
                    if clause_no
                    else [],
                    "point_nos": [
                        str(point.get("point_no", "")).strip()
                        for point in clause.get("points", [])
                        if str(
                            point.get("point_no", "")
                        ).strip()
                    ],
                }
            ]

        points = clause.get("points", [])
        if points:
            clause_header = self._clause_header(
                clause
            )
            parts = []

            for point in points:
                parts.extend(
                    self._split_point(
                        point,
                        context=context,
                        clause_header=clause_header,
                        clause_no=clause_no,
                    )
                )

            return parts

        pieces = self._hard_split_body(
            clause_text,
            context=context,
        )

        return [
            {
                "text": piece,
                "strategy": "sentence_fallback",
                "clause_nos": [clause_no]
                if clause_no
                else [],
                "point_nos": [],
            }
            for piece in pieces
        ]

    def _split_article(
        self,
        chapter: dict[str, Any],
        section: dict[str, Any] | None,
        article: dict[str, Any],
    ) -> list[dict[str, Any]]:
        context = self._context_header(
            chapter,
            section,
            article,
        )
        full_article = self._full_article_text(article)

        if self._fits(full_article):
            return [
                {
                    "text": full_article,
                    "strategy": "article",
                    "clause_nos": [
                        self._safe_int(
                            clause.get("clause_no")
                        )
                        for clause in article.get(
                            "clauses",
                            [],
                        )
                        if self._safe_int(
                            clause.get("clause_no")
                        )
                    ],
                    "point_nos": [
                        str(point.get("point_no", "")).strip()
                        for clause in article.get(
                            "clauses",
                            [],
                        )
                        for point in clause.get(
                            "points",
                            [],
                        )
                        if str(
                            point.get("point_no", "")
                        ).strip()
                    ],
                }
            ]

        parts: list[dict[str, Any]] = []

        article_text = str(
            article.get("article_text", "")
        ).strip()

        if article_text:
            intro = self._join_context(
                context,
                article_text,
            )

            if self._fits(intro):
                parts.append(
                    {
                        "text": intro,
                        "strategy": "article_intro",
                        "clause_nos": [],
                        "point_nos": [],
                    }
                )
            else:
                for piece in self._hard_split_body(
                    article_text,
                    context=context,
                ):
                    parts.append(
                        {
                            "text": piece,
                            "strategy": "sentence_fallback",
                            "clause_nos": [],
                            "point_nos": [],
                        }
                    )

        clauses = article.get("clauses", [])

        for clause in clauses:
            parts.extend(
                self._split_clause(
                    clause,
                    context=context,
                )
            )

        if not parts:
            for piece in self._hard_split_body(
                full_article,
                context=context,
            ):
                parts.append(
                    {
                        "text": piece,
                        "strategy": "sentence_fallback",
                        "clause_nos": [],
                        "point_nos": [],
                    }
                )

        return parts

    def build_chunks(
        self,
        document: dict[str, Any],
    ) -> list[dict[str, Any]]:
        namespace = self._namespace(document)
        output: list[dict[str, Any]] = []

        articles = self.collect_articles(document)

        if not articles:
            raise ValueError(
                "Legal tree không có Điều nào."
            )

        for article, chapter, section in articles:
            article_no = self._safe_int(
                article.get("article_no")
            )

            if article_no <= 0:
                raise ValueError(
                    "Phát hiện article_no không hợp lệ."
                )

            parts = self._split_article(
                chapter,
                section,
                article,
            )
            chunk_count = len(parts)

            for chunk_index, part in enumerate(
                parts,
                start=1,
            ):
                clean_text = self.normalize_text(
                    part["text"]
                )

                if not clean_text:
                    raise ValueError(
                        f"Chunk rỗng tại Điều {article_no}."
                    )

                if len(clean_text) > self.max_chars:
                    raise ValueError(
                        "Hard limit bị vi phạm trước khi lưu: "
                        f"Điều {article_no}, "
                        f"chunk {chunk_index}, "
                        f"{len(clean_text)} ký tự."
                    )

                source_path = [
                    namespace,
                    f"chapter_{chapter.get('chapter_no', '')}",
                ]

                if section is not None:
                    source_path.append(
                        f"section_{section.get('section_no', '')}"
                    )

                source_path.append(
                    f"article_{article_no:03d}"
                )

                chunk = LegalChunk(
                    chunk_id=(
                        f"{namespace}_art{article_no:03d}_"
                        f"chunk{chunk_index:03d}"
                    ),
                    document_id=str(
                        document.get("document_id", "")
                    ),
                    document_name=str(
                        document.get("document_name", "")
                    ),
                    article_no=article_no,
                    article_title=str(
                        article.get("article_title", "")
                    ),
                    chapter_no=(
                        str(chapter.get("chapter_no"))
                        if chapter.get("chapter_no")
                        not in (None, "")
                        else None
                    ),
                    chapter_title=(
                        str(chapter.get("chapter_title"))
                        if chapter.get("chapter_title")
                        not in (None, "")
                        else None
                    ),
                    section_no=self._section_no(
                        section
                    ),
                    section_title=(
                        str(section.get("section_title"))
                        if section is not None
                        and section.get("section_title")
                        not in (None, "")
                        else None
                    ),
                    clause_nos=part["clause_nos"],
                    point_nos=part["point_nos"],
                    strategy=part["strategy"],
                    chunk_index=chunk_index,
                    chunk_count=chunk_count,
                    source_node_id=(
                        f"{namespace}_article_"
                        f"{article_no:03d}"
                    ),
                    source_path=source_path,
                    parent_id=(
                        f"{namespace}_article_"
                        f"{article_no:03d}"
                    ),
                    text=part["text"],
                    clean_text=clean_text,
                    char_count=len(clean_text),
                    metadata=LegalChunkMetadata(
                        document_number=document.get(
                            "document_number"
                        ),
                        document_type=document.get(
                            "document_type"
                        ),
                        issued_date=document.get(
                            "issued_date"
                        ),
                        effective_date=document.get(
                            "effective_date"
                        ),
                        source_file=document.get(
                            "source_file"
                        ),
                    ),
                )

                output.append(chunk.to_dict())

        return output

    def validate_chunks(
        self,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not chunks:
            raise ValueError(
                "Không tạo được legal chunk."
            )

        chunk_ids = [
            chunk["chunk_id"]
            for chunk in chunks
        ]

        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError(
                "Phát hiện chunk_id bị trùng."
            )

        articles = self.collect_articles(document)
        expected_articles = {
            self._safe_int(article.get("article_no"))
            for article, _, _ in articles
        }
        expected_articles.discard(0)

        actual_articles = {
            self._safe_int(chunk.get("article_no"))
            for chunk in chunks
        }
        actual_articles.discard(0)

        missing_articles = sorted(
            expected_articles - actual_articles
        )
        unexpected_articles = sorted(
            actual_articles - expected_articles
        )

        if missing_articles:
            raise ValueError(
                f"Thiếu chunk cho các Điều: "
                f"{missing_articles}"
            )

        if unexpected_articles:
            raise ValueError(
                f"Có Điều không tồn tại trong tree: "
                f"{unexpected_articles}"
            )

        empty_chunks = []
        oversized_chunks = []
        metadata_errors = []

        by_article: dict[
            int,
            list[dict[str, Any]]
        ] = {}

        for chunk in chunks:
            clean_text = str(
                chunk.get("clean_text", "")
            ).strip()
            chunk_id = str(
                chunk.get("chunk_id", "")
            )

            if not clean_text:
                empty_chunks.append(chunk_id)

            if len(clean_text) > self.max_chars:
                oversized_chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "article_no": chunk.get(
                            "article_no"
                        ),
                        "length": len(clean_text),
                        "strategy": chunk.get(
                            "strategy"
                        ),
                    }
                )

            article_no = self._safe_int(
                chunk.get("article_no")
            )

            if article_no <= 0:
                metadata_errors.append(
                    f"{chunk_id}: article_no không hợp lệ"
                )

            if not str(
                chunk.get("article_title", "")
            ).strip():
                metadata_errors.append(
                    f"{chunk_id}: thiếu article_title"
                )

            by_article.setdefault(
                article_no,
                [],
            ).append(chunk)

        if empty_chunks:
            raise ValueError(
                f"Có chunk rỗng: "
                f"{empty_chunks[:10]}"
            )

        if oversized_chunks:
            raise ValueError(
                f"Có {len(oversized_chunks)} chunk "
                f"vượt max_chars: "
                f"{oversized_chunks[:10]}"
            )

        if metadata_errors:
            raise ValueError(
                f"Lỗi metadata: "
                f"{metadata_errors[:10]}"
            )

        for article_no, article_chunks in by_article.items():
            indexes = sorted(
                self._safe_int(
                    chunk.get("chunk_index")
                )
                for chunk in article_chunks
            )
            expected_indexes = list(
                range(1, len(article_chunks) + 1)
            )

            if indexes != expected_indexes:
                raise ValueError(
                    f"chunk_index Điều {article_no} "
                    "không liên tục."
                )

            chunk_counts = {
                self._safe_int(
                    chunk.get("chunk_count")
                )
                for chunk in article_chunks
            }

            if chunk_counts != {
                len(article_chunks)
            }:
                raise ValueError(
                    f"chunk_count Điều {article_no} "
                    "không nhất quán."
                )

        lengths = [
            len(chunk["clean_text"])
            for chunk in chunks
        ]

        strategies: dict[str, int] = {}
        for chunk in chunks:
            strategy = str(
                chunk.get("strategy", "")
            )
            strategies[strategy] = (
                strategies.get(strategy, 0) + 1
            )

        return {
            "articles": len(actual_articles),
            "chunks": len(chunks),
            "average_length": sum(lengths) / len(lengths),
            "shortest_length": min(lengths),
            "longest_length": max(lengths),
            "oversized_chunks": 0,
            "empty_chunks": 0,
            "duplicate_ids": 0,
            "strategies": strategies,
        }

    @staticmethod
    def write_json(
        chunks: list[dict[str, Any]],
        output_path: str | Path,
    ) -> Path:
        path = Path(output_path)
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            json.dumps(
                chunks,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return path
