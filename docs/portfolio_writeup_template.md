# 포트폴리오 작성 템플릿

## 프로젝트명
공공 문서 기반 한국어 RAG 지식도우미

## 한 줄 소개
업로드된 공공 문서를 파싱·색인하고, 질문에 대해 출처 기반 답변과 페이지 정보를 제공하는 한국어 RAG 시스템

## 문제 정의
- 문서가 많아질수록 사용자가 필요한 규정을 빠르게 찾기 어렵다.
- LLM 단독 답변은 문서 근거가 없는 hallucination 위험이 있다.

## 내가 맡은 역할
- ingestion 파이프라인 설계 및 구현
- BM25 + dense retrieval 하이브리드 검색 구현
- heuristic reranker와 no-answer/guard 정책 설계
- JSONL 기반 자동 평가와 HTML 리포트 생성
- Streamlit 데모 및 운영 지표 대시보드 구현

## 기술 스택
Python, FastAPI, SQLite, Streamlit, BM25, dense retrieval, Docker

## 핵심 기능
- PDF/TXT/DOCX 업로드 및 파싱
- 청크 분할 및 인덱싱
- 질문-응답 with citation
- guard 기반 비근거 요청 차단
- 자동 평가 및 운영 지표 확인

## 성과
- Retrieval / Keyword / Citation / No-answer / Status 지표 기반 평가 체계 구축
- JSON + HTML 리포트 자동 생성으로 발표 준비 시간 단축
- 최근 질문/문서 활용도/피드백을 보는 운영 대시보드 구현

## 한계와 개선 방향
- 현재는 extractive answer baseline
- 실제 dense embedding 모델과 cross-encoder reranker 고도화 예정
- OCR/HWP/표 인식 확장 예정
