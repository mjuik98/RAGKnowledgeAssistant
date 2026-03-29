from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse
from app.services.pipeline import ask_question_core

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def ask_question(payload: ChatRequest) -> ChatResponse:
    return ask_question_core(question=payload.question, top_k=payload.top_k)
