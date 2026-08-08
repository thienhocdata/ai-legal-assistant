from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.services.legal_assistant import LegalAssistantService


ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "app" / "static"


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


@lru_cache(maxsize=1)
def get_service() -> LegalAssistantService:
    return LegalAssistantService()


app = FastAPI(
    title="AI Legal Assistant - Pháp luật đất đai",
    version="0.1.0",
    description="Tra cứu pháp luật đất đai có truy hồi và trích dẫn căn cứ.",
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
    ]
    manifest_path = ROOT / "data" / "processed" / "legal_embeddings_manifest.json"
    active_document_id = None
    if manifest_path.exists():
        active_document_id = json.loads(
            manifest_path.read_text(encoding="utf-8")
        ).get("document_id")
    return {
        "status": "ready" if all(path.exists() for path in required) else "degraded",
        "artifacts": {path.name: path.exists() for path in required},
        "active_document_id": active_document_id,
    }


@app.post("/api/chat")
async def chat(request: ChatRequest) -> dict:
    try:
        return await run_in_threadpool(get_service().answer, request.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Không thể xử lý câu hỏi ở thời điểm hiện tại.",
        ) from exc
