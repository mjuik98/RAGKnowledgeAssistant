from __future__ import annotations

import time

from app.models.schemas import ChatResponse
from app.services.generator import ExtractiveAnswerGenerator
from app.services.guard import QueryGuard
from app.services.repository import QueryRepository


generator = ExtractiveAnswerGenerator()
guard = QueryGuard()
query_repo = QueryRepository()


def ask_question_core(question: str, top_k: int = 5) -> ChatResponse:
    from app.main import retriever  # 순환 참조 방지용 로컬 import

    started_at = time.perf_counter()
    guard_decision = guard.inspect(question)

    if guard_decision.blocked:
        latency_ms = (time.perf_counter() - started_at) * 1000
        query_id = query_repo.create_query_log(
            question=question,
            normalized_question=question.strip().lower(),
            answer=guard_decision.message or "질문을 처리할 수 없습니다.",
            status=guard_decision.status,
            latency_ms=latency_ms,
        )
        return ChatResponse(
            answer=guard_decision.message or "질문을 처리할 수 없습니다.",
            status=guard_decision.status,
            citations=[],
            retrieved_chunks=[],
            latency_ms=round(latency_ms, 2),
            query_id=query_id,
            guard_reason=guard_decision.reason,
        )

    retrieved_chunks = retriever.search(question, top_k=top_k)
    answer, status, citations = generator.generate(question, retrieved_chunks)
    latency_ms = (time.perf_counter() - started_at) * 1000

    query_id = query_repo.create_query_log(
        question=question,
        normalized_question=question.strip().lower(),
        answer=answer,
        status=status,
        latency_ms=latency_ms,
    )
    query_repo.insert_retrieval_logs(
        query_id=query_id,
        retrievals=[
            {
                "chunk_id": item.chunk_id,
                "score": item.score,
                "rank": item.rank,
                "stage": item.metadata.get("retrieval_mode", "retrieve"),
            }
            for item in retrieved_chunks
        ],
    )

    return ChatResponse(
        answer=answer,
        status=status,
        citations=citations,
        retrieved_chunks=retrieved_chunks,
        latency_ms=round(latency_ms, 2),
        query_id=query_id,
        guard_reason=None,
    )
