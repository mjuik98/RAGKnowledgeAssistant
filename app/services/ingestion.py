from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.models.schemas import UploadDocumentResponse
from app.services.chunker import TextChunker
from app.services.parser import DocumentParser
from app.services.web_loader import WebDocumentFetcher
from app.services.repository import ChunkRepository, DocumentRepository


@dataclass
class DirectoryIngestionSummary:
    processed_count: int
    inserted_count: int
    skipped_count: int
    error_count: int
    errors: list[str]


class IngestionService:
    def __init__(self) -> None:
        self.parser = DocumentParser()
        self.document_repo = DocumentRepository()
        self.chunk_repo = ChunkRepository()
        self.chunker = TextChunker()
        self.web_loader = WebDocumentFetcher()

    def ingest_file(self, file_path: Path) -> UploadDocumentResponse:
        parsed_document = self.parser.parse(file_path)
        existing_document = self.document_repo.get_document_by_checksum(parsed_document.checksum)
        if existing_document:
            return UploadDocumentResponse(
                document_id=int(existing_document["id"]),
                title=str(existing_document["title"]),
                total_pages=int(existing_document["total_pages"]),
                chunk_count=0,
                existed=True,
            )

        document_id = self.document_repo.create_document(
            title=parsed_document.title,
            original_filename=parsed_document.original_filename,
            source_path=parsed_document.source_path,
            source_type=parsed_document.source_type,
            checksum=parsed_document.checksum,
            total_pages=len(parsed_document.pages),
        )
        chunks = self.chunker.chunk_document(document_id=document_id, parsed_document=parsed_document)
        self.chunk_repo.insert_chunks(chunks)
        return UploadDocumentResponse(
            document_id=document_id,
            title=parsed_document.title,
            total_pages=len(parsed_document.pages),
            chunk_count=len(chunks),
            existed=False,
        )

    def ingest_web_url(
        self,
        url: str,
        title_hint: str | None = None,
        filename_hint: str | None = None,
        snapshot_dir: Path | None = None,
    ) -> UploadDocumentResponse:
        snapshot_path = self.web_loader.snapshot_url_to_text(
            url=url,
            title_hint=title_hint,
            filename_hint=filename_hint,
            output_dir=snapshot_dir,
        )
        return self.ingest_file(snapshot_path)

    def ingest_directory(self, directory: Path, recursive: bool = True) -> DirectoryIngestionSummary:
        if not directory.exists():
            raise FileNotFoundError(f"디렉터리를 찾을 수 없습니다: {directory}")

        pattern = "**/*" if recursive else "*"
        files = [
            path for path in directory.glob(pattern)
            if path.is_file() and path.suffix.lower() in self.parser.supported_suffixes
        ]

        inserted_count = 0
        skipped_count = 0
        errors: list[str] = []

        for file_path in sorted(files):
            try:
                result = self.ingest_file(file_path)
                if result.existed:
                    skipped_count += 1
                else:
                    inserted_count += 1
            except Exception as exc:  # pragma: no cover - CLI에서 메시지 전달용
                errors.append(f"{file_path.name}: {exc}")

        return DirectoryIngestionSummary(
            processed_count=len(files),
            inserted_count=inserted_count,
            skipped_count=skipped_count,
            error_count=len(errors),
            errors=errors,
        )
