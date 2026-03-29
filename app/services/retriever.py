from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from app.core.config import get_settings
from app.models.schemas import RetrievedChunk

LOGGER = logging.getLogger(__name__)


def simple_tokenize(text: str) -> list[str]:
    """한국어/영문 혼합 문장을 위한 가벼운 토크나이저입니다."""
    base_tokens = re.findall(r"[가-힣A-Za-z0-9]+", text.lower())
    tokens: list[str] = []
    for token in base_tokens:
        tokens.append(token)

        korean_only = re.sub(r"[^가-힣]", "", token)
        alnum = re.sub(r"[^가-힣A-Za-z0-9]", "", token)

        for compact, n_values in ((korean_only, (2, 3)), (alnum, (3, 4))):
            for n in n_values:
                if len(compact) >= n:
                    tokens.extend(compact[i : i + n] for i in range(len(compact) - n + 1))
    return tokens


def slugify_for_path(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip().lower())
    return value.strip("-") or "default"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass
class ChunkRow:
    chunk_id: int
    document_id: int
    document_title: str
    page_number: int
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class SimpleBM25:
    def __init__(self, corpus_tokens: list[list[str]], k1: float = 1.5, b: float = 0.75) -> None:
        self.corpus_tokens = corpus_tokens
        self.k1 = k1
        self.b = b
        self.doc_lens = [len(doc) for doc in corpus_tokens]
        self.avgdl = sum(self.doc_lens) / len(self.doc_lens) if self.doc_lens else 0.0
        self.doc_freqs: list[Counter[str]] = [Counter(doc) for doc in corpus_tokens]
        self.df: Counter[str] = Counter()
        for freqs in self.doc_freqs:
            for token in freqs.keys():
                self.df[token] += 1
        self.N = len(corpus_tokens)

    def idf(self, token: str) -> float:
        n_q = self.df.get(token, 0)
        return math.log(1 + (self.N - n_q + 0.5) / (n_q + 0.5))

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        scores: list[float] = []
        for doc_freq, doc_len in zip(self.doc_freqs, self.doc_lens):
            score = 0.0
            for token in query_tokens:
                tf = doc_freq.get(token, 0)
                if tf == 0:
                    continue
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl if self.avgdl else 0))
                score += self.idf(token) * (tf * (self.k1 + 1)) / denominator
            scores.append(score)
        return scores


class BM25Retriever:
    def __init__(self) -> None:
        self.chunk_rows: list[ChunkRow] = []
        self.corpus_tokens: list[list[str]] = []
        self.bm25: SimpleBM25 | None = None

    def rebuild(self, chunk_rows: list[ChunkRow]) -> None:
        self.chunk_rows = chunk_rows
        self.corpus_tokens = [simple_tokenize(row.content) for row in self.chunk_rows]
        self.bm25 = SimpleBM25(self.corpus_tokens) if self.corpus_tokens else None

    def search_scores(self, query: str, top_k: int = 20) -> list[tuple[int, float]]:
        if not self.bm25 or not self.chunk_rows:
            return []

        tokenized_query = simple_tokenize(query)
        if not tokenized_query:
            return []

        scores = self.bm25.get_scores(tokenized_query)
        indexed_scores = [(idx, float(score)) for idx, score in enumerate(scores) if float(score) > 0]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        return indexed_scores[:top_k]


class HashEmbeddingEncoder:
    """
    외부 모델 다운로드 없이 동작하는 경량 벡터 인코더입니다.
    진짜 semantic embedding은 아니지만, BM25와 다른 scoring surface를 제공해
    하이브리드 검색 baseline을 빠르게 만들기 좋습니다.
    """

    backend_name = "hash"

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim
        self.model_name = f"local-hash-{dim}"

    def _index_and_sign(self, token: str) -> tuple[int, float]:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, "little", signed=False)
        index = value % self.dim
        sign = 1.0 if ((value >> 1) & 1) == 0 else -1.0
        return index, sign

    def encode_one(self, text: str) -> np.ndarray:
        tokens = simple_tokenize(text)
        vector = np.zeros(self.dim, dtype=np.float32)
        if not tokens:
            return vector

        counts = Counter(tokens)
        for token, count in counts.items():
            index, sign = self._index_and_sign(token)
            vector[index] += sign * (1.0 + math.log1p(count))

        norm = float(np.linalg.norm(vector))
        if norm > 0:
            vector /= norm
        return vector

    def encode_many(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.vstack([self.encode_one(text) for text in texts])


class SentenceTransformerEncoder:
    backend_name = "sentence_transformers"

    def __init__(self, model_name: str, batch_size: int = 32) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self._model = None
        self.dim: int | None = None

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers가 설치되지 않았습니다. `pip install -r requirements-optional.txt` 후 다시 시도하세요."
            ) from exc

        self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode_many(self, texts: list[str]) -> np.ndarray:
        if not texts:
            if self.dim is None:
                return np.zeros((0, 0), dtype=np.float32)
            return np.zeros((0, self.dim), dtype=np.float32)

        model = self._load_model()
        embeddings = model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        vectors = np.asarray(embeddings, dtype=np.float32)
        self.dim = int(vectors.shape[1]) if vectors.ndim == 2 else None
        return vectors

    def encode_one(self, text: str) -> np.ndarray:
        vectors = self.encode_many([text])
        if vectors.shape[0] == 0:
            return np.zeros((self.dim or 0,), dtype=np.float32)
        return vectors[0]


