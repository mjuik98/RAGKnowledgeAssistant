# Streamlit 데모 가이드

## 1. 설치
기본 API만 실행하려면 `requirements.txt`만 설치하면 됩니다.
데모 화면과 실제 임베딩 모델까지 같이 쓰려면 아래를 추가 설치합니다.

```bash
pip install -r requirements-optional.txt
```

## 2. API 실행
```bash
uvicorn app.main:app --reload
```

## 3. 데모 실행
새 터미널에서:

```bash
streamlit run ui/streamlit_app.py
```

기본 API 주소는 `http://127.0.0.1:8000` 입니다.
다른 주소를 쓰고 있다면 좌측 사이드바에서 바꿀 수 있습니다.

## 4. 탭별 시연 포인트
### 질문하기
1. 샘플 문서 업로드
2. 질문 실행
3. 답변과 출처 확인
4. retrieved chunk 펼쳐서 근거 확인
5. 좋아요/별로예요 피드백 저장

### 운영 현황
1. 누적 질문 수와 평균 응답 시간 확인
2. grounded / no-answer / guard blocked 비율 확인
3. 최근 질문 목록과 문서 활용도 확인
4. 최근 평가 결과 확인

### 평가
1. `data/eval/portfolio_eval.jsonl` 입력
2. 평가 실행
3. Retrieval / Keyword / Citation / Status 지표 확인
4. 생성된 JSON / HTML 리포트 경로 확인

## 5. 실제 임베딩 모델 켜기
`.env`를 아래처럼 바꾸고 API를 다시 시작합니다.

```env
ENABLE_DENSE_RETRIEVAL=true
DENSE_BACKEND=sentence_transformers
DENSE_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_CACHE_ENABLED=true
```

최초 한 번은 모델 다운로드와 임베딩 계산 때문에 시간이 더 걸릴 수 있습니다.
이후에는 `storage/index`의 캐시를 재사용합니다.
