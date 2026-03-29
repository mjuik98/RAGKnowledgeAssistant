from __future__ import annotations

import re

from app.core.config import get_settings
from app.models.schemas import ChunkRecord, ParsedDocument


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class TextChunker:
    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None) -> None:
        settings = get_settings()
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    def chunk_document(self, document_id: int, parsed_document: ParsedDocument) -> list[ChunkRecord]:
        chunks: list[ChunkRecord] = []

        for page in parsed_document.pages:
            text = normalize_whitespace(page.text)
            if not text:
                continue

            start = 0
            chunk_index = 0
            while start < len(text):
                end = start + self.chunk_size
                content = text[start:end].strip()
                if content:
                    chunks.append(
                        ChunkRecord(
                            document_id=document_id,
                            page_number=page.page_number,
                            chunk_index=chunk_index,
                            content=content,
                            metadata={
                                "title": parsed_document.title,
                                "page_number": page.page_number,
                                "chunk_index": chunk_index,
                            },
                        )
                    )
                    chunk_index += 1

                if end >= len(text):
                    break

                start = max(0, end - self.chunk_overlap)

        return chunks
