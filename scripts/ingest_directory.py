from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import init_db
from app.services.ingestion import IngestionService
from app.services.repository import ChunkRepository
from app.services.retriever import HybridRetriever


def main() -> None:
    parser = argparse.ArgumentParser(description="디렉터리 내 문서를 일괄 적재합니다.")
    parser.add_argument("--input-dir", default="storage/raw", help="문서가 있는 디렉터리 경로")
    parser.add_argument("--no-recursive", action="store_true", help="하위 폴더를 재귀적으로 읽지 않습니다.")
    args = parser.parse_args()

    init_db()
    service = IngestionService()
    summary = service.ingest_directory(Path(args.input_dir), recursive=not args.no_recursive)

    retriever = HybridRetriever()
    chunk_repo = ChunkRepository()
    retriever.rebuild(chunk_repo.list_all_chunks())
    retriever_info = retriever.describe()

    print("문서 일괄 적재가 완료되었습니다.")
    print(f"- 처리 파일 수: {summary.processed_count}")
    print(f"- 신규 적재 수: {summary.inserted_count}")
    print(f"- 중복 스킵 수: {summary.skipped_count}")
    print(f"- 오류 수: {summary.error_count}")
    print(f"- Dense backend: {retriever_info['dense_backend']}")
    print(f"- Dense model:   {retriever_info['dense_model_name']}")
    print(f"- Cache loaded:  {retriever_info['loaded_from_cache']}")
    if summary.errors:
        print("\n오류 상세")
        for error in summary.errors:
            print(f"  - {error}")


if __name__ == "__main__":
    main()
