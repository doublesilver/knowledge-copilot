from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from .config import load_settings


@dataclass
class DocumentRecord:
    id: str
    project_id: str
    filename: str | None
    source_type: str
    status: str
    chunk_count: int
    created_at: str
    updated_at: str


@dataclass
class QueryRecord:
    id: str
    project_id: str
    question: str
    answer: str
    citations: list[dict[str, Any]]
    latency_ms: int
    tokens_used: int
    model: str
    related_documents: list[str]
    created_at: str


def _current_timestamp() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def get_db_path() -> str:
    raw = load_settings().db_path
    return str(Path(raw).expanduser())


def ensure_db_dir() -> None:
    Path(get_db_path()).parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    ensure_db_dir()
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def _serialize_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _deserialize_json(value: str | bytes | None) -> Any:
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    return json.loads(value)


@contextmanager
def db_transaction():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with db_transaction() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                filename TEXT,
                source_type TEXT NOT NULL,
                status TEXT NOT NULL,
                chunk_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                embedding TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS queries (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                citations TEXT NOT NULL,
                latency_ms INTEGER NOT NULL,
                tokens_used INTEGER NOT NULL,
                model TEXT NOT NULL,
                related_documents TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                query_id TEXT NOT NULL,
                rating INTEGER,
                note TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (query_id) REFERENCES queries(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS actions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                type TEXT NOT NULL,
                payload TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_documents_project ON documents(project_id);
            CREATE INDEX IF NOT EXISTS idx_chunks_project ON chunks(project_id);
            CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id);
            CREATE INDEX IF NOT EXISTS idx_queries_project ON queries(project_id);
            CREATE INDEX IF NOT EXISTS idx_feedback_query ON feedback(query_id);
            """
        )


def create_document(project_id: str, filename: str | None, source_type: str) -> DocumentRecord:
    document_id = str(uuid.uuid4())
    now = _current_timestamp()
    record = DocumentRecord(
        id=document_id,
        project_id=project_id,
        filename=filename,
        source_type=source_type,
        status="processing",
        chunk_count=0,
        created_at=now,
        updated_at=now,
    )
    with db_transaction() as conn:
        conn.execute(
            """INSERT INTO documents (id, project_id, filename, source_type, status, chunk_count, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.id,
                record.project_id,
                record.filename,
                record.source_type,
                record.status,
                record.chunk_count,
                record.created_at,
                record.updated_at,
            ),
        )
    return record


def set_document_status(document_id: str, status: str, chunk_count: int | None = None) -> None:
    now = _current_timestamp()
    with db_transaction() as conn:
        if chunk_count is None:
            conn.execute(
                "UPDATE documents SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, document_id),
            )
        else:
            conn.execute(
                "UPDATE documents SET status = ?, chunk_count = ?, updated_at = ? WHERE id = ?",
                (status, chunk_count, now, document_id),
            )


def get_document(document_id: str) -> DocumentRecord | None:
    with db_transaction() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
    if row is None:
        return None
    return DocumentRecord(**dict(row))


def list_documents(project_id: str, limit: int = 20, offset: int = 0) -> list[DocumentRecord]:
    with db_transaction() as conn:
        rows = conn.execute(
            """
            SELECT * FROM documents
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (project_id, limit, offset),
        ).fetchall()
    return [DocumentRecord(**dict(row)) for row in rows]


def create_chunk(document_id: str, project_id: str, chunk_index: int, text: str, embedding: list[float], metadata: dict[str, Any]) -> None:
    chunk_id = str(uuid.uuid4())
    now = _current_timestamp()
    with db_transaction() as conn:
        conn.execute(
            """INSERT INTO chunks (id, project_id, document_id, chunk_index, text, embedding, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                chunk_id,
                project_id,
                document_id,
                chunk_index,
                text,
                _serialize_json(embedding),
                _serialize_json(metadata),
                now,
            ),
        )


def get_chunks_by_project(project_id: str) -> list[dict[str, Any]]:
    with db_transaction() as conn:
        rows = conn.execute(
            "SELECT * FROM chunks WHERE project_id = ?",
            (project_id,),
        ).fetchall()
    chunks: list[dict[str, Any]] = []
    for row in rows:
        payload = dict(row)
        payload["embedding"] = _deserialize_json(payload["embedding"])
        payload["metadata"] = _deserialize_json(payload["metadata"])
        chunks.append(payload)
    return chunks


