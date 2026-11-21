from __future__ import annotations

from functools import lru_cache
from contextlib import asynccontextmanager, suppress
import asyncio
import json
from pathlib import Path
from threading import Lock
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.services.legal_assistant import LegalAssistantService
from app.services.runtime import RuntimeReadiness


ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "app" / "static"


QuestionText = Annotated[str, StringConstraints(min_length=1, max_length=2000)]
HistoryText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)
]


class ClarificationContext(BaseModel):
    question: QuestionText
    answers: list[QuestionText] = Field(default_factory=list, max_length=3)


class ChatTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: HistoryText


class ChatRequest(BaseModel):
    question: QuestionText
    clarification_context: ClarificationContext | None = None
    conversation_history: list[ChatTurn] | None = Field(default=None, max_length=8)

    @model_validator(mode="after")
    def validate_history_budget(self) -> "ChatRequest":
        if sum(len(turn.content) for turn in self.conversation_history or []) > 12000:
            raise ValueError("Lịch sử hội thoại vượt tổng giới hạn 12000 ký tự.")
        return self


@lru_cache(maxsize=1)
def _cached_service() -> LegalAssistantService:
    return LegalAssistantService()


_SERVICE_LOCK = Lock()


def get_service() -> LegalAssistantService:
    with _SERVICE_LOCK:
        return _cached_service()


@asynccontextmanager
async def lifespan(application: FastAPI):
    readiness = RuntimeReadiness()
    application.state.runtime = readiness
    warmup = asyncio.create_task(run_in_threadpool(readiness.probe, get_service))
    try:
        yield
    finally:
        if not warmup.done():
            warmup.cancel()
        with suppress(asyncio.CancelledError):
            await warmup


app = FastAPI(
    title="AI Legal Assistant - Pháp luật đất đai",
    version="0.1.0",
    description="Tra cứu pháp luật đất đai có truy hồi và trích dẫn căn cứ.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health() -> dict:
    required = [
        ROOT / "data" / "processed" / "legal_chunks.json",
        ROOT / "data" / "processed" / "legal_embeddings_manifest.json",
        ROOT / "data" / "vector_db" / "legal_chunks.faiss",
        ROOT / "data" / "vector_db" / "legal_chunks_metadata.json",
    ]
    manifest_path = ROOT / "data" / "processed" / "legal_embeddings_manifest.json"
    active_document_id = None
    metadata_readable = True
    try:
        if manifest_path.exists():
            active_document_id = json.loads(
                manifest_path.read_text(encoding="utf-8")
            ).get("document_id")
    except (OSError, ValueError, AttributeError):
        metadata_readable = False
    readiness = getattr(app.state, "runtime", None)
    runtime = readiness.snapshot() if readiness else {
        "status": "warming_up", "ready": False, "error_code": None,
        "probe": "startup_not_run", "hosted_provider_live_tested": False,
    }
    artifacts_present = all(path.exists() for path in required)
    if not artifacts_present or not metadata_readable:
        status = "degraded"
    else:
        status = runtime["status"]
    return {
        "status": status,
        "artifacts": {path.name: path.exists() for path in required},
        "metadata_readable": metadata_readable,
        "active_document_id": active_document_id,
        "runtime": runtime,
    }


@app.post("/api/chat")
async def chat(request: ChatRequest) -> dict:
    try:
        service = await run_in_threadpool(get_service)
        return await run_in_threadpool(
            service.answer, request.question,
            clarification_context=(request.clarification_context.model_dump()
                                   if request.clarification_context else None),
            conversation_history=(
                [turn.model_dump() for turn in request.conversation_history]
                if request.conversation_history is not None else None
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Không thể xử lý câu hỏi ở thời điểm hiện tại.",
        ) from exc