class VectorRetriever:
    def __init__(self, dim: int = 384) -> None:
        self.settings = get_settings()
        self.dim = dim
        self.chunk_rows: list[ChunkRow] = []
        self.embeddings = np.zeros((0, dim), dtype=np.float32)
        self.backend_name = "disabled"
        self.model_name = "disabled"
        self.loaded_from_cache = False
        self.fallback_reason: str | None = None
        self.cache_path: str | None = None
        self.encoder = self._build_encoder()

    def _build_encoder(self):
        backend = self.settings.dense_backend.strip().lower()
        model_name = self.settings.dense_model_name.strip()

        # 예전 설정값 호환
        if model_name.lower().startswith("local-hash") and backend == "hash":
            encoder = HashEmbeddingEncoder(dim=self.settings.dense_embedding_dim)
            self.backend_name = encoder.backend_name
            self.model_name = encoder.model_name
            self.dim = encoder.dim
            return encoder

        if backend in {"hash", "local_hash", "hashed"}:
            encoder = HashEmbeddingEncoder(dim=self.settings.dense_embedding_dim)
            self.backend_name = encoder.backend_name
            self.model_name = encoder.model_name
            self.dim = encoder.dim
            return encoder

        if backend in {"auto", "sentence_transformers", "sentence-transformers", "sbert"}:
            try:
                encoder = SentenceTransformerEncoder(
                    model_name=model_name,
                    batch_size=self.settings.embedding_batch_size,
                )
                self.backend_name = encoder.backend_name
                self.model_name = model_name
                return encoder
            except Exception as exc:  # pragma: no cover - optional dependency fallback
                self.fallback_reason = str(exc)
                LOGGER.warning("sentence-transformers 로드 실패, hash encoder로 대체합니다: %s", exc)
                encoder = HashEmbeddingEncoder(dim=self.settings.dense_embedding_dim)
                self.backend_name = encoder.backend_name
                self.model_name = encoder.model_name
                self.dim = encoder.dim
                return encoder

        self.fallback_reason = f"알 수 없는 dense backend: {backend}. hash encoder로 대체합니다."
        LOGGER.warning(self.fallback_reason)
        encoder = HashEmbeddingEncoder(dim=self.settings.dense_embedding_dim)
        self.backend_name = encoder.backend_name
        self.model_name = encoder.model_name
        self.dim = encoder.dim
        return encoder

    def _cache_file_stem(self) -> str:
        backend = slugify_for_path(self.backend_name)
        model = slugify_for_path(self.model_name)
        return f"{backend}_{model}"

    def _cache_paths(self) -> tuple[Path, Path]:
        index_dir = Path(self.settings.index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)
        stem = self._cache_file_stem()
        manifest_path = index_dir / f"{stem}.manifest.json"
        array_path = index_dir / f"{stem}.embeddings.npz"
        self.cache_path = str(array_path)
        return manifest_path, array_path

    def _corpus_payload(self, texts: list[str]) -> dict[str, Any]:
        corpus_hash = hashlib.sha256()
        for row, text in zip(self.chunk_rows, texts):
            corpus_hash.update(str(row.chunk_id).encode("utf-8"))
            corpus_hash.update(sha256_text(text).encode("utf-8"))
        return {
            "backend_name": self.backend_name,
            "model_name": self.model_name,
            "chunk_count": len(texts),
            "corpus_hash": corpus_hash.hexdigest(),
        }

    def _load_cache(self, payload: dict[str, Any]) -> bool:
        if not self.settings.embedding_cache_enabled:
            return False

        manifest_path, array_path = self._cache_paths()
        if not manifest_path.exists() or not array_path.exists():
            return False

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest != payload:
                return False
            data = np.load(array_path)
            embeddings = np.asarray(data["embeddings"], dtype=np.float32)
            if embeddings.shape[0] != len(self.chunk_rows):
                return False
            self.embeddings = embeddings
            self.loaded_from_cache = True
            if embeddings.ndim == 2 and embeddings.shape[1] > 0:
                self.dim = int(embeddings.shape[1])
            return True
        except Exception as exc:  # pragma: no cover - cache 손상 대비
            LOGGER.warning("임베딩 캐시 로드 실패: %s", exc)
            return False

    def _save_cache(self, payload: dict[str, Any]) -> None:
        if not self.settings.embedding_cache_enabled or self.embeddings.size == 0:
            return
        manifest_path, array_path = self._cache_paths()
        manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        np.savez_compressed(array_path, embeddings=self.embeddings.astype(np.float32))

    def rebuild(self, chunk_rows: list[ChunkRow]) -> None:
        self.chunk_rows = chunk_rows
        self.loaded_from_cache = False
        texts = [f"{row.document_title}\n{row.content}" for row in self.chunk_rows]
        if not texts:
            self.embeddings = np.zeros((0, self.dim), dtype=np.float32)
            return

        payload = self._corpus_payload(texts)
        if self._load_cache(payload):
            return

        try:
            self.embeddings = np.asarray(self.encoder.encode_many(texts), dtype=np.float32)
        except Exception as exc:
            # sentence-transformers의 실제 로딩은 encode 시점에 일어나므로 이 지점에서 fallback 처리
            if self.backend_name == "sentence_transformers":
                self.fallback_reason = str(exc)
                LOGGER.warning("dense 인코딩 실패, hash encoder로 대체합니다: %s", exc)
                self.encoder = HashEmbeddingEncoder(dim=self.settings.dense_embedding_dim)
                self.backend_name = self.encoder.backend_name
                self.model_name = self.encoder.model_name
                self.dim = self.encoder.dim
                payload = self._corpus_payload(texts)
                self.embeddings = np.asarray(self.encoder.encode_many(texts), dtype=np.float32)
            else:
                raise

        if self.embeddings.ndim == 2 and self.embeddings.shape[1] > 0:
            self.dim = int(self.embeddings.shape[1])
        self._save_cache(payload)

    def search_scores(self, query: str, top_k: int = 20) -> list[tuple[int, float]]:
        if not self.chunk_rows or self.embeddings.size == 0:
            return []
        query_vec = self.encoder.encode_one(query)
        if query_vec.ndim != 1 or float(np.linalg.norm(query_vec)) == 0:
            return []
        scores = self.embeddings @ query_vec
        indexed_scores = [(idx, float(score)) for idx, score in enumerate(scores) if float(score) > 0]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        return indexed_scores[:top_k]


