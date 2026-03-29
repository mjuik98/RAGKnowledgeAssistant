from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Callable

from app.core.config import get_settings
from app.models.schemas import EvalItemResult, EvalRunResponse
from app.services.reporting import save_eval_html_report


class SimpleEvaluator:
    def run(self, eval_file_path: str, ask_fn: Callable[[str], dict], save_report: bool = True) -> EvalRunResponse:
        path = Path(eval_file_path)
        if not path.exists():
            raise FileNotFoundError(f"평가 파일을 찾을 수 없습니다: {eval_file_path}")

        raw_items = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        results: list[EvalItemResult] = []
        retrieval_hits: list[int] = []
        keyword_hits: list[int] = []
        citation_hits: list[int] = []
        no_answer_checks: list[int] = []
        status_checks: list[int] = []
        latencies: list[float] = []

        for item in raw_items:
            question = item["question"]
            must_include = item.get("must_include", [])
            must_not_include = item.get("must_not_include", [])
            expected_document_titles = item.get("expected_document_titles", [])
            expected_no_answer = item.get("expected_no_answer")
            expected_status = item.get("expected_status")
            acceptable_statuses = set(item.get("acceptable_statuses", []))

            response = ask_fn(question)
            predicted_answer = response["answer"]
            status = response.get("status", "unknown")
            citations = response.get("citations", [])
            latency_ms = float(response.get("latency_ms") or 0.0)
            if latency_ms > 0:
                latencies.append(latency_ms)

            cited_titles = {citation["document_title"] for citation in citations}
            retrieval_hit = (
                True
                if not expected_document_titles
                else any(title in cited_titles for title in expected_document_titles)
            )
            keyword_hit = all(keyword in predicted_answer for keyword in must_include) and all(
                keyword not in predicted_answer for keyword in must_not_include
            )
            citation_hit = retrieval_hit if expected_document_titles else True

            if expected_no_answer is None:
                no_answer_correct = None
            else:
                is_no_answer_like = status in {"no_answer", "guard_blocked"}
                no_answer_correct = is_no_answer_like == bool(expected_no_answer)

            if expected_status and not acceptable_statuses:
                acceptable_statuses = {str(expected_status)}
            elif expected_no_answer is not None and not acceptable_statuses:
                acceptable_statuses = {"no_answer", "guard_blocked"} if bool(expected_no_answer) else {"grounded_answer"}

            status_match = None if not acceptable_statuses else status in acceptable_statuses

            retrieval_hits.append(int(retrieval_hit))
            keyword_hits.append(int(keyword_hit))
            citation_hits.append(int(citation_hit))
            if no_answer_correct is not None:
                no_answer_checks.append(int(no_answer_correct))
            if status_match is not None:
                status_checks.append(int(status_match))

            results.append(
                EvalItemResult(
                    question=question,
                    predicted_answer=predicted_answer,
                    status=status,
                    retrieval_hit=retrieval_hit,
                    keyword_hit=keyword_hit,
                    citation_hit=citation_hit,
                    no_answer_correct=no_answer_correct,
                    status_match=status_match,
                    latency_ms=round(latency_ms, 2) if latency_ms else None,
                    notes=item.get("notes"),
                )
            )

        report_path, html_report_path = self._save_report(path, results) if save_report else (None, None)
        return EvalRunResponse(
            eval_name=path.stem,
            total_count=len(results),
            retrieval_hit_rate=mean(retrieval_hits) if retrieval_hits else 0.0,
            keyword_hit_rate=mean(keyword_hits) if keyword_hits else 0.0,
            citation_hit_rate=mean(citation_hits) if citation_hits else 0.0,
            no_answer_accuracy=mean(no_answer_checks) if no_answer_checks else None,
            status_hit_rate=mean(status_checks) if status_checks else None,
            average_latency_ms=mean(latencies) if latencies else None,
            report_path=str(report_path) if report_path else None,
            html_report_path=str(html_report_path) if html_report_path else None,
            results=results,
        )

    def _save_report(self, eval_file_path: Path, results: list[EvalItemResult]) -> tuple[Path, Path]:
        settings = get_settings()
        report_dir = Path(settings.eval_report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        json_path = report_dir / f"{eval_file_path.stem}_{timestamp}.json"
        html_path = report_dir / f"{eval_file_path.stem}_{timestamp}.html"

        payload = {
            "eval_name": eval_file_path.stem,
            "generated_at": timestamp,
            "results": [item.model_dump() for item in results],
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        save_eval_html_report(
            eval_name=eval_file_path.stem,
            generated_at=timestamp,
            results=[item.model_dump() for item in results],
            output_path=html_path,
        )
        return json_path, html_path
