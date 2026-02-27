from __future__ import annotations

import traceback
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import db
from .config import load_settings
from .schemas import (
    ActionRequest,
    ActionResponse,
    Citation,
    DocumentCreateResponse,
    DocumentItem,
    EvalRequest,
    EvalResponse,
    MetricResponse,
    QueryDetail,
    QueryRequest,
    QueryResponse,
)
from .services.actions import execute_action
from .services.ingest import process_document
from .services.metrics import get_metrics
from .services.query import answer_query

@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Knowledge Copilot API", version="0.1.0", lifespan=lifespan)


settings = load_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _to_list_response(item: db.DocumentRecord) -> DocumentItem:
    return DocumentItem(**item.__dict__)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/documents", response_model=DocumentCreateResponse)
async def upload_document(
    project_id: str = Form("default"),
    source_text: str = Form(default=""),
    file: UploadFile | None = File(default=None),
):
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required")

    if file is None and not source_text.strip():
        raise HTTPException(status_code=400, detail="Either file or source_text must be provided")

    if file is not None:
        if not file.filename:
            raise HTTPException(status_code=400, detail="file name is missing")
        raw = await file.read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Only UTF-8 text files are supported in this build")
        filename = file.filename
        source_type = "file"
        if filename.lower().endswith(".md"):
            source_type = "markdown"
        elif filename.lower().endswith(".txt"):
            source_type = "text"
        else:
            source_type = "unknown"
    else:
        text = source_text.strip()
        filename = "source_text.txt"
        source_type = "text"

    document = db.create_document(project_id=project_id, filename=filename, source_type=source_type)
    try:
        chunk_count = await process_document(document.id, project_id, text)
        return DocumentCreateResponse(
            id=document.id,
            status="ready" if chunk_count > 0 else "empty",
            project_id=project_id,
            chunk_count=chunk_count,
        )
    except Exception as err:
        db.set_document_status(document.id, "failed")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {err}") from err


@app.get("/api/v1/documents", response_model=list[DocumentItem])
def list_documents(project_id: str = "default", limit: int = 100, offset: int = 0):
    rows = db.list_documents(project_id=project_id, limit=limit, offset=offset)
    return [_to_list_response(row) for row in rows]


@app.get("/api/v1/documents/{document_id}")
def get_document(document_id: str):
    item = db.get_document(document_id)
    if item is None:
        raise HTTPException(status_code=404, detail="document not found")
    return {
        "document": _to_list_response(item),
        "chunks": db.get_chunks_for_document(document_id),
    }


@app.post("/api/v1/queries", response_model=QueryResponse)
async def query(payload: QueryRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="question cannot be empty")

    started = datetime.now(timezone.utc)
    result = await answer_query(payload.project_id, payload.question, payload.top_k)
    latency_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    query_id = str(uuid.uuid4())

    db.create_query(
        db.QueryRecord(
            id=query_id,
            project_id=payload.project_id,
            question=payload.question,
            answer=result["answer"],
            citations=result["citations"],
            latency_ms=latency_ms,
            tokens_used=result["tokens_used"],
            model=result["model"],
            related_documents=result["related_documents"],
            created_at=started.isoformat(),
        )
    )

    return QueryResponse(
        id=query_id,
        answer=result["answer"],
        citations=[Citation(**c) for c in result["citations"]],
        latency_ms=latency_ms,
        model=result["model"],
        related_documents=result["related_documents"],
    )


@app.get("/api/v1/queries/{query_id}", response_model=QueryDetail)
def get_query(query_id: str):
    item = db.get_query(query_id)
    if item is None:
        raise HTTPException(status_code=404, detail="query not found")
    return QueryDetail(
        id=item.id,
        answer=item.answer,
        citations=[Citation(**citation) for citation in item.citations],
        latency_ms=item.latency_ms,
        model=item.model,
        related_documents=item.related_documents,
        question=item.question,
        tokens_used=item.tokens_used,
        created_at=item.created_at,
    )


@app.post("/api/v1/evals", response_model=EvalResponse)
def add_eval(payload: EvalRequest):
    try:
        db.add_feedback(payload.query_id, payload.rating, payload.note)
    except KeyError as err:
        raise HTTPException(status_code=404, detail=str(err))
    return EvalResponse(ok=True)


@app.post("/api/v1/agent/actions", response_model=ActionResponse)
async def run_action(payload: ActionRequest):
    action_id = db.create_action(payload.project_id, payload.type, payload.payload)
    try:
        result = await execute_action(payload.project_id, payload.type, payload.payload)
        db.complete_action(action_id, result)
        return ActionResponse(action_id=action_id, status="completed", result=result)
    except Exception:
        db.complete_action(action_id, "failed", status="failed")
        raise HTTPException(status_code=500, detail="action execution failed")


@app.get("/api/v1/metrics", response_model=MetricResponse)
def metrics(project_id: str | None = None):
    return get_metrics(project_id)


@app.get("/api/v1/changelog")
def changelog() -> dict[str, str]:
    return {
        "version": "0.1.0",
        "status": "implemented",
    }


@app.exception_handler(Exception)
def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "trace": traceback.format_exc().splitlines()[-1]},
    )
