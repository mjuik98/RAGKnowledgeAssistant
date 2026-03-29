from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.models.schemas import RetrievedChunk
from app.services.generator import ExtractiveAnswerGenerator
from app.services.reporting import build_eval_summary, save_eval_html_report


class GeneratorAndReportingTests(unittest.TestCase):
    def test_generator_returns_grounded_answer_with_citation(self) -> None:
        generator = ExtractiveAnswerGenerator()
        chunks = [
            RetrievedChunk(
                chunk_id=1,
                document_id=1,
                document_title="sample_notice",
                page_number=1,
                content="전입신고를 위해서는 신청인의 신분증이 필요합니다. 대리 신청 시에는 위임장이 필요합니다.",
                score=0.9,
                rank=1,
                metadata={"lexical_score": 0.9, "rerank_bonus": 0.1},
            )
        ]
        answer, status, citations = generator.generate("전입신고에 필요한 서류가 뭐야?", chunks)
        self.assertEqual(status, "grounded_answer")
        self.assertIn("신분증", answer)
        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0].document_title, "sample_notice")

    def test_reporting_generates_html_file(self) -> None:
        results = [
            {
                "question": "전입신고에 필요한 서류가 뭐야?",
                "predicted_answer": "신분증이 필요합니다.",
                "status": "grounded_answer",
                "retrieval_hit": True,
                "keyword_hit": True,
                "citation_hit": True,
                "no_answer_correct": True,
                "status_match": True,
                "latency_ms": 1.2,
            }
        ]
        summary = build_eval_summary(results)
        self.assertEqual(summary["retrieval_hit_rate"], 1.0)
        self.assertEqual(summary["status_hit_rate"], 1.0)

        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "report.html"
            saved = save_eval_html_report(
                eval_name="unit_eval",
                generated_at="20260329_100000",
                results=results,
                output_path=html_path,
            )
            self.assertTrue(saved.exists())
            content = saved.read_text(encoding="utf-8")
            self.assertIn("unit_eval 평가 리포트", content)
            self.assertIn("Retrieval Hit Rate", content)


if __name__ == "__main__":
    unittest.main()
