# 예상 면접 질문과 답변 포인트

## 왜 RAG를 선택했나요?
- 포트폴리오에서 모델 사용보다 문제 정의, 검색, 근거 제시, 평가, 운영까지 보여주기 좋기 때문입니다.
- 공공 문서 도메인은 출처 기반 답변의 가치가 분명합니다.

## 왜 추출형 답변으로 시작했나요?
- 초기 단계에서 hallucination을 줄이고 retrieval 품질을 먼저 검증하기 위해서입니다.
- 이후 생성형 LLM으로 교체할 때 baseline 비교가 쉬워집니다.

## 하이브리드 검색을 쓴 이유는 무엇인가요?
- BM25는 키워드/고유명사에 강하고 dense retrieval은 의미 유사도에 강합니다.
- 둘을 결합하면 recall과 robustness를 동시에 확보하기 좋습니다.

## guard를 넣은 이유는 무엇인가요?
- 문서 밖 질문이나 프롬프트 인젝션 요청에 대해 안전하게 답변을 보류해야 포트폴리오가 더 실무적으로 보입니다.
- 특히 RAG에서는 groundedness를 깨는 요청을 별도로 통제할 필요가 있습니다.

## 평가셋은 어떻게 만들었나요?
- 핵심/일반/문서밖/no-answer/guard 케이스를 섞어서 JSONL로 만들었습니다.
- retrieval, keyword, citation, no-answer, status 지표를 함께 봤습니다.

## 다음 개선 계획은 무엇인가요?
- sentence-transformers 임베딩 고도화
- cross-encoder reranker
- 생성형 답변과 answer faithfulness 평가
- HWP/OCR/표 인식 파이프라인 추가
