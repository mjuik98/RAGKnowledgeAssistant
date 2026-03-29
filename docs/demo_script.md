# 3분 데모 스크립트

## 0:00 ~ 0:30 문제 정의
- 공공 문서가 많아질수록 사용자는 필요한 규정을 찾기 어렵습니다.
- 이 프로젝트는 업로드된 문서만을 근거로 답변하고, 근거가 없으면 답변을 보류하는 한국어 RAG 지식도우미입니다.

## 0:30 ~ 1:20 문서 적재
- 샘플 문서 6개를 적재합니다.
- `/system/index`와 Streamlit 사이드바에서 문서 수와 청크 수를 확인합니다.
- dense backend와 캐시 사용 여부도 함께 보여줍니다.

## 1:20 ~ 2:10 질의응답
- 전입신고 질문으로 grounded answer를 시연합니다.
- 출처 페이지와 retrieved chunk를 펼쳐 실제 근거를 보여줍니다.
- 이어서 문서 밖 질문 또는 프롬프트 인젝션 질문을 던져 guard 차단 동작을 보여줍니다.

## 2:10 ~ 2:40 운영/평가
- 운영 현황 탭에서 최근 질문, 응답 상태, 문서 활용도를 보여줍니다.
- 평가 탭에서 `portfolio_eval.jsonl`을 실행하고 Retrieval/Keyword/Citation/Status 지표를 확인합니다.
- HTML 리포트 경로를 보여주며 발표 자료로 재활용할 수 있다고 설명합니다.

## 2:40 ~ 3:00 마무리
- 현재는 extractive answer baseline입니다.
- 다음 확장으로 sentence-transformers, cross-encoder reranker, 생성형 LLM, OCR/HWP를 계획하고 있다고 설명합니다.
