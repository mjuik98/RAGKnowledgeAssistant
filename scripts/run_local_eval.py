from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import init_db
from app.services.evaluator import SimpleEvaluator
from app.services.pipeline import ask_question_core
from app.services.repository import ChunkRepository
from app.services.retriever import HybridRetriever


def main() -> None:
    parser = argparse.ArgumentParser(description="로컬 평가셋을 실행합니다.")
    parser.add_argument("--eval-file", default="data/eval/eval_template.jsonl", help="평가 JSONL 파일 경로")
    parser.add_argument("--no-save-report", action="store_true", help="평가 리포트를 저장하지 않습니다.")
    args = parser.parse_args()

    init_db()
    retriever = HybridRetriever()
    retriever.rebuild(ChunkRepository().list_all_chunks())

    import app.main as main_module

    main_module.retriever = retriever

    evaluator = SimpleEvaluator()
    result = evaluator.run(
        eval_file_path=args.eval_file,
        ask_fn=lambda question: ask_question_core(question=question, top_k=5).model_dump(),
        save_report=not args.no_save_report,
    )

    retriever_info = retriever.describe()
    print(f"평가셋: {result.eval_name}")
    print(f"- 문항 수: {result.total_count}")
    print(f"- Dense backend:       {retriever_info['dense_backend']}")
    print(f"- Dense model:         {retriever_info['dense_model_name']}")
    print(f"- Retrieval Hit Rate:  {result.retrieval_hit_rate:.2%}")
    print(f"- Keyword Hit Rate:    {result.keyword_hit_rate:.2%}")
    if result.citation_hit_rate is not None:
        print(f"- Citation Hit Rate:   {result.citation_hit_rate:.2%}")
    if result.no_answer_accuracy is not None:
        print(f"- No-answer 정확도:    {result.no_answer_accuracy:.2%}")
    if result.average_latency_ms is not None:
        print(f"- 평균 응답 시간:      {result.average_latency_ms:.2f}ms")
    if result.report_path:
        print(f"- JSON 리포트 경로:    {result.report_path}")
    if result.html_report_path:
        print(f"- HTML 리포트 경로:    {result.html_report_path}")


if __name__ == "__main__":
    main()
