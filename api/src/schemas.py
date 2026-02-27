from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentCreateResponse(BaseModel):
    id: str
    status: str
    project_id: str
    chunk_count: int


class DocumentItem(BaseModel):
    id: str
    project_id: str
    filename: str | None
    source_type: str
    status: str
    chunk_count: int
    created_at: str
    updated_at: str


class Citation(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    score: float


class QueryRequest(BaseModel):
    project_id: str = "default"
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class QueryResponse(BaseModel):
    id: str
    answer: str
    citations: list[Citation]
    latency_ms: int
    model: str
    related_documents: list[str]


class QueryDetail(QueryResponse):
    question: str
    tokens_used: int
    created_at: str


class EvalRequest(BaseModel):
    query_id: str
    rating: int | None = Field(default=None, ge=1, le=5)
    note: str | None = None


class EvalResponse(BaseModel):
    ok: bool


class ActionRequest(BaseModel):
    project_id: str = "default"
    type: str
    payload: dict


class ActionResponse(BaseModel):
    action_id: str
    status: str
    result: str


class MetricResponse(BaseModel):
    documents: int
    chunks: int
    queries: int
    avg_query_latency_ms: float
    feedback_count: int
    avg_feedback_rating: float | None
