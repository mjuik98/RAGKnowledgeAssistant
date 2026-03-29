from __future__ import annotations

import json
from typing import Any

from app.core.database import execute, executemany, fetchall, fetchone
from app.models.schemas import ChunkRecord


class DocumentRepository:
    def create_document(
        self,
        title: str,
        original_filename: str,
        source_path: str,
        source_type: str,
        checksum: str,
        total_pages: int,
    ) -> int:
        execute(
            """
            INSERT INTO documents (title, original_filename, source_path, source_type, checksum, total_pages)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, original_filename, source_path, source_type, checksum, total_pages),
        )
        row = fetchone("SELECT id FROM documents WHERE checksum = ?", (checksum,))
        assert row is not None
        return int(row["id"])

    def get_document_by_checksum(self, checksum: str) -> dict[str, Any] | None:
        row = fetchone("SELECT * FROM documents WHERE checksum = ?", (checksum,))
        return dict(row) if row else None

    def list_documents(self) -> list[dict[str, Any]]:
        rows = fetchall("SELECT * FROM documents ORDER BY id DESC")
        return [dict(row) for row in rows]

    def count_documents(self) -> int:
        row = fetchone("SELECT COUNT(*) AS count FROM documents")
        return int(row["count"]) if row else 0

    def list_document_usage(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = fetchall(
            """
            SELECT
                d.id AS document_id,
                d.title AS document_title,
                d.source_type,
                d.total_pages,
                COUNT(DISTINCT c.id) AS chunk_count,
                COALESCE(COUNT(qr.id), 0) AS retrieval_count
            FROM documents d
            LEFT JOIN chunks c ON c.document_id = d.id
            LEFT JOIN query_retrievals qr ON qr.chunk_id = c.id
            GROUP BY d.id, d.title, d.source_type, d.total_pages
            ORDER BY retrieval_count DESC, d.id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in rows]


class ChunkRepository:
    def insert_chunks(self, chunks: list[ChunkRecord]) -> None:
        values = [
            (
                chunk.document_id,
                chunk.page_number,
                chunk.chunk_index,
                chunk.content,
                len(chunk.content),
                json.dumps(chunk.metadata, ensure_ascii=False),
            )
            for chunk in chunks
        ]
        executemany(
            """
            INSERT INTO chunks (document_id, page_number, chunk_index, content, content_length, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            values,
        )

    def list_all_chunks(self) -> list[dict[str, Any]]:
        rows = fetchall(
            """
            SELECT c.id, c.document_id, c.page_number, c.chunk_index, c.content,
                   c.metadata_json, d.title AS document_title
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            ORDER BY c.id ASC
            """
        )
        chunk_dicts: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            metadata_json = item.pop("metadata_json", None)
            if metadata_json:
                try:
                    item["metadata"] = json.loads(metadata_json)
                except json.JSONDecodeError:
                    item["metadata"] = {}
            else:
                item["metadata"] = {}
            chunk_dicts.append(item)
        return chunk_dicts

    def count_chunks(self) -> int:
        row = fetchone("SELECT COUNT(*) AS count FROM chunks")
        return int(row["count"]) if row else 0


class QueryRepository:
    def create_query_log(
        self,
        question: str,
        normalized_question: str,
        answer: str,
        status: str,
        latency_ms: float,
    ) -> int:
        execute(
            """
            INSERT INTO queries (question, normalized_question, answer, status, latency_ms)
            VALUES (?, ?, ?, ?, ?)
            """,
            (question, normalized_question, answer, status, latency_ms),
        )
        row = fetchone("SELECT id FROM queries ORDER BY id DESC LIMIT 1")
        assert row is not None
        return int(row["id"])

    def insert_retrieval_logs(self, query_id: int, retrievals: list[dict[str, Any]]) -> None:
        if not retrievals:
            return
        values = [
            (query_id, item["chunk_id"], item["score"], item["rank"], item.get("stage", "retrieve"))
            for item in retrievals
        ]
        executemany(
            """
            INSERT INTO query_retrievals (query_id, chunk_id, score, rank_order, stage)
            VALUES (?, ?, ?, ?, ?)
            """,
            values,
        )

    def get_query_by_id(self, query_id: int) -> dict[str, Any] | None:
        row = fetchone("SELECT * FROM queries WHERE id = ?", (query_id,))
        return dict(row) if row else None

    def count_queries(self) -> int:
        row = fetchone("SELECT COUNT(*) AS count FROM queries")
        return int(row["count"]) if row else 0

    def average_latency_ms(self) -> float | None:
        row = fetchone("SELECT AVG(latency_ms) AS value FROM queries")
        value = row["value"] if row else None
        return float(value) if value is not None else None

    def count_by_status(self) -> dict[str, int]:
        rows = fetchall(
            """
            SELECT status, COUNT(*) AS count
            FROM queries
            GROUP BY status
            """
        )
        return {str(row["status"]): int(row["count"]) for row in rows}

    def list_recent_queries(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = fetchall(
            """
            SELECT
                q.id AS query_id,
                q.question,
                q.status,
                q.latency_ms,
                q.created_at,
                f.rating AS feedback_rating,
                f.comment AS feedback_comment,
                d.title AS top_document_title
            FROM queries q
            LEFT JOIN feedback f
                ON f.id = (
                    SELECT f2.id FROM feedback f2 WHERE f2.query_id = q.id ORDER BY f2.id DESC LIMIT 1
                )
            LEFT JOIN query_retrievals qr
                ON qr.id = (
                    SELECT qr2.id FROM query_retrievals qr2 WHERE qr2.query_id = q.id ORDER BY qr2.rank_order ASC, qr2.id ASC LIMIT 1
                )
            LEFT JOIN chunks c ON c.id = qr.chunk_id
            LEFT JOIN documents d ON d.id = c.document_id
            ORDER BY q.id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in rows]


