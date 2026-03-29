# 공공 문서 기반 한국어 RAG 지식도우미

포트폴리오 제출을 목표로 만든 **문서 기반 한국어 RAG 프로젝트**입니다. 단순 챗봇 데모가 아니라, 문서 적재부터 검색·근거 기반 응답·가드레일·평가·운영 지표까지 한 번에 보여주는 **제출형 스타터 저장소**로 정리했습니다.

![RAG Pipeline Overview](docs/assets/rag_pipeline_overview.png)

## 한 줄 소개
공공 문서와 공개 웹문서를 적재하고, 질문에 대해 **citation이 포함된 grounded answer**를 반환하는 한국어 RAG 지식도우미입니다.

## 이 프로젝트에서 보여주는 역량
- **Ingestion**: PDF / TXT / DOCX 업로드, 공개 URL 스냅샷 적재
- **Retrieval**: BM25 + dense retrieval(hash / sentence-transformers) + heuristic reranking
- **Answering**: extractive grounded answer + citation
- **Safety**: no-answer, 문서 밖 질문 차단, prompt injection 차단
- **Ops**: query log, feedback, analytics summary API
- **Eval**: JSONL 평가셋 실행, JSON / HTML 리포트 생성
- **Demo**: FastAPI + Streamlit 분리 구조

## 완료된 1차 범위
- PDF / TXT / DOCX 파싱
- URL → TXT 스냅샷 적재
- 청크 분할 및 SQLite 저장
- BM25 + dense retrieval 하이브리드 검색
- heuristic reranker
- citation 포함 추출형 답변
- guard_blocked / no_answer 처리
- 평가셋 실행 및 HTML 리포트 생성
- 운영 현황 조회 API와 Streamlit 데모
- smoke test / unittest / GitHub Actions

## 빠른 시작
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
make reset
make seed
make ingest
make run
```

실행 후 확인할 주소
- API 문서: `http://127.0.0.1:8000/docs`
- 헬스체크: `GET /health`
- 인덱스 상태: `GET /system/index`
- 운영 지표: `GET /analytics/summary`

Streamlit 데모 UI
```bash
pip install -r requirements-optional.txt
make demo
```
- 데모 화면: `http://127.0.0.1:8501`

## 공개 웹문서 적재
### 단건 적재
```bash
curl -X POST "http://127.0.0.1:8000/documents/ingest-url"   -H "Content-Type: application/json"   -d '{
    "url": "https://www.gov.kr/portal/locgovNews/4679243?hideurl=N",
    "title_hint": "희망디딤돌 인천센터 자립생활실 입주자 상시모집 안내",
    "filename_hint": "hope_stepping_stone_incheon_housing"
  }'
```

### URL 매니페스트 일괄 적재
```bash
make ingest-public
```
또는
```bash
python scripts/ingest_url_manifest.py --manifest data/corpus/public_service_manifest.csv
```

적재 결과
- 스냅샷 파일: `storage/raw/web_imports/*.txt`
- 검색 인덱스: SQLite + BM25 + dense cache

> `data/corpus/public_service_manifest.csv`는 시작용 예시 매니페스트입니다. 실제 제출본에서는 본인이 검토한 기관 공지와 정책 페이지로 교체하는 편이 좋습니다.

## 평가 실행
```bash
make eval-portfolio
```
또는
```bash
curl -X POST "http://127.0.0.1:8000/evals/run"   -H "Content-Type: application/json"   -d '{
    "eval_file_path": "data/eval/portfolio_eval.jsonl",
    "save_report": true
  }'
```

리포트 저장 위치
- `storage/evals/*.json`
- `storage/evals/*.html`
- 예시 리포트: [`docs/sample_eval_report.html`](docs/sample_eval_report.html)

## 폴더 구조
```text
rag_knowledge_assistant_starter/
├─ app/
│  ├─ api/
│  ├─ core/
│  ├─ db/
│  ├─ models/
│  ├─ services/
│  │  ├─ evaluator.py
│  │  ├─ generator.py
│  │  ├─ guard.py
│  │  ├─ ingestion.py
│  │  ├─ parser.py
│  │  ├─ pipeline.py
│  │  ├─ reporting.py
│  │  ├─ repository.py
│  │  ├─ retriever.py
│  │  └─ web_loader.py
│  └─ main.py
├─ data/
│  ├─ corpus/
│  │  └─ public_service_manifest.csv
│  └─ eval/
├─ docs/
│  ├─ assets/
│  ├─ demo_script.md
│  ├─ final_submission_checklist.md
│  ├─ github_publish_guide.md
│  ├─ interview_qa.md
│  ├─ official_public_corpus_guide.md
│  ├─ portfolio_intro_ko.md
│  ├─ portfolio_writeup_template.md
│  ├─ resume_bullets.md
│  └─ sample_eval_report.html
├─ scripts/
│  ├─ ingest_directory.py
│  ├─ ingest_url_manifest.py
│  ├─ reset_demo_state.py
│  ├─ run_local_eval.py
│  ├─ seed_sample_documents.py
│  └─ smoke_test.py
├─ storage/
├─ tests/
├─ ui/
├─ .github/workflows/tests.yml
├─ Dockerfile
├─ LICENSE
├─ Makefile
└─ README.md
```

## 발표 포인트
1. 문서 적재와 검색, 답변, 평가, 운영을 분리해서 설계했습니다.
2. 문서 밖 질문과 프롬프트 인젝션은 `guard_blocked`로 차단합니다.
3. 답변에는 citation을 붙이고, 근거가 약하면 `no_answer`를 우선합니다.
4. 평가 결과를 HTML로 저장해 발표 캡처와 README 링크에 바로 활용할 수 있습니다.
5. 실제 웹 공지 페이지를 TXT 스냅샷으로 정규화해 corpus에 넣을 수 있습니다.


## 로컬 검증 결과
- `python -m unittest discover -s tests -v` → **7개 테스트 통과**
- `python scripts/smoke_test.py` → 샘플 문서 적재 / grounded_answer / guard_blocked 확인
- `python scripts/run_local_eval.py --eval-file data/eval/portfolio_eval.jsonl` → **13문항 평가 통과**
  - Retrieval Hit Rate: **100%**
  - Keyword Hit Rate: **100%**
  - Citation Hit Rate: **100%**
  - No-answer 정확도: **100%**
  - 평균 응답 시간: **3.47ms**

> 위 수치는 **hash backend 기준 로컬 검증 결과**입니다. `sentence-transformers` 경로는 옵션으로 제공되며, 실제 모델 다운로드가 필요한 환경에서 다시 검증하는 것을 권장합니다.

## GitHub / 포트폴리오 문서
- GitHub 업로드 가이드: [`docs/github_publish_guide.md`](docs/github_publish_guide.md)
- 포트폴리오 소개글: [`docs/portfolio_intro_ko.md`](docs/portfolio_intro_ko.md)
- 이력서 bullet: [`docs/resume_bullets.md`](docs/resume_bullets.md)
- 발표 스크립트: [`docs/demo_script.md`](docs/demo_script.md)
- 예상 면접 질문: [`docs/interview_qa.md`](docs/interview_qa.md)
- 제출 체크리스트: [`docs/final_submission_checklist.md`](docs/final_submission_checklist.md)
- 검증 기록: [`docs/validation_report.md`](docs/validation_report.md)
