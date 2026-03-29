from __future__ import annotations

import re
from typing import Iterable

from app.core.config import get_settings
from app.models.schemas import Citation, RetrievedChunk
from app.services.retriever import simple_tokenize


def split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+|(?<=다)\s+|(?<=요)\s+", text)
    return [part.strip() for part in parts if part.strip()]


class ExtractiveAnswerGenerator:
    """검색된 근거에서 질문과 가장 가까운 문장을 뽑아 답변을 구성합니다."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.stopwords = {
            "무엇", "인가요", "있나요", "해주세요", "정리", "알려줘", "알려주세요", "필요", "어떻게",
            "어떤", "관련", "기준", "조건", "대상", "문의", "안내", "문서", "해당", "대한", "위해",
            "뭐야", "누구야", "언제야", "얼마야", "얼마", "있어", "추가로", "추가", "게", "때", "까지", "받을", "말고",
            "필요한", "서류",
        }
        self.particle_suffixes = [
            "으로", "에서", "에게", "한테", "부터", "까지", "라고", "이라면", "이면", "입니다",
            "하는", "하다", "하며", "하고", "하면", "했다", "한다", "할", "한", "를", "을", "은", "는",
            "이", "가", "에", "의", "도", "와", "과", "로", "야", "요",
        ]

    def _normalize_coarse_token(self, token: str) -> str:
        normalized = token.lower()
        for suffix in self.particle_suffixes:
            if len(normalized) > len(suffix) + 1 and normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)]
                break
        return normalized

    def _query_tokens(self, question: str) -> set[str]:
        return {token for token in simple_tokenize(question) if token not in self.stopwords and len(token) > 1}

    def _coarse_tokens(self, text: str) -> set[str]:
        tokens: set[str] = set()
        for raw_token in re.findall(r"[가-힣A-Za-z0-9]+", text.lower()):
            normalized = self._normalize_coarse_token(raw_token)
            if normalized not in self.stopwords and len(normalized) > 1:
                tokens.add(normalized)
        return tokens

    def _coarse_overlap(self, question_tokens: set[str], text: str) -> float:
        if not question_tokens:
            return 0.0
        content_tokens = self._coarse_tokens(text)
        return len(question_tokens & content_tokens) / len(question_tokens)

    def _sentence_score(self, sentence: str, question_tokens: set[str], chunk_score: float) -> float:
        sentence_tokens = {token for token in simple_tokenize(sentence) if len(token) > 1}
        overlap = len(question_tokens & sentence_tokens) / len(question_tokens) if question_tokens else 0.0
        length_penalty = -0.05 if len(sentence) < 15 else 0.0
        return 0.35 * chunk_score + 0.65 * overlap + length_penalty

    def generate(self, question: str, retrieved_chunks: Iterable[RetrievedChunk]) -> tuple[str, str, list[Citation]]:
        chunks = list(retrieved_chunks)
        if not chunks:
            return "제공된 문서에서 확인할 수 없습니다.", "no_answer", []

        top_chunk = chunks[0]
        if top_chunk.score < self.settings.min_retrieval_score:
            return "제공된 문서에서 확인할 수 없습니다.", "no_answer", []

        lexical_score = float(top_chunk.metadata.get("lexical_score", top_chunk.score))
        rerank_bonus = float(top_chunk.metadata.get("rerank_bonus", 0.0))
        if lexical_score == 0.0 and top_chunk.score < 0.45 and rerank_bonus < 0.08:
            return "제공된 문서에서 확인할 수 없습니다.", "no_answer", []

        question_tokens = self._query_tokens(question)
        coarse_question_tokens = self._coarse_tokens(question)
        top_chunk_overlap = self._coarse_overlap(
            coarse_question_tokens,
            f"{top_chunk.document_title} {top_chunk.content}",
        )
        if coarse_question_tokens and top_chunk_overlap < 0.45:
            return "제공된 문서에서 확인할 수 없습니다.", "no_answer", []

        support_candidates: list[tuple[float, str, RetrievedChunk]] = []
        seen_sentences: set[str] = set()

        for chunk in chunks[:4]:
            chunk_overlap = self._coarse_overlap(coarse_question_tokens, f"{chunk.document_title} {chunk.content}")
            if chunk.chunk_id != top_chunk.chunk_id and chunk_overlap < max(0.35, top_chunk_overlap - 0.2):
                continue

            sentences = split_sentences(chunk.content)
            if not sentences:
                sentences = [chunk.content[:180]]
            for sentence in sentences[:6]:
                normalized = re.sub(r"\s+", " ", sentence).strip().lower()
                if not normalized or normalized in seen_sentences:
                    continue
                sentence_overlap = self._coarse_overlap(coarse_question_tokens, sentence)
                if chunk.chunk_id != top_chunk.chunk_id and sentence_overlap == 0.0:
                    continue
                seen_sentences.add(normalized)
                support_candidates.append((self._sentence_score(sentence, question_tokens, chunk.score), sentence, chunk))

        support_candidates.sort(key=lambda item: item[0], reverse=True)
        selected = support_candidates[:3]

        if not selected or selected[0][0] < max(self.settings.min_retrieval_score, 0.20):
            return "제공된 문서에서 확인할 수 없습니다.", "no_answer", []

        answer_lines: list[str] = ["문서에서 직접 확인된 핵심 내용입니다."]
        citations: list[Citation] = []
        used_chunk_ids: set[int] = set()

        for idx, (_, sentence, chunk) in enumerate(selected, start=1):
            answer_lines.append(f"{idx}. {sentence}")
            if chunk.chunk_id not in used_chunk_ids:
                used_chunk_ids.add(chunk.chunk_id)
                citations.append(
                    Citation(
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        document_title=chunk.document_title,
                        page_number=chunk.page_number,
                        score=chunk.score,
                    )
                )

        answer_lines.append("최종 신청 요건이나 최신 개정 여부는 출처 페이지를 함께 확인하세요.")
        return "\n".join(answer_lines), "grounded_answer", citations