class FeedbackRepository:
    def create_feedback(self, query_id: int, rating: int, comment: str | None = None) -> int:
        execute(
            """
            INSERT INTO feedback (query_id, rating, comment)
            VALUES (?, ?, ?)
            """,
            (query_id, rating, comment),
        )
        row = fetchone("SELECT id FROM feedback ORDER BY id DESC LIMIT 1")
        assert row is not None
        return int(row["id"])

    def summarize_feedback(self) -> dict[str, int]:
        row = fetchone(
            """
            SELECT
                COUNT(*) AS feedback_count,
                SUM(CASE WHEN rating > 0 THEN 1 ELSE 0 END) AS positive_feedback_count,
                SUM(CASE WHEN rating < 0 THEN 1 ELSE 0 END) AS negative_feedback_count,
                SUM(CASE WHEN rating = 0 THEN 1 ELSE 0 END) AS neutral_feedback_count
            FROM feedback
            """
        )
        if not row:
            return {
                "feedback_count": 0,
                "positive_feedback_count": 0,
                "negative_feedback_count": 0,
                "neutral_feedback_count": 0,
            }
        return {
            "feedback_count": int(row["feedback_count"] or 0),
            "positive_feedback_count": int(row["positive_feedback_count"] or 0),
            "negative_feedback_count": int(row["negative_feedback_count"] or 0),
            "neutral_feedback_count": int(row["neutral_feedback_count"] or 0),
        }


class EvalRepository:
    def create_eval_run(
        self,
        eval_name: str,
        eval_file_path: str,
        total_count: int,
        retrieval_hit_rate: float,
        keyword_hit_rate: float,
        citation_hit_rate: float | None = None,
        no_answer_accuracy: float | None = None,
        average_latency_ms: float | None = None,
        report_path: str | None = None,
    ) -> int:
        execute(
            """
            INSERT INTO eval_runs (
                eval_name, eval_file_path, total_count, retrieval_hit_rate, keyword_hit_rate,
                citation_hit_rate, no_answer_accuracy, average_latency_ms, report_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                eval_name,
                eval_file_path,
                total_count,
                retrieval_hit_rate,
                keyword_hit_rate,
                citation_hit_rate,
                no_answer_accuracy,
                average_latency_ms,
                report_path,
            ),
        )
        row = fetchone("SELECT id FROM eval_runs ORDER BY id DESC LIMIT 1")
        assert row is not None
        return int(row["id"])

    def insert_eval_results(self, eval_run_id: int, results: list[dict[str, Any]]) -> None:
        values = [
            (
                eval_run_id,
                item["question"],
                item.get("reference_answer"),
                item["predicted_answer"],
                int(item["retrieval_hit"]),
                int(item["keyword_hit"]),
                item.get("notes"),
            )
            for item in results
        ]
        executemany(
            """
            INSERT INTO eval_results (
                eval_run_id, question, reference_answer, predicted_answer,
                retrieval_hit, keyword_hit, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )

    def list_recent_eval_runs(self, limit: int = 10) -> list[dict[str, Any]]:
        rows = fetchall(
            """
            SELECT
                id AS eval_run_id,
                eval_name,
                total_count,
                retrieval_hit_rate,
                keyword_hit_rate,
                citation_hit_rate,
                no_answer_accuracy,
                average_latency_ms,
                report_path,
                created_at
            FROM eval_runs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in rows]

    def get_latest_eval_run(self) -> dict[str, Any] | None:
        row = fetchone(
            """
            SELECT
                eval_name,
                total_count,
                retrieval_hit_rate,
                keyword_hit_rate,
                citation_hit_rate,
                no_answer_accuracy,
                average_latency_ms,
                report_path,
                created_at
            FROM eval_runs
            ORDER BY id DESC
            LIMIT 1
            """
        )
        return dict(row) if row else None
