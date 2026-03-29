from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import init_db
from app.services.ingestion import IngestionService
from app.services.repository import ChunkRepository
from app.services.retriever import HybridRetriever


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="공개 URL 목록을 TXT 스냅샷으로 저장한 뒤 문서로 적재합니다.")
    parser.add_argument(
        "--manifest",
        default="data/corpus/public_service_manifest.csv",
        help="적재할 URL 목록 CSV 경로",
    )
    parser.add_argument(
        "--snapshot-dir",
        default="storage/raw/web_imports",
        help="TXT 스냅샷을 저장할 디렉터리",
    )
    parser.add_argument("--limit", type=int, default=None, help="상위 N개 항목만 적재")
    parser.add_argument(
        "--include-disabled",
        action="store_true",
        help="enabled=false 항목도 함께 적재합니다.",
    )
    return parser.parse_args()


def load_manifest(path: Path, include_disabled: bool) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if include_disabled:
        return rows

    enabled_values = {"1", "true", "yes", "y"}
    filtered: list[dict[str, str]] = []
    for row in rows:
        enabled = (row.get("enabled") or "true").strip().lower()
        if enabled in enabled_values:
            filtered.append(row)
    return filtered


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest)
    snapshot_dir = Path(args.snapshot_dir)
    if not manifest_path.exists():
        raise FileNotFoundError(f"매니페스트 파일을 찾을 수 없습니다: {manifest_path}")

    init_db()
    service = IngestionService()
    rows = load_manifest(manifest_path, include_disabled=args.include_disabled)
    if args.limit is not None:
        rows = rows[: args.limit]

    inserted = 0
    skipped = 0
    errors: list[str] = []

    for row in rows:
        title = (row.get("title") or "").strip()
        url = (row.get("url") or "").strip()
        slug = (row.get("slug") or "").strip() or None
        if not url:
            errors.append(f"{title or '<unknown>'}: url 값이 비어 있습니다.")
            continue

        try:
            result = service.ingest_web_url(
                url=url,
                title_hint=title or None,
                filename_hint=slug,
                snapshot_dir=snapshot_dir,
            )
            if result.existed:
                skipped += 1
                print(f"[SKIP] {title} -> 이미 동일 내용이 적재되어 있습니다.")
            else:
                inserted += 1
                print(
                    f"[OK] {title} -> document_id={result.document_id}, chunks={result.chunk_count}, pages={result.total_pages}"
                )
        except Exception as exc:
            errors.append(f"{title or url}: {exc}")
            print(f"[ERR] {title or url} -> {exc}")

    retriever = HybridRetriever()
    chunk_repo = ChunkRepository()
    retriever.rebuild(chunk_repo.list_all_chunks())
    info = retriever.describe()

    print("\n공개 URL 적재가 완료되었습니다.")
    print(f"- 처리 항목 수: {len(rows)}")
    print(f"- 신규 적재 수: {inserted}")
    print(f"- 중복 스킵 수: {skipped}")
    print(f"- 오류 수: {len(errors)}")
    print(f"- Dense backend: {info['dense_backend']}")
    print(f"- Dense model:   {info['dense_model_name']}")
    if errors:
        print("\n오류 상세")
        for error in errors:
            print(f"  - {error}")


if __name__ == "__main__":
    main()