class HeuristicReranker:
    def __init__(self) -> None:
        self.stopwords = {
            "무엇", "인가요", "있나요", "해주세요", "정리", "알려줘", "알려주세요", "필요", "어떻게",
            "어떤", "관련", "기준", "조건", "대상", "문의", "안내", "문서", "해당", "대한",
        }

    def _important_tokens(self, text: str) -> set[str]:
        return {token for token in simple_tokenize(text) if token not in self.stopwords and len(token) > 1}

    def score(self, query: str, row: ChunkRow) -> float:
        query_tokens = self._important_tokens(query)
        if not query_tokens:
            return 0.0

        chunk_tokens = self._important_tokens(row.content)
        title_tokens = self._important_tokens(row.document_title)
        overlap = len(query_tokens & chunk_tokens) / len(query_tokens)
        title_overlap = len(query_tokens & title_tokens) / len(query_tokens)

        normalized_query = re.sub(r"\s+", "", query.lower())
        normalized_content = re.sub(r"\s+", "", row.content.lower())
        substring_bonus = 0.08 if normalized_query and normalized_query[: min(10, len(normalized_query))] in normalized_content else 0.0
        first_page_bonus = 0.03 if row.page_number == 1 else 0.0
        short_penalty = -0.03 if len(row.content) < 40 else 0.0

        return min(0.35, 0.18 * overlap + 0.10 * title_overlap + substring_bonus + first_page_bonus + short_penalty)


