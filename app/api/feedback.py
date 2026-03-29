from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import FeedbackRequest, FeedbackResponse
from app.services.repository import FeedbackRepository, QueryRepository

router = APIRouter(prefix="/feedback", tags=["feedback"])

feedback_repo = FeedbackRepository()
query_repo = QueryRepository()


@router.post("", response_model=FeedbackResponse)
def create_feedback(payload: FeedbackRequest) -> FeedbackResponse:
    query_row = query_repo.get_query_by_id(payload.query_id)
    if not query_row:
        raise HTTPException(status_code=404, detail="해당 query_id를 찾을 수 없습니다.")

    feedback_id = feedback_repo.create_feedback(
        query_id=payload.query_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    return FeedbackResponse(status="ok", feedback_id=feedback_id)
