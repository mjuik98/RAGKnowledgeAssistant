# 평가셋 작성 가이드

## 권장 JSONL 스키마

각 줄은 하나의 JSON 객체입니다.

```json
{
  "question": "전입신고에 필요한 서류가 뭐야?",
  "must_include": ["신분증"],
  "must_not_include": ["여권"],
  "expected_document_titles": ["sample_notice"],
  "expected_no_answer": false,
  "expected_status": "grounded_answer",
  "acceptable_statuses": ["grounded_answer"],
  "notes": "핵심 규정 질문"
}
```

## 필드 설명
- `question`: 실제 사용자 질문
- `must_include`: 답변에 반드시 포함되어야 하는 핵심 키워드
- `must_not_include`: 답변에 포함되면 안 되는 키워드
- `expected_document_titles`: citation에 포함되길 기대하는 문서 제목 목록
- `expected_no_answer`: 근거가 없을 때 no-answer 계열 응답이 나와야 하는지 여부
- `expected_status`: 기대 상태값 하나를 지정할 때 사용
- `acceptable_statuses`: 허용 가능한 상태값 목록. `grounded_answer`, `no_answer`, `guard_blocked`를 주로 사용
- `notes`: 사람 검토용 메모

## 상태값 추천 규칙
- 일반 질의응답: `acceptable_statuses: ["grounded_answer"]`
- 문서 밖 질문: `acceptable_statuses: ["no_answer"]`
- 프롬프트 인젝션/비근거 요청: `acceptable_statuses: ["guard_blocked"]`

## 추천 구성 비율
- 핵심 질문 40%
- 일반 질문 30%
- 엣지 케이스 20%
- 공격/문서밖 질문 10%

## 평가 지표 해석
- `retrieval_hit_rate`: 기대 문서가 citation에 포함되는 비율
- `keyword_hit_rate`: 정답 핵심 키워드를 포함하는 비율
- `citation_hit_rate`: citation 기대치 충족 여부
- `no_answer_accuracy`: 답변 보류가 맞게 동작한 비율
- `status_hit_rate`: 기대 상태값과 실제 상태값이 맞는 비율

## 리포트 산출물
평가를 실행하면 `storage/evals` 아래에 아래 파일이 함께 생성됩니다.
- `*.json`: 원본 결과 저장용
- `*.html`: 발표/캡처용 대시보드 리포트