class HybridRetriever:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.chunk_rows: list[ChunkRow] = []
        self.bm25 = BM25Retriever()
        self.vector = VectorRetriever(dim=settings.dense_embedding_dim)
        self.reranker = HeuristicReranker()

    def rebuild(self, chunk_dicts: list[dict]) -> None:
        self.chunk_rows = [
            ChunkRow(
                chunk_id=int(item["id"]),
                document_id=int(item["document_id"]),
                document_title=str(item["document_title"]),
                page_number=int(item["page_number"]),
                content=str(item["content"]),
                metadata=item.get("metadata") or {},
            )
            for item in chunk_dicts
        ]
        self.bm25.rebuild(self.chunk_rows)
        if self.settings.enable_dense_retrieval:
            self.vector.rebuild(self.chunk_rows)

    def _normalize(self, scores: list[tuple[int, float]]) -> dict[int, float]:
        if not scores:
            return {}
        max_score = max(score for _, score in scores)
        if max_score <= 0:
            return {idx: 0.0 for idx, _ in scores}
        return {idx: score / max_score for idx, score in scores}

    def _build_result(self, idx: int, final_score: float, rank: int, detail: dict[str, float]) -> RetrievedChunk:
        row = self.chunk_rows[idx]
        return RetrievedChunk(
            chunk_id=row.chunk_id,
            document_id=row.document_id,
            document_title=row.document_title,
            page_number=row.page_number,
            content=row.content,
            score=round(final_score, 4),
            rank=rank,
            metadata={
                "lexical_score": round(detail.get("lexical_score", 0.0), 4),
                "vector_score": round(detail.get("vector_score", 0.0), 4),
                "hybrid_score": round(detail.get("hybrid_score", 0.0), 4),
                "rerank_bonus": round(detail.get("rerank_bonus", 0.0), 4),
                "retrieval_mode": "hybrid" if self.settings.enable_dense_retrieval else "bm25",
                "vector_backend": self.vector.backend_name if self.settings.enable_dense_retrieval else "disabled",
                "vector_model_name": self.vector.model_name if self.settings.enable_dense_retrieval else "disabled",
            },
        )

    def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        if not self.chunk_rows:
            return []

        candidate_pool_size = max(top_k * 4, self.settings.candidate_pool_size)
        lexical_scores = self.bm25.search_scores(query, top_k=candidate_pool_size)
        vector_scores = self.vector.search_scores(query, top_k=candidate_pool_size) if self.settings.enable_dense_retrieval else []

        lexical_norm = self._normalize(lexical_scores)
        vector_norm = self._normalize(vector_scores)
        candidate_ids = set(lexical_norm) | set(vector_norm)

        if not candidate_ids:
            return []

        scored_candidates: list[tuple[int, float, dict[str, float]]] = []
        for idx in candidate_ids:
            lexical_score = lexical_norm.get(idx, 0.0)
            vector_score = vector_norm.get(idx, 0.0)
            hybrid_score = (
                self.settings.hybrid_alpha * lexical_score + (1 - self.settings.hybrid_alpha) * vector_score
                if self.settings.enable_dense_retrieval
                else lexical_score
            )
            rerank_bonus = self.reranker.score(query, self.chunk_rows[idx])
            final_score = min(1.0, max(0.0, hybrid_score + rerank_bonus))
            scored_candidates.append(
                (
                    idx,
                    final_score,
                    {
                        "lexical_score": lexical_score,
                        "vector_score": vector_score,
                        "hybrid_score": hybrid_score,
                        "rerank_bonus": rerank_bonus,
                    },
                )
            )

        scored_candidates.sort(key=lambda item: item[1], reverse=True)

        results: list[RetrievedChunk] = []
        for rank, (idx, final_score, detail) in enumerate(scored_candidates[:top_k], start=1):
            results.append(self._build_result(idx=idx, final_score=final_score, rank=rank, detail=detail))
        return results

    def describe(self) -> dict[str, Any]:
        return {
            "dense_enabled": self.settings.enable_dense_retrieval,
            "dense_backend": self.vector.backend_name if self.settings.enable_dense_retrieval else "disabled",
            "dense_model_name": self.vector.model_name if self.settings.enable_dense_retrieval else "disabled",
            "dense_encoder_dim": self.vector.dim if self.settings.enable_dense_retrieval else None,
            "embedding_cache_enabled": self.settings.embedding_cache_enabled,
            "embedding_cache_path": self.vector.cache_path if self.settings.enable_dense_retrieval else None,
            "loaded_from_cache": self.vector.loaded_from_cache if self.settings.enable_dense_retrieval else False,
            "fallback_reason": self.vector.fallback_reason if self.settings.enable_dense_retrieval else None,
        }
