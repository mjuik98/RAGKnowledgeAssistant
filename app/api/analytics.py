from __future__ import annotations

from fastapi import APIRouter, Query

from app.models.schemas import (
    AnalyticsSummaryResponse,
    DocumentUsageItem,
    EvalRunListItem,
    LatestEvalSummary,
    RecentQueryItem,
)
from app.services.repository import ChunkRepository, DocumentRepository, EvalRepository, FeedbackRepository, QueryRepository

router = APIRouter(prefix="/analytics", tags=["analytics"])

document_repo = DocumentRepository()
chunk_repo = ChunkRepository()
query_repo = QueryRepository()
feedback_repo = FeedbackRepository()
eval_repo = EvalRepository()


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_summary() -> AnalyticsSummaryResponse:
    status_counts = query_repo.count_by_status()
    feedback_stats = feedback_repo.summarize_feedback()
    latest_eval_row = eval_repo.get_latest_eval_run()
    latest_eval = LatestEvalSummary(**latest_eval_row) if latest_eval_row else None

    return AnalyticsSummaryResponse(
        document_count=document_repo.count_documents(),
        chunk_count=chunk_repo.count_chunks(),
        total_queries=query_repo.count_queries(),
        grounded_answer_count=status_counts.get("grounded_answer", 0),
        no_answer_count=status_counts.get("no_answer", 0),
        guard_blocked_count=status_counts.get("guard_blocked", 0),
        average_latency_ms=query_repo.average_latency_ms(),
        feedback_count=feedback_stats["feedback_count"],
        positive_feedback_count=feedback_stats["positive_feedback_count"],
        negative_feedback_count=feedback_stats["negative_feedback_count"],
        neutral_feedback_count=feedback_stats["neutral_feedback_count"],
        latest_eval=latest_eval,
    )


@router.get("/recent-queries", response_model=list[RecentQueryItem])
def get_recent_queries(limit: int = Query(default=20, ge=1, le=100)) -> list[RecentQueryItem]:
    return [RecentQueryItem(**row) for row in query_repo.list_recent_queries(limit=limit)]


@router.get("/eval-runs", response_model=list[EvalRunListItem])
def get_eval_runs(limit: int = Query(default=10, ge=1, le=50)) -> list[EvalRunListItem]:
    return [EvalRunListItem(**row) for row in eval_repo.list_recent_eval_runs(limit=limit)]


@router.get("/document-usage", response_model=list[DocumentUsageItem])
def get_document_usage(limit: int = Query(default=20, ge=1, le=100)) -> list[DocumentUsageItem]:
    return [DocumentUsageItem(**row) for row in document_repo.list_document_usage(limit=limit)]
