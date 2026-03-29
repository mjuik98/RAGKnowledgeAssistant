from __future__ import annotations

from typing import Any

from pydantic import AnyHttpUrl, BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app_name: str


class UploadDocumentResponse(BaseModel):
    document_id: int
    title: str
    total_pages: int
    chunk_count: int
    existed: bool = False


class IngestUrlRequest(BaseModel):
    url: AnyHttpUrl
    title_hint: str | None = Field(default=None, max_length=200)
    filename_hint: str | None = Field(default=None, max_length=120)


class Citation(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str
    page_number: int
    score: float


class RetrievedChunk(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str
    page_number: int
    content: str
    score: float
    rank: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2)
    top_k: int = Field(default=5, ge=1, le=20)


class ChatResponse(BaseModel):
    answer: str
    status: str
    citations: list[Citation]
    retrieved_chunks: list[RetrievedChunk]
    latency_ms: float | None = None
    query_id: int | None = None
    guard_reason: str | None = None


class FeedbackRequest(BaseModel):
    query_id: int = Field(..., ge=1)
    rating: int = Field(..., ge=-1, le=1)
    comment: str | None = Field(default=None, max_length=1000)


class FeedbackResponse(BaseModel):
    status: str
    feedback_id: int


class IndexInfoResponse(BaseModel):
    document_count: int
    chunk_count: int
    dense_enabled: bool
    dense_backend: str
    dense_model_name: str
    dense_encoder_dim: int | None = None
    embedding_cache_enabled: bool
    embedding_cache_path: str | None = None
    loaded_from_cache: bool = False
    fallback_reason: str | None = None


class EvalRunRequest(BaseModel):
    eval_file_path: str
    save_report: bool = True


class EvalItemResult(BaseModel):
    question: str
    predicted_answer: str
    status: str
    retrieval_hit: bool
    keyword_hit: bool
    citation_hit: bool | None = None
    no_answer_correct: bool | None = None
    status_match: bool | None = None
    latency_ms: float | None = None
    notes: str | None = None


class EvalRunResponse(BaseModel):
    eval_name: str
    total_count: int
    retrieval_hit_rate: float
    keyword_hit_rate: float
    citation_hit_rate: float | None = None
    no_answer_accuracy: float | None = None
    status_hit_rate: float | None = None
    average_latency_ms: float | None = None
    report_path: str | None = None
    html_report_path: str | None = None
    results: list[EvalItemResult]


class ParsedPage(BaseModel):
    page_number: int
    text: str


class ParsedDocument(BaseModel):
    title: str
    original_filename: str
    source_path: str
    source_type: str
    checksum: str
    pages: list[ParsedPage]


class ChunkRecord(BaseModel):
    document_id: int
    page_number: int
    chunk_index: int
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class LatestEvalSummary(BaseModel):
    eval_name: str
    total_count: int
    retrieval_hit_rate: float
    keyword_hit_rate: float
    citation_hit_rate: float | None = None
    no_answer_accuracy: float | None = None
    average_latency_ms: float | None = None
    created_at: str
    report_path: str | None = None


class AnalyticsSummaryResponse(BaseModel):
    document_count: int
    chunk_count: int
    total_queries: int
    grounded_answer_count: int
    no_answer_count: int
    guard_blocked_count: int
    average_latency_ms: float | None = None
    feedback_count: int
    positive_feedback_count: int
    negative_feedback_count: int
    neutral_feedback_count: int
    latest_eval: LatestEvalSummary | None = None


class RecentQueryItem(BaseModel):
    query_id: int
    question: str
    status: str
    latency_ms: float
    created_at: str
    feedback_rating: int | None = None
    feedback_comment: str | None = None
    top_document_title: str | None = None


class EvalRunListItem(BaseModel):
    eval_run_id: int
    eval_name: str
    total_count: int
    retrieval_hit_rate: float
    keyword_hit_rate: float
    citation_hit_rate: float | None = None
    no_answer_accuracy: float | None = None
    average_latency_ms: float | None = None
    created_at: str
    report_path: str | None = None


class DocumentUsageItem(BaseModel):
    document_id: int
    document_title: str
    source_type: str
    total_pages: int
    chunk_count: int
    retrieval_count: int
