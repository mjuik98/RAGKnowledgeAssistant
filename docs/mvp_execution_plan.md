# MVP 구현 순서

## 0. 범위 고정
- 도메인: 공공 민원 / 기관 안내문 / 학사 규정 중 하나 선택
- 파일 형식: PDF, TXT, DOCX
- 답변 정책: 문서 기반 근거가 없으면 no-answer

## 1. 문서 수집
- 공개 문서 20~50개 수집
- 파일명 규칙 통일
- 최신/구버전 구분
- 너무 긴 문서는 장/절 기준으로 분리 고려

## 2. ingestion
- 파일 업로드
- 디렉터리 일괄 적재
- 텍스트 추출
- 페이지별 저장
- 청크 분할
- checksum 기반 중복 방지

## 3. 검색
- 하이브리드 검색 baseline(BM25 + hash vector)
- top_k 5~10 실험
- heuristic reranker 적용
- 실패 질문 수집
- 실제 dense embedding 모델은 2차 적용

## 4. 답변 생성
- 추출형 답변으로 시작
- 근거 citation 포함
- no-answer 임계값 튜닝
- 문서 밖 질문 차단 정책 추가

## 5. 평가
- 골드 질문 80~120개 작성
- 핵심 / 일반 / 엣지 / 공격 질문 분리
- retrieval hit, keyword hit, citation hit, no-answer 정확도 측정
- latency와 실패 사례 로그 정리

## 6. 발표 자료
- 시스템 구조도
- API 흐름도
- 평가표
- 실패 예시 3개
- 개선 전/후 비교

## 7. 확장 우선순위
1. sentence-transformers 임베딩 교체
2. Cross-encoder reranker
3. LLM 생성형 답변
4. Docker 배포
5. 대시보드
6. OCR / HWP / 표 인식
