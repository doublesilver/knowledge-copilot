from __future__ import annotations

from typing import Any

from .. import db
from .rag import build_citations, embed_text, generate_answer, similarity


async def answer_query(project_id: str, question: str, top_k: int = 5) -> dict[str, Any]:
    query_vec = await embed_text(question)
    all_chunks = db.get_chunks_by_project(project_id)
    if not all_chunks:
        return {
            "answer": "아직 프로젝트에 업로드된 문서가 없습니다. 먼저 문서를 업로드해 주세요.",
            "citations": [],
            "model": "local-fallback",
            "tokens_used": 0,
            "related_documents": [],
        }

    scored = []
    for chunk in all_chunks:
        score = similarity(query_vec, chunk["embedding"])
        scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    top = scored[:top_k]
    selected_chunks = [chunk for _, chunk in top]
    scores = [score for score, _ in top]
    citations = build_citations(selected_chunks, scores)

    answer, tokens_used, model = await generate_answer(
        question=question,
        context_chunks=selected_chunks,
    )

    related_documents = sorted({chunk["document_id"] for chunk in selected_chunks})
    return {
        "answer": answer,
        "citations": citations,
        "model": model,
        "tokens_used": int(tokens_used or 0),
        "related_documents": list(related_documents),
    }
