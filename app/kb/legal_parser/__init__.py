"""Module 4 - Legal Structure Parser."""

from .models import (
    Article,
    Chapter,
    Clause,
    LegalDocument,
    Point,
    Section,
)
from .parser import LegalStructureParser

__all__ = [
    "Article",
    "Chapter",
    "Clause",
    "LegalDocument",
    "Point",
    "Section",
    "LegalStructureParser",
]
