# GitHub 업로드 가이드

## 저장소 이름 추천
- `korean-rag-knowledge-assistant`
- `public-doc-rag-assistant`
- `korean-rag-portfolio`

## About 문구 예시
### 한글
공공 문서와 공개 웹문서를 대상으로 한 한국어 RAG 지식도우미입니다. 문서 적재, 하이브리드 검색, citation 기반 응답, guardrail, 평가 리포트, 운영 지표, Streamlit 데모까지 포함한 포트폴리오 프로젝트입니다.

### 영어
Korean RAG assistant for public-style documents and public web pages. The project covers ingestion, hybrid retrieval, grounded responses with citations, guardrails, evaluation reports, analytics, and a demo UI.

## 토픽 추천
- rag
- fastapi
- streamlit
- korean-nlp
- retrieval-augmented-generation
- information-retrieval
- portfolio
- mlops

## 올리기 전에 지울 것
- `.env`
- `storage/app.db`
- `storage/index/*`
- `storage/evals/*`
- `storage/raw/web_imports/*`

## 첫 커밋 전 체크
1. `make reset`
2. `make seed && make ingest`
3. `make smoke`
4. `make test`
5. README 이미지 / 평가 결과 / 데모 캡처 확인
6. GitHub About / Topics 입력

## 커밋 메시지 예시
- `feat: add public web document ingestion`
- `feat: add hybrid retrieval and grounded answer flow`
- `test: add smoke and web loader tests`
- `docs: finalize github and portfolio materials`
