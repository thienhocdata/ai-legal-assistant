from __future__ import annotations

from datetime import date
import re
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


ProcessingStatus = Literal[
    "metadata_created",
    "pending",
    "downloaded",
    "parsed",
    "structure_extracted",
    "chunked",
    "embedded",
    "indexed",
    "failed",
]

LegalStatus = Literal[
    "unknown",
    "in_force",
    "expired",
    "partially_expired",
    "amended",
    "reference",
]


class DocumentRelations(BaseModel):
    amended_by: list[str] = Field(default_factory=list)
    amends: list[str] = Field(default_factory=list)
    replaces: list[str] = Field(default_factory=list)
    replaced_by: list[str] = Field(default_factory=list)
    related_documents: list[str] = Field(default_factory=list)


class SourceFile(BaseModel):
    path: str
    source_url: str
    sha256: str
    content_length: int = Field(gt=0)
    role: Literal["official", "derived"] = "official"
    derived_from: str | None = None

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        normalized = value.lower()
        if not re.fullmatch(r"[0-9a-f]{64}", normalized):
            raise ValueError("sha256 must contain exactly 64 hexadecimal characters")
        return normalized


class DocumentSource(BaseModel):
    source_type: str
    source_name: str = ""
    source_url: str = ""
    raw_file_path: str
    sha256: str | None = None
    hash_method: str | None = None
    files: list[SourceFile] = Field(default_factory=list)


class DocumentProcessing(BaseModel):
    processing_status: ProcessingStatus
    parser: str | None = None
    chunk_strategy: str | None = None
    embedding_model: str | None = None
    indexed: bool = False
    last_processed_at: str | None = None
    experimental_status: ProcessingStatus | None = None
    experimental_artifact_path: str | None = None


class DocumentMetadata(BaseModel):
    document_id: str
    document_title: str
    document_number: str = ""
    document_type: str
    version: str = "1.0"
    language: str = "vi"

    issuing_authority: str = ""
    issued_date: str = ""
    original_effective_date: str = ""
    current_effective_date: str = ""
    expiry_date: str | None = None
    legal_status: LegalStatus = "unknown"

    scope: str = ""
    jurisdiction: str = "Việt Nam"
    legal_domain: str = "Đất đai"
    tags: list[str] = Field(default_factory=list)

    relations: DocumentRelations
    source: DocumentSource
    processing: DocumentProcessing

    notes: str = ""

    @field_validator("document_id")
    @classmethod
    def validate_document_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("document_id không được để trống")
        if " " in value:
            raise ValueError("document_id không nên chứa khoảng trắng")
        return value

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("tags không được để trống")
        return value


    @field_validator(
        "issued_date",
        "original_effective_date",
        "current_effective_date",
    )
    @classmethod
    def validate_iso_date(cls, value: str) -> str:
        if value:
            date.fromisoformat(value)
        return value


class SourceInventoryRow(BaseModel):
    source_id: str
    document_id: str
    document_title: str
    document_number: str = ""
    document_type: str
    official_source: str
    source_url: str = ""
    source_type: str
    expected_format: str
    raw_target_path: str
    metadata_path: str
    priority: int | str = 1
    language: str = "vi"
    jurisdiction: str = "Việt Nam"
    crawl_status: str = "pending"
    crawl_date: str = ""
    last_checked_at: str = ""
    document_hash: str = ""
    content_length: str = ""
    error_message: str = ""
    notes: str = ""

    @field_validator("source_id", "document_id", "raw_target_path", "metadata_path")
    @classmethod
    def not_empty(cls, value: str) -> str:
        if not str(value).strip():
            raise ValueError("Trường bắt buộc không được để trống")
        return str(value)
