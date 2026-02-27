from __future__ import annotations

from typing import Any

from .. import db
from .query import answer_query


async def execute_action(project_id: str, action_type: str, payload: dict[str, Any]) -> str:
    if action_type == "summary":
        target_docs = payload.get("documents") or []
        question = payload.get("question") or "문서의 핵심 내용을 5줄로 요약해줘"
        if target_docs:
            # create a synthetic project scoped to selected docs by querying each question and concatenating manually in fallback mode
            chunks = []
            for doc_id in target_docs:
                chunks.extend(db.get_chunks_for_document(doc_id))
            if chunks:
                return " ".join(chunk["text"] for chunk in chunks[:20])
        return "요약 대상 문서가 없거나 텍스트 조각이 없습니다."

    if action_type == "query_digest":
        digest_question = payload.get("question", "최근 질의 내역을 요약해줘")
        return digest_question

    return "지원하지 않는 액션 타입입니다."
