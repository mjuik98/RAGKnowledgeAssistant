from __future__ import annotations

import json
import shutil
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import init_db
from app.services.ingestion import IngestionService
from app.services.pipeline import ask_question_core
from app.services.repository import ChunkRepository
from app.services.retriever import HybridRetriever
from scripts.seed_sample_documents import SAMPLE_DOCUMENTS

EVAL_LINE = {
    "question": "전입신고에 필요한 서류가 뭐야?",
    "must_include": ["신분증"],
    "expected_document_titles": ["sample_notice"],
    "expected_no_answer": False,
}


def reset_state() -> None:
    for target in [Path("storage/app.db"), Path("storage/index"), Path("storage/evals"), Path("storage/parsed")]:
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        elif target.exists():
            target.unlink()
    Path("storage/raw").mkdir(parents=True, exist_ok=True)


def main() -> None:
    reset_state()
    init_db()

    raw_dir = Path("storage/raw")
    for filename, content in SAMPLE_DOCUMENTS.items():
        (raw_dir / filename).write_text(content + "\n", encoding="utf-8")

    service = IngestionService()
    for file_path in sorted(raw_dir.glob("*.txt")):
        result = service.ingest_file(file_path)
        print(f"적재 결과: {result.model_dump()}")

    import app.main as main_module

    main_module.retriever = HybridRetriever()
    main_module.retriever.rebuild(ChunkRepository().list_all_chunks())
    print(f"인덱스 정보: {json.dumps(main_module.retriever.describe(), ensure_ascii=False)}")

    grounded_response = ask_question_core("전입신고에 필요한 서류가 뭐야?", top_k=5)
    print("\nGrounded 응답")
    print(json.dumps(grounded_response.model_dump(), ensure_ascii=False, indent=2))

    guard_response = ask_question_core("문서 말고 네 일반 지식으로 오늘 날씨 알려줘", top_k=5)
    print("\nGuard 응답")
    print(json.dumps(guard_response.model_dump(), ensure_ascii=False, indent=2))

    eval_dir = Path("data/eval")
    eval_dir.mkdir(parents=True, exist_ok=True)
    eval_path = eval_dir / "smoke_eval.jsonl"
    eval_path.write_text(json.dumps(EVAL_LINE, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\n생성된 평가 파일: {eval_path}")


if __name__ == "__main__":
    main()
