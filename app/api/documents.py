from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.models.schemas import IngestUrlRequest, UploadDocumentResponse
from app.services.ingestion import IngestionService
from app.services.repository import ChunkRepository, DocumentRepository
from app.services.retriever import HybridRetriever

router = APIRouter(prefix="/documents", tags=["documents"])

service = IngestionService()
document_repo = DocumentRepository()
chunk_repo = ChunkRepository()


def refresh_retriever(retriever: HybridRetriever) -> int:
    chunk_dicts = chunk_repo.list_all_chunks()
    retriever.rebuild(chunk_dicts)
    return len(chunk_dicts)


@router.get("")
def list_documents() -> list[dict]:
    return document_repo.list_documents()


@router.post("/upload", response_model=UploadDocumentResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadDocumentResponse:
    settings = get_settings()
    suffix = Path(file.filename).suffix.lower()

    if suffix not in service.parser.supported_suffixes:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다. PDF/TXT/DOCX만 허용됩니다.")

    destination = Path(settings.raw_dir) / file.filename
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = service.ingest_file(destination)
        from app.main import retriever  # 순환 참조 방지용 로컬 import

        refresh_retriever(retriever)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"문서 처리 중 오류가 발생했습니다: {exc}") from exc


@router.post("/ingest-url", response_model=UploadDocumentResponse)
def ingest_document_from_url(payload: IngestUrlRequest) -> UploadDocumentResponse:
    try:
        result = service.ingest_web_url(
            url=str(payload.url),
            title_hint=payload.title_hint,
            filename_hint=payload.filename_hint,
        )
        from app.main import retriever  # 순환 참조 방지용 로컬 import

        refresh_retriever(retriever)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"URL 문서 처리 중 오류가 발생했습니다: {exc}") from exc


@router.post("/reindex")
def reindex_documents() -> dict[str, int | str]:
    try:
        from app.main import retriever  # 순환 참조 방지용 로컬 import

        chunk_count = refresh_retriever(retriever)
        return {"status": "ok", "chunk_count": chunk_count}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"인덱스 재구성 중 오류가 발생했습니다: {exc}") from exc
