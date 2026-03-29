# 로컬 검증 기록

이 문서는 v6 패키지 기준으로 실제 실행한 검증 항목을 정리한 것입니다.

## 1. 단위 테스트

실행 명령:

```bash
python -m unittest discover -s tests -v
```

결과:
- 총 7개 테스트 통과
- guard / generator / reporting 테스트 유지
- web loader 테스트 2개 통과

## 2. 스모크 테스트

실행 명령:

```bash
python scripts/smoke_test.py
```

결과:
- 샘플 문서 6건 적재 성공
- grounded_answer 응답 확인
- guard_blocked 응답 확인
- `data/eval/smoke_eval.jsonl` 생성 확인

## 3. 포트폴리오 평가 실행

실행 명령:

```bash
python scripts/run_local_eval.py --eval-file data/eval/portfolio_eval.jsonl
```

결과:
- 문항 수: 13
- Dense backend: hash
- Dense model: local-hash-384
- Retrieval Hit Rate: 100%
- Keyword Hit Rate: 100%
- Citation Hit Rate: 100%
- No-answer 정확도: 100%
- 평균 응답 시간: 3.47ms

생성 산출물:
- `storage/evals/portfolio_eval_20260329_104754.json`
- `storage/evals/portfolio_eval_20260329_104754.html`

## 4. 참고
- 위 결과는 **hash backend 기준**입니다.
- `sentence-transformers` 경로는 옵션으로 제공되며, 모델 다운로드가 가능한 환경에서 추가 검증이 필요합니다.
