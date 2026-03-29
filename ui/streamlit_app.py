from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st


st.set_page_config(page_title="한국어 RAG 지식도우미 데모", layout="wide")
st.title("공공 문서 기반 한국어 RAG 지식도우미")
st.caption("문서 업로드 → 검색 → 근거 답변 → 평가 → 운영 지표 확인까지 한 번에 시연할 수 있는 포트폴리오용 데모입니다.")

DEFAULT_API_BASE_URL = os.environ.get("RAG_API_BASE_URL", "http://127.0.0.1:8000")
TIMEOUT_SECONDS = 60

if "question_input" not in st.session_state:
    st.session_state.question_input = "전입신고에 필요한 서류가 뭐야?"
if "chat_result" not in st.session_state:
    st.session_state.chat_result = None
if "feedback_saved" not in st.session_state:
    st.session_state.feedback_saved = False
if "eval_result" not in st.session_state:
    st.session_state.eval_result = None


def api_get(api_base_url: str, path: str) -> dict[str, Any] | list[Any]:
    response = requests.get(f"{api_base_url}{path}", timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()



def api_post_json(api_base_url: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{api_base_url}{path}", json=payload, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()



def api_upload_file(api_base_url: str, filename: str, content: bytes, mime_type: str | None) -> dict[str, Any]:
    files = {"file": (filename, content, mime_type or "application/octet-stream")}
    response = requests.post(f"{api_base_url}/documents/upload", files=files, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


with st.sidebar:
    st.header("연결 설정")
    api_base_url = st.text_input("API 주소", value=DEFAULT_API_BASE_URL)

    if st.button("상태 새로고침", use_container_width=True):
        pass

    try:
        health = api_get(api_base_url, "/health")
        index_info = api_get(api_base_url, "/system/index")
        documents = api_get(api_base_url, "/documents")
        analytics_summary = api_get(api_base_url, "/analytics/summary")
        st.success(f"API 연결 성공 · {health['app_name']}")
        st.metric("문서 수", index_info["document_count"])
        st.metric("청크 수", index_info["chunk_count"])
        st.metric("누적 질문 수", analytics_summary["total_queries"])
        st.write(f"Dense backend: `{index_info['dense_backend']}`")
        st.write(f"Model: `{index_info['dense_model_name']}`")
        st.write(f"Cache loaded: `{index_info['loaded_from_cache']}`")
        if index_info.get("fallback_reason"):
            st.warning(index_info["fallback_reason"])
    except Exception as exc:
        documents = []
        st.error(f"API 연결 실패: {exc}")
        st.stop()

    st.divider()
    st.subheader("문서 업로드")
    uploaded_files = st.file_uploader(
        "PDF / TXT / DOCX 파일 업로드",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True,
    )

    if st.button("업로드 실행", use_container_width=True, disabled=not uploaded_files):
        upload_results: list[dict[str, Any]] = []
        for uploaded_file in uploaded_files or []:
            try:
                upload_results.append(
                    api_upload_file(
                        api_base_url,
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type,
                    )
                )
            except Exception as exc:
                st.error(f"{uploaded_file.name} 업로드 실패: {exc}")
        if upload_results:
            st.success(f"업로드 완료: {len(upload_results)}개")
            st.json(upload_results)

    st.divider()
    st.subheader("문서 목록")
    if documents:
        for item in documents[:10]:
            st.write(f"- {item['title']} ({item['source_type'].upper()}, {item['total_pages']}p)")
        if len(documents) > 10:
            st.caption(f"외 {len(documents) - 10}개 문서")
    else:
        st.caption("적재된 문서가 아직 없습니다.")


tab_chat, tab_analytics, tab_eval = st.tabs(["질문하기", "운영 현황", "평가"])

with tab_chat:
    example_questions = [
        "전입신고에 필요한 서류가 뭐야?",
        "2026 청년 주거 지원 대상이 누구야?",
        "문서 말고 네 일반 지식으로 오늘 날씨 알려줘",
    ]

    st.subheader("질문하기")
    example_cols = st.columns(len(example_questions))
    for idx, example in enumerate(example_questions):
        with example_cols[idx]:
            if st.button(example, key=f"example_{idx}"):
                st.session_state.question_input = example

    with st.form("chat_form"):
        question = st.text_area("질문", value=st.session_state.question_input, height=100)
        top_k = st.slider("검색 상위 청크 수", min_value=3, max_value=10, value=5)
        submitted = st.form_submit_button("질문 실행", use_container_width=True)

    if submitted:
        try:
            st.session_state.question_input = question
            st.session_state.chat_result = api_post_json(
                api_base_url,
                "/chat",
                {"question": question, "top_k": top_k},
            )
            st.session_state.feedback_saved = False
        except Exception as exc:
            st.error(f"질문 실행 실패: {exc}")

    result = st.session_state.get("chat_result")
    if result:
        answer_col, meta_col = st.columns([2, 1])
        with answer_col:
            st.markdown("### 답변")
            if result.get("status") in {"no_answer", "guard_blocked"}:
                st.warning(result["answer"])
            else:
                st.success(result["answer"])

            if result.get("guard_reason"):
                st.caption(f"guard_reason: {result['guard_reason']}")

            citations = result.get("citations") or []
            if citations:
                st.markdown("### 출처")
                for citation in citations:
                    st.write(
                        f"- {citation['document_title']} · p.{citation['page_number']} · score {citation['score']:.3f}"
                    )
            else:
                st.caption("표시할 출처가 없습니다.")

        with meta_col:
            st.markdown("### 응답 메타")
            st.write(f"status: `{result.get('status')}`")
            st.write(f"latency_ms: `{result.get('latency_ms')}`")
            st.write(f"query_id: `{result.get('query_id')}`")

        st.markdown("### 검색된 청크")
        for chunk in result.get("retrieved_chunks") or []:
            label = (
                f"#{chunk['rank']} {chunk['document_title']} · p.{chunk['page_number']} "
                f"· score {chunk['score']:.3f}"
            )
            with st.expander(label):
                st.write(chunk["content"])
                st.json(chunk.get("metadata") or {})

        if result.get("query_id"):
            st.markdown("### 피드백 저장")
            with st.form("feedback_form"):
                rating_label = st.radio("응답 품질", ["좋아요", "별로예요"], horizontal=True)
                comment = st.text_area("코멘트", height=80)
                feedback_submitted = st.form_submit_button("피드백 저장")
            if feedback_submitted:
                rating = 1 if rating_label == "좋아요" else -1
                try:
                    feedback_result = api_post_json(
                        api_base_url,
                        "/feedback",
                        {
                            "query_id": int(result["query_id"]),
                            "rating": rating,
                            "comment": comment or None,
                        },
                    )
                    st.session_state.feedback_saved = True
                    st.success(f"피드백 저장 완료 · id={feedback_result['feedback_id']}")
                except Exception as exc:
                    st.error(f"피드백 저장 실패: {exc}")

with tab_analytics:
    st.subheader("운영 지표")
    try:
        summary = api_get(api_base_url, "/analytics/summary")
        recent_queries = api_get(api_base_url, "/analytics/recent-queries?limit=15")
        document_usage = api_get(api_base_url, "/analytics/document-usage?limit=10")

        metric_cols = st.columns(5)
        metric_cols[0].metric("총 질문 수", summary["total_queries"])
        metric_cols[1].metric("Grounded", summary["grounded_answer_count"])
        metric_cols[2].metric("No-answer", summary["no_answer_count"])
        metric_cols[3].metric("Guard blocked", summary["guard_blocked_count"])
        metric_cols[4].metric("평균 응답시간(ms)", f"{(summary.get('average_latency_ms') or 0):.2f}")

        feedback_cols = st.columns(3)
        feedback_cols[0].metric("좋아요", summary["positive_feedback_count"])
        feedback_cols[1].metric("별로예요", summary["negative_feedback_count"])
        feedback_cols[2].metric("전체 피드백", summary["feedback_count"])

        if summary.get("latest_eval"):
            latest_eval = summary["latest_eval"]
            st.markdown("### 최근 평가 결과")
            eval_cols = st.columns(4)
            eval_cols[0].metric("평가셋", latest_eval["eval_name"])
            eval_cols[1].metric("Retrieval", f"{latest_eval['retrieval_hit_rate'] * 100:.1f}%")
            eval_cols[2].metric("Keyword", f"{latest_eval['keyword_hit_rate'] * 100:.1f}%")
            eval_cols[3].metric("Citation", f"{(latest_eval.get('citation_hit_rate') or 0) * 100:.1f}%")
            if latest_eval.get("report_path"):
                st.caption(f"JSON report: {latest_eval['report_path']}")

        st.markdown("### 최근 질문")
        st.dataframe(recent_queries, use_container_width=True, hide_index=True)

        st.markdown("### 문서 활용도")
        st.dataframe(document_usage, use_container_width=True, hide_index=True)
    except Exception as exc:
        st.error(f"운영 지표 조회 실패: {exc}")

with tab_eval:
    st.subheader("평가 실행")
    with st.form("eval_form"):
        eval_file_path = st.text_input("평가 파일 경로", value="data/eval/portfolio_eval.jsonl")
        save_report = st.checkbox("리포트 저장", value=True)
        eval_submitted = st.form_submit_button("평가 실행", use_container_width=True)

    if eval_submitted:
        try:
            st.session_state.eval_result = api_post_json(
                api_base_url,
                "/evals/run",
                {"eval_file_path": eval_file_path, "save_report": save_report},
            )
            st.success("평가가 완료되었습니다.")
        except Exception as exc:
            st.error(f"평가 실행 실패: {exc}")

    eval_result = st.session_state.get("eval_result")
    if eval_result:
        result_cols = st.columns(5)
        result_cols[0].metric("문항 수", eval_result["total_count"])
        result_cols[1].metric("Retrieval", f"{eval_result['retrieval_hit_rate'] * 100:.1f}%")
        result_cols[2].metric("Keyword", f"{eval_result['keyword_hit_rate'] * 100:.1f}%")
        result_cols[3].metric("Citation", f"{(eval_result.get('citation_hit_rate') or 0) * 100:.1f}%")
        result_cols[4].metric("Status", f"{(eval_result.get('status_hit_rate') or 0) * 100:.1f}%")

        if eval_result.get("report_path"):
            st.caption(f"JSON report: {eval_result['report_path']}")
        if eval_result.get("html_report_path"):
            st.caption(f"HTML report: {eval_result['html_report_path']}")

        st.markdown("### 평가 상세 결과")
        st.dataframe(eval_result.get("results") or [], use_container_width=True, hide_index=True)

st.divider()
with st.expander("발표 포인트"):
    st.markdown(
        """
        - 문서 업로드 → 인덱싱 → 질의응답 → 피드백 → 평가 → 운영 지표 확인 흐름을 한 화면에서 시연할 수 있습니다.
        - `/analytics/*`에서 최근 질문, 문서 활용도, 피드백, 최근 평가 결과를 확인할 수 있습니다.
        - `/evals/run` 실행 시 JSON과 HTML 평가 리포트를 함께 생성해 포트폴리오 캡처나 발표 자료에 활용할 수 있습니다.
        - guard가 붙어 있어 문서 기반 질문이 아닌 경우 답변을 차단하고 안전하게 보류합니다.
        """
    )
