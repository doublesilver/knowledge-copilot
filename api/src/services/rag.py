from __future__ import annotations

import hashlib
import time
from typing import Any

import httpx
import numpy as np

from ..config import load_settings


class LLMError(RuntimeError):
    pass


_EMBED_DIM = 256


def _normalize_vector(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


def _local_embed(text: str) -> list[float]:
    vec = np.zeros(_EMBED_DIM, dtype=np.float32)
    tokens = [token for token in text.lower().replace("\n", " ").split(" ") if token]
    if not tokens:
        return vec.astype(float).tolist()
    for token in tokens:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest()
        idx = int.from_bytes(digest, "big") % _EMBED_DIM
        vec[idx] += 1.0
    return _normalize_vector(vec).astype(float).tolist()


def chunk_text(text: str, max_tokens: int = 220, overlap: int = 40) -> list[str]:
    tokens = text.split()
    if not tokens:
        return []
    if max_tokens <= 0:
        raise ValueError("max_tokens must be greater than 0")
    step = max_tokens - min(overlap, max_tokens - 1)
    chunks = []
    for start in range(0, len(tokens), step):
        chunk_tokens = tokens[start : start + max_tokens]
        if not chunk_tokens:
            break
        chunks.append(" ".join(chunk_tokens))
    return chunks


async def embed_text(text: str) -> list[float]:
    settings = load_settings()
    if not settings.openai_api_key:
        return _local_embed(text)

    endpoint = "https://api.openai.com/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "input": text,
        "model": settings.embedding_model,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.openai_timeout) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
    except Exception:
        # fallback to local mode if provider call is unavailable
        return _local_embed(text)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    return [await embed_text(text) for text in texts]


def similarity(query: list[float], candidate: list[float]) -> float:
    if not query or not candidate:
        return 0.0
    q = np.array(query, dtype=np.float32)
    c = np.array(candidate, dtype=np.float32)
    if q.size == 0 or c.size == 0:
        return 0.0
    denom = np.linalg.norm(q) * np.linalg.norm(c)
    if denom == 0:
        return 0.0
    return float(np.dot(q, c) / denom)


def build_prompt(question: str, context_chunks: list[dict[str, Any]]) -> str:
    context_lines = []
    for i, chunk in enumerate(context_chunks, start=1):
        context_lines.append(f"[{i}] {chunk['text']}")
    context = "\n".join(context_lines)
    return (
        "당신은 정확성과 근거 제시가 중요한 비서형 AI입니다. 아래 컨텍스트만 사용해 답변하세요.\n\n"
        f"질문: {question}\n\n"
        f"컨텍스트:\n{context}\n\n"
        "규칙:\n"
        "1) 컨텍스트에서 얻을 수 있는 정보만 사용하세요.\n"
        "2) 답변은 한국어로 4~8문장 이내로 작성하세요.\n"
        "3) 근거가 되는 컨텍스트 항목 번호를 반드시 언급하세요."
    )


async def generate_answer(question: str, context_chunks: list[dict[str, Any]], model: str | None = None) -> tuple[str, int, str]:
    settings = load_settings()
    if not settings.openai_api_key:
        if not context_chunks:
            return (
                "현재 API 키가 없어 데모 모드로 동작 중입니다. 먼저 참고 문서를 업로드하면 키워드 기반 응답을 제공합니다.",
                0,
                "local",
            )
        snippets = " ".join(chunk["text"] for chunk in context_chunks[:2])
        used = min(120, len(snippets))
        return (
            f"업로드된 문서를 기준으로 요약한 결과입니다: {snippets[:used]}...",
            0,
            "local-fallback",
        )

    endpoint = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    selected_model = model or settings.chat_model
    prompt = build_prompt(question, context_chunks)
    payload = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": "You are a practical engineering assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    try:
        start = time.perf_counter()
        async with httpx.AsyncClient(timeout=settings.openai_timeout) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            used_tokens = int(data.get("usage", {}).get("total_tokens", 0))
            _ = time.perf_counter() - start
            return answer.strip(), used_tokens, selected_model
    except Exception as err:
        raise LLMError(str(err))


def build_citations(context_chunks: list[dict[str, Any]], scores: list[float]) -> list[dict[str, Any]]:
    citations = []
    for chunk, score in zip(context_chunks, scores):
        citations.append(
            {
                "chunk_id": chunk["id"],
                "document_id": chunk["document_id"],
                "text": chunk["text"],
                "score": round(float(score), 4),
            }
        )
    return citations
