from __future__ import annotations

import html
import json
from pathlib import Path
from statistics import mean
from typing import Any


def _percent(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:.1f}%"


def _latency(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2f} ms"


def build_eval_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    retrieval = [int(bool(item.get("retrieval_hit"))) for item in results]
    keyword = [int(bool(item.get("keyword_hit"))) for item in results]
    citation_values = [
        int(bool(item.get("citation_hit")))
        for item in results
        if item.get("citation_hit") is not None
    ]
    no_answer_values = [
        int(bool(item.get("no_answer_correct")))
        for item in results
        if item.get("no_answer_correct") is not None
    ]
    status_values = [
        int(bool(item.get("status_match")))
        for item in results
        if item.get("status_match") is not None
    ]
    latencies = [
        float(item.get("latency_ms"))
        for item in results
        if item.get("latency_ms") is not None
    ]

    return {
        "total_count": len(results),
        "retrieval_hit_rate": mean(retrieval) if retrieval else 0.0,
        "keyword_hit_rate": mean(keyword) if keyword else 0.0,
        "citation_hit_rate": mean(citation_values) if citation_values else None,
        "no_answer_accuracy": mean(no_answer_values) if no_answer_values else None,
        "status_hit_rate": mean(status_values) if status_values else None,
        "average_latency_ms": mean(latencies) if latencies else None,
    }


def save_eval_html_report(
    *,
    eval_name: str,
    generated_at: str,
    results: list[dict[str, Any]],
    output_path: Path,
) -> Path:
    summary = build_eval_summary(results)
    failures = [
        item for item in results
        if not all(
            value is True
            for value in [
                item.get("retrieval_hit", True),
                item.get("keyword_hit", True),
                item.get("citation_hit", True),
                item.get("no_answer_correct", True),
                item.get("status_match", True),
            ]
            if value is not None
        )
    ]

    def metric_card(label: str, value: str) -> str:
        return f"""
        <div class=\"card\">
          <div class=\"label\">{html.escape(label)}</div>
          <div class=\"value\">{html.escape(value)}</div>
        </div>
        """

    failure_rows = "".join(
        f"""
        <tr>
          <td>{html.escape(str(item.get('question', '')))}</td>
          <td>{html.escape(str(item.get('status', '')))}</td>
          <td>{'✅' if item.get('retrieval_hit') else '❌'}</td>
          <td>{'✅' if item.get('keyword_hit') else '❌'}</td>
          <td>{'✅' if item.get('citation_hit', True) else '❌'}</td>
          <td>{'✅' if item.get('no_answer_correct', True) else '❌'}</td>
          <td>{html.escape(str(item.get('predicted_answer', '')))}</td>
        </tr>
        """
        for item in failures[:50]
    )

    all_rows = "".join(
        f"""
        <tr>
          <td>{idx}</td>
          <td>{html.escape(str(item.get('question', '')))}</td>
          <td>{html.escape(str(item.get('status', '')))}</td>
          <td>{'✅' if item.get('retrieval_hit') else '❌'}</td>
          <td>{'✅' if item.get('keyword_hit') else '❌'}</td>
          <td>{'✅' if item.get('citation_hit', True) else '❌'}</td>
          <td>{'✅' if item.get('no_answer_correct', True) else '❌'}</td>
          <td>{html.escape(str(item.get('latency_ms', '-')))}</td>
        </tr>
        """
        for idx, item in enumerate(results, start=1)
    )

    payload_json = html.escape(json.dumps(results, ensure_ascii=False, indent=2))

    html_text = f"""
<!doctype html>
<html lang=\"ko\">
<head>
  <meta charset=\"utf-8\" />
  <title>{html.escape(eval_name)} · Eval Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #222; }}
    h1, h2 {{ margin-bottom: 8px; }}
    .sub {{ color: #666; margin-bottom: 20px; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, minmax(220px, 1fr)); gap: 12px; margin: 20px 0 28px; }}
    .card {{ border: 1px solid #ddd; border-radius: 10px; padding: 16px; background: #fafafa; }}
    .label {{ font-size: 12px; color: #666; margin-bottom: 6px; }}
    .value {{ font-size: 24px; font-weight: 700; }}
    table {{ width: 100%; border-collapse: collapse; margin: 16px 0 24px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; text-align: left; font-size: 14px; }}
    th {{ background: #f5f5f5; }}
    .pill {{ display: inline-block; padding: 4px 8px; border-radius: 999px; background: #eef3ff; color: #224; font-size: 12px; margin-right: 6px; }}
    details {{ margin-top: 20px; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #f8f8f8; padding: 12px; border-radius: 8px; border: 1px solid #e5e5e5; }}
  </style>
</head>
<body>
  <h1>{html.escape(eval_name)} 평가 리포트</h1>
  <div class=\"sub\">생성 시각: {html.escape(generated_at)} · 총 문항 수: {summary['total_count']}</div>
  <div>
    <span class=\"pill\">Retrieval {_percent(summary['retrieval_hit_rate'])}</span>
    <span class=\"pill\">Keyword {_percent(summary['keyword_hit_rate'])}</span>
    <span class=\"pill\">Citation {_percent(summary['citation_hit_rate'])}</span>
    <span class=\"pill\">No-answer {_percent(summary['no_answer_accuracy'])}</span>
    <span class=\"pill\">Status {_percent(summary['status_hit_rate'])}</span>
  </div>

  <div class=\"grid\">
    {metric_card('Retrieval Hit Rate', _percent(summary['retrieval_hit_rate']))}
    {metric_card('Keyword Hit Rate', _percent(summary['keyword_hit_rate']))}
    {metric_card('Citation Hit Rate', _percent(summary['citation_hit_rate']))}
    {metric_card('No-answer Accuracy', _percent(summary['no_answer_accuracy']))}
    {metric_card('Status Hit Rate', _percent(summary['status_hit_rate']))}
    {metric_card('Average Latency', _latency(summary['average_latency_ms']))}
  </div>

  <h2>실패/주의 케이스</h2>
  <table>
    <thead>
      <tr>
        <th>질문</th>
        <th>상태</th>
        <th>검색</th>
        <th>키워드</th>
        <th>인용</th>
        <th>No-answer</th>
        <th>예측 답변</th>
      </tr>
    </thead>
    <tbody>
      {failure_rows or '<tr><td colspan="7">실패 케이스가 없습니다.</td></tr>'}
    </tbody>
  </table>

  <h2>전체 결과</h2>
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>질문</th>
        <th>상태</th>
        <th>검색</th>
        <th>키워드</th>
        <th>인용</th>
        <th>No-answer</th>
        <th>Latency(ms)</th>
      </tr>
    </thead>
    <tbody>
      {all_rows}
    </tbody>
  </table>

  <details>
    <summary>원본 JSON 결과 보기</summary>
    <pre>{payload_json}</pre>
  </details>
</body>
</html>
    """.strip()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_text, encoding="utf-8")
    return output_path
