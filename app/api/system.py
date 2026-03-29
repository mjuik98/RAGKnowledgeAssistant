from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import IndexInfoResponse
from app.services.repository import ChunkRepository, DocumentRepository

router = APIRouter(prefix="/system", tags=["system"])

document_repo = DocumentRepository()
chunk_repo = ChunkRepository()


@router.get("/index", response_model=IndexInfoResponse)
def get_index_info() -> IndexInfoResponse:
    from app.main import retriever  # 순환 참조 방지용 로컬 import

    detail = retriever.describe()
    return IndexInfoResponse(
        document_count=document_repo.count_documents(),
        chunk_count=chunk_repo.count_chunks(),
        dense_enabled=bool(detail["dense_enabled"]),
        dense_backend=str(detail["dense_backend"]),
        dense_model_name=str(detail["dense_model_name"]),
        dense_encoder_dim=detail.get("dense_encoder_dim"),
        embedding_cache_enabled=bool(detail["embedding_cache_enabled"]),
        embedding_cache_path=detail.get("embedding_cache_path"),
        loaded_from_cache=bool(detail.get("loaded_from_cache", False)),
        fallback_reason=detail.get("fallback_reason"),
    )
