from __future__ import annotations

from fastapi import FastAPI

from app.api.analytics import router as analytics_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.evals import router as evals_router
from app.api.feedback import router as feedback_router
from app.api.system import router as system_router
from app.core.config import get_settings
from app.core.database import init_db
from app.models.schemas import HealthResponse
from app.services.repository import ChunkRepository
from app.services.retriever import HybridRetriever

settings = get_settings()
app = FastAPI(title=settings.app_name)

retriever = HybridRetriever()


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    chunk_repo = ChunkRepository()
    retriever.rebuild(chunk_repo.list_all_chunks())


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", app_name=settings.app_name)


app.include_router(documents_router)
app.include_router(analytics_router)
app.include_router(chat_router)
app.include_router(evals_router)
app.include_router(feedback_router)
app.include_router(system_router)
