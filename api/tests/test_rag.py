from __future__ import annotations

import sys
from pathlib import Path

import pytest

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(API_ROOT))

from src.services.rag import chunk_text, _local_embed, similarity, build_prompt, _normalize_vector
from src.config import load_settings
import numpy as np


class TestChunkText:
    def test_empty_string(self):
        assert chunk_text("") == []

    def test_short_text_single_chunk(self):
        result = chunk_text("hello world")
        assert len(result) == 1
        assert result[0] == "hello world"

    def test_respects_max_tokens(self):
        text = " ".join(f"word{i}" for i in range(500))
        chunks = chunk_text(text, max_tokens=100, overlap=20)
        for chunk in chunks:
            assert len(chunk.split()) <= 100

    def test_overlap_produces_more_chunks(self):
        text = " ".join(f"w{i}" for i in range(200))
        no_overlap = chunk_text(text, max_tokens=100, overlap=0)
        with_overlap = chunk_text(text, max_tokens=100, overlap=40)
        assert len(with_overlap) > len(no_overlap)

    def test_invalid_max_tokens(self):
        with pytest.raises(ValueError):
            chunk_text("hello", max_tokens=0)

    def test_covers_all_tokens(self):
        words = [f"w{i}" for i in range(50)]
        text = " ".join(words)
        chunks = chunk_text(text, max_tokens=20, overlap=5)
        reconstructed = set()
        for chunk in chunks:
            reconstructed.update(chunk.split())
        assert reconstructed == set(words)


class TestLocalEmbed:
    def test_returns_correct_dimension(self):
        vec = _local_embed("hello world")
        assert len(vec) == 256

    def test_empty_input(self):
        vec = _local_embed("")
        assert len(vec) == 256
        assert all(v == 0.0 for v in vec)

    def test_normalized(self):
        vec = _local_embed("test embedding normalization")
        norm = sum(v ** 2 for v in vec) ** 0.5
        assert abs(norm - 1.0) < 1e-5

    def test_deterministic(self):
        v1 = _local_embed("same text")
        v2 = _local_embed("same text")
        assert v1 == v2

    def test_different_texts_different_vectors(self):
        v1 = _local_embed("hello")
        v2 = _local_embed("completely different text")
        assert v1 != v2


class TestSimilarity:
    def test_identical_vectors(self):
        vec = _local_embed("test")
        score = similarity(vec, vec)
        assert abs(score - 1.0) < 1e-5

    def test_empty_vectors(self):
        assert similarity([], []) == 0.0

    def test_zero_vector(self):
        zero = [0.0] * 256
        vec = _local_embed("test")
        assert similarity(zero, vec) == 0.0

    def test_range(self):
        v1 = _local_embed("hello world")
        v2 = _local_embed("goodbye moon")
        score = similarity(v1, v2)
        assert -1.0 <= score <= 1.0


class TestNormalizeVector:
    def test_unit_vector(self):
        vec = np.array([3.0, 4.0])
        result = _normalize_vector(vec)
        assert abs(np.linalg.norm(result) - 1.0) < 1e-6

    def test_zero_vector(self):
        vec = np.array([0.0, 0.0])
        result = _normalize_vector(vec)
        assert np.allclose(result, vec)


class TestBuildPrompt:
    def test_includes_question(self):
        prompt = build_prompt("test question", [])
        assert "test question" in prompt

    def test_includes_context(self):
        chunks = [{"text": "chunk one"}, {"text": "chunk two"}]
        prompt = build_prompt("q", chunks)
        assert "chunk one" in prompt
        assert "chunk two" in prompt
        assert "[1]" in prompt
        assert "[2]" in prompt

    def test_korean_instructions(self):
        prompt = build_prompt("q", [])
        assert "한국어" in prompt


class TestLoadSettings:
    def test_defaults(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_CHAT_MODEL", raising=False)
        settings = load_settings()
        assert settings.gemini_api_key is None
        assert settings.chat_model == "gemini-2.5-flash"
        assert settings.embedding_model == "text-embedding-004"
        assert settings.api_timeout == 30

    def test_custom_values(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        monkeypatch.setenv("GEMINI_CHAT_MODEL", "custom-model")
        monkeypatch.setenv("GEMINI_REQUEST_TIMEOUT", "60")
        settings = load_settings()
        assert settings.gemini_api_key == "test-key"
        assert settings.chat_model == "custom-model"
        assert settings.api_timeout == 60
