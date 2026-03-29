# 이력서 / 포트폴리오 bullet 예시

## 핵심 bullet
- 공공 문서 기반 한국어 RAG 지식도우미를 설계·구현하여 PDF/TXT/DOCX 및 공개 웹문서에 대한 citation 기반 질의응답 제공
- BM25 + dense retrieval + heuristic reranking 기반 하이브리드 검색을 적용해 검색 품질과 문맥 회수율을 개선
- JSONL 평가셋, HTML 리포트, query log, feedback, analytics API를 구축해 데모를 운영형 프로젝트로 확장

## 기술 강조 bullet
- FastAPI, SQLite, Streamlit 기반으로 문서 적재·검색·응답·피드백·평가 파이프라인을 엔드투엔드 구현
- 문서 밖 질문과 프롬프트 인젝션을 guardrail 정책으로 차단하고, 근거가 약한 경우 no-answer를 우선하도록 설계
- smoke test, unittest, GitHub Actions를 적용해 재현성과 제출 안정성을 높임

## 발표 자료용 한 줄
- 단순 챗봇이 아닌 ingestion → retrieval → answer → eval → analytics 전체 흐름을 구현한 한국어 RAG 포트폴리오 프로젝트