def get_chunks_for_document(document_id: str) -> list[dict[str, Any]]:
    with db_transaction() as conn:
        rows = conn.execute(
            "SELECT id, chunk_index, text, embedding, metadata FROM chunks WHERE document_id = ? ORDER BY chunk_index ASC",
            (document_id,),
        ).fetchall()
    chunks = []
    for row in rows:
        payload = dict(row)
        payload["embedding"] = _deserialize_json(payload["embedding"])
        payload["metadata"] = _deserialize_json(payload["metadata"])
        chunks.append(payload)
    return chunks


def create_query(record: QueryRecord) -> None:
    with db_transaction() as conn:
        conn.execute(
            """INSERT INTO queries (id, project_id, question, answer, citations, latency_ms, tokens_used, model, related_documents, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.id,
                record.project_id,
                record.question,
                record.answer,
                _serialize_json(record.citations),
                record.latency_ms,
                record.tokens_used,
                record.model,
                _serialize_json(record.related_documents),
                record.created_at,
            ),
        )


def get_query(query_id: str) -> QueryRecord | None:
    with db_transaction() as conn:
        row = conn.execute("SELECT * FROM queries WHERE id = ?", (query_id,)).fetchone()
    if row is None:
        return None
    payload = dict(row)
    return QueryRecord(
        id=payload["id"],
        project_id=payload["project_id"],
        question=payload["question"],
        answer=payload["answer"],
        citations=_deserialize_json(payload["citations"]),
        latency_ms=payload["latency_ms"],
        tokens_used=payload["tokens_used"],
        model=payload["model"],
        related_documents=_deserialize_json(payload["related_documents"]),
        created_at=payload["created_at"],
    )


def add_feedback(query_id: str, rating: int | None, note: str | None) -> None:
    feedback_id = str(uuid.uuid4())
    now = _current_timestamp()
    with db_transaction() as conn:
        exists = conn.execute("SELECT id FROM queries WHERE id = ?", (query_id,)).fetchone()
        if not exists:
            raise KeyError("query_id does not exist")
        conn.execute(
            "INSERT INTO feedback (id, query_id, rating, note, created_at) VALUES (?, ?, ?, ?, ?)",
            (feedback_id, query_id, rating, note, now),
        )


def create_action(project_id: str, action_type: str, payload: dict[str, Any]) -> str:
    action_id = str(uuid.uuid4())
    now = _current_timestamp()
    with db_transaction() as conn:
        conn.execute(
            "INSERT INTO actions (id, project_id, type, payload, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (action_id, project_id, action_type, _serialize_json(payload), "queued", now),
        )
    return action_id


def complete_action(action_id: str, result: str, status: str = "completed") -> None:
    now = _current_timestamp()
    with db_transaction() as conn:
        conn.execute(
            "UPDATE actions SET status = ?, result = ?, completed_at = ? WHERE id = ?",
            (status, result, now, action_id),
        )


def metric_snapshot(project_id: str | None = None) -> dict[str, Any]:
    project_filter = "WHERE project_id = ?" if project_id else ""
    params = (project_id,) if project_id else ()
    with db_transaction() as conn:
        doc_count = conn.execute(
            f"SELECT COUNT(*) FROM documents {project_filter}",
            params,
        ).fetchone()[0]
        chunk_count = conn.execute(
            f"SELECT COUNT(*) FROM chunks {project_filter}",
            params,
        ).fetchone()[0]
        query_rows = conn.execute(
            f"SELECT id, latency_ms FROM queries {project_filter}",
            params,
        ).fetchall()
        query_count = len(query_rows)
        total_latency = sum(row["latency_ms"] for row in query_rows if row["latency_ms"] is not None)
        if project_id:
            feedback_rows = conn.execute(
                "SELECT rating FROM feedback f JOIN queries q ON f.query_id = q.id WHERE q.project_id = ?",
                (project_id,),
            ).fetchall()
        else:
            feedback_rows = conn.execute("SELECT rating FROM feedback").fetchall()
    avg_latency = total_latency / query_count if query_count else 0
    ratings = [row[0] for row in feedback_rows if row[0] is not None]
    avg_rating = sum(ratings) / len(ratings) if ratings else None
    return {
        "documents": int(doc_count),
        "chunks": int(chunk_count),
        "queries": int(query_count),
        "avg_query_latency_ms": round(avg_latency, 2),
        "feedback_count": len(ratings),
        "avg_feedback_rating": None if avg_rating is None else round(avg_rating, 2),
    }
