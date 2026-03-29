from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import EvalRunRequest, EvalRunResponse
from app.services.evaluator import SimpleEvaluator
from app.services.pipeline import ask_question_core
from app.services.repository import EvalRepository

router = APIRouter(prefix="/evals", tags=["evals"])

evaluator = SimpleEvaluator()
eval_repo = EvalRepository()


@router.post("/run", response_model=EvalRunResponse)
def run_eval(payload: EvalRunRequest) -> EvalRunResponse:
    def _ask_fn(question: str) -> dict:
        response = ask_question_core(question=question)
        return response.model_dump()

    try:
        result = evaluator.run(
            eval_file_path=payload.eval_file_path,
            ask_fn=_ask_fn,
            save_report=payload.save_report,
        )
        eval_run_id = eval_repo.create_eval_run(
            eval_name=result.eval_name,
            eval_file_path=payload.eval_file_path,
            total_count=result.total_count,
            retrieval_hit_rate=result.retrieval_hit_rate,
            keyword_hit_rate=result.keyword_hit_rate,
            citation_hit_rate=result.citation_hit_rate,
            no_answer_accuracy=result.no_answer_accuracy,
            average_latency_ms=result.average_latency_ms,
            report_path=result.report_path,
        )
        eval_repo.insert_eval_results(
            eval_run_id=eval_run_id,
            results=[
                {
                    "question": item.question,
                    "reference_answer": None,
                    "predicted_answer": item.predicted_answer,
                    "retrieval_hit": item.retrieval_hit,
                    "keyword_hit": item.keyword_hit,
                    "notes": item.notes,
                }
                for item in result.results
            ],
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"평가 실행 중 오류가 발생했습니다: {exc}") from exc
