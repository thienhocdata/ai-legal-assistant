from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Point:
    point_no: str
    point_text: str
    chapter_no: str = ""
    chapter_title: str = ""
    section_no: str = ""
    section_title: str = ""
    article_no: str = ""
    article_title: str = ""
    clause_no: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Clause:
    clause_no: str
    clause_text: str
    chapter_no: str = ""
    chapter_title: str = ""
    section_no: str = ""
    section_title: str = ""
    article_no: str = ""
    article_title: str = ""
    points: list[Point] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Article:
    article_no: str
    article_title: str
    chapter_no: str = ""
    chapter_title: str = ""
    section_no: str = ""
    section_title: str = ""
    article_text: str = ""
    clauses: list[Clause] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Section:
    section_no: str
    section_title: str = ""
    chapter_no: str = ""
    chapter_title: str = ""
    articles: list[Article] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Chapter:
    chapter_no: str
    chapter_title: str = ""
    articles: list[Article] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class LegalDocument:
    document_id: str
    document_number: str
    document_name: str
    document_type: str
    source_file: str
    chapters: list[Chapter] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
