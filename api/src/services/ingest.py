from __future__ import annotations

from typing import Iterable

from .. import db
from .rag import chunk_text, embed_texts


async def process_document(document_id: str, project_id: str, text: str) -> int:
    chunks = chunk_text(text)
    if not chunks:
        db.set_document_status(document_id, "empty")
        return 0

    embeddings = await embed_texts(chunks)
    for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
        db.create_chunk(
            document_id=document_id,
            project_id=project_id,
            chunk_index=idx,
            text=chunk,
            embedding=vector,
            metadata={"length": len(chunk), "index": idx},
        )

    db.set_document_status(document_id, "ready", chunk_count=len(chunks))
    return len(chunks)
