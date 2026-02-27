from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


API_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(API_ROOT))


def test_health_and_document_query_cycle(tmp_path, monkeypatch):
    monkeypatch.setenv("KNOWLEDGE_COPILOT_DATABASE_PATH", str(tmp_path / "knowledge_copilot.db"))

    import src.main as main

    importlib.reload(main)

    with TestClient(main.app) as client:
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        payload = {"project_id": "default", "source_text": "이 프로젝트는 문서 기반 질의 응답 시스템입니다."}
        create_res = client.post("/api/v1/documents", data=payload)
        assert create_res.status_code == 200
        doc = create_res.json()
        assert "id" in doc
        assert doc["chunk_count"] >= 1

        list_res = client.get("/api/v1/documents?project_id=default")
        assert list_res.status_code == 200
        assert len(list_res.json()) == 1

        query_res = client.post(
            "/api/v1/queries",
            json={"project_id": "default", "question": "이 시스템의 목적은?", "top_k": 3},
        )
        assert query_res.status_code == 200
        query_json = query_res.json()
        assert "answer" in query_json
        assert "citations" in query_json
        assert query_json["model"]
        assert "id" in query_json


def test_eval_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("KNOWLEDGE_COPILOT_DATABASE_PATH", str(tmp_path / "knowledge_copilot.db"))

    import src.main as main

    importlib.reload(main)

    with TestClient(main.app) as client:
        create_res = client.post(
            "/api/v1/documents",
            data={"project_id": "default", "source_text": "평가 테스트 문장입니다."},
        )
        assert create_res.status_code == 200

        query_res = client.post(
            "/api/v1/queries",
            json={"project_id": "default", "question": "평가 테스트"},
        )
        assert query_res.status_code == 200
        query_id = query_res.json()["id"]

        res = client.post(
            "/api/v1/evals",
            json={"query_id": query_id, "rating": 5, "note": "테스트 메모"},
        )
        # feedback API accepts any query id and persists; returns true in this PoC build.
        assert res.status_code == 200
        assert res.json()["ok"] is True
