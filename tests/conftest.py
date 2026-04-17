"""
Shared test fixtures — mocks all external services (Oracle, Embedding, LLM, VLM, arXiv).
All tests run without Docker.
"""

import sys
from pathlib import Path

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from main import app
from services import oracle_service, embedding_service, llm_service, vlm_service
from services import search_service, arxiv_service


# ── Mock Oracle ──

@pytest.fixture(autouse=True)
def mock_oracle(monkeypatch):
    """Mock all oracle_service functions so tests never hit a real DB."""
    monkeypatch.setattr(oracle_service, "ensure_tables", AsyncMock())
    monkeypatch.setattr(oracle_service, "insert_doc", AsyncMock(return_value="test-doc-001"))
    monkeypatch.setattr(oracle_service, "insert_chunks", AsyncMock(return_value=3))
    monkeypatch.setattr(oracle_service, "update_doc_chunk_count", AsyncMock())
    monkeypatch.setattr(oracle_service, "sync_text_index", AsyncMock())
    monkeypatch.setattr(oracle_service, "check_url_exists", AsyncMock(return_value=False))
    monkeypatch.setattr(oracle_service, "get_all_doc_titles", AsyncMock(return_value=[]))
    monkeypatch.setattr(oracle_service, "get_category_chunk_counts", AsyncMock(return_value={
        "small_data": 50, "digital_twin": 30, "physics_ml": 20,
    }))
    monkeypatch.setattr(oracle_service, "get_random_chunk", AsyncMock(return_value={
        "chunk_id": "chunk-001", "doc_id": "doc-001",
        "chunk_text": "Transfer learning reduces data requirements by leveraging pretrained models.",
        "page_hint": "p.5", "category": "small_data",
    }))
    monkeypatch.setattr(oracle_service, "get_doc_title", AsyncMock(return_value="Test Paper Title"))
    monkeypatch.setattr(oracle_service, "get_history_rows", AsyncMock(return_value=[
        {
            "history_id": "h1", "question": "What is ML?", "answer_preview": "ML is...",
            "study_mode": "tutor", "model_mode": "fast", "category": "small_data",
            "quiz_score": None, "created_at": "2026-04-15T10:00:00",
        }
    ]))
    monkeypatch.setattr(oracle_service, "insert_history", AsyncMock(return_value="hist-001"))
    monkeypatch.setattr(oracle_service, "get_all_history_source_chunks", AsyncMock(return_value=[
        {"source_chunks": '[{"chunk_id":"c1","category":"small_data"},{"chunk_id":"c2","category":"physics_ml"}]'}
    ]))
    monkeypatch.setattr(oracle_service, "get_history_stats", AsyncMock(return_value={
        "count": 5, "last_studied": None,
    }))
    monkeypatch.setattr(oracle_service, "count_history_since", AsyncMock(return_value=3))
    monkeypatch.setattr(oracle_service, "vector_search", AsyncMock(return_value=[]))
    monkeypatch.setattr(oracle_service, "bm25_search", AsyncMock(return_value=[]))


# ── Mock Embedding ──

@pytest.fixture(autouse=True)
def mock_embedding(monkeypatch):
    monkeypatch.setattr(embedding_service, "embed_passages", AsyncMock(return_value=[[0.1] * 1024] * 10))
    monkeypatch.setattr(embedding_service, "embed_query", AsyncMock(return_value=[0.1] * 1024))


# ── Mock LLM (Ollama) ──

@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    monkeypatch.setattr(llm_service, "generate", AsyncMock(return_value="Mock LLM response about ML."))


# ── Mock VLM (3-stage extraction) ──

@pytest.fixture(autouse=True)
def mock_vlm(monkeypatch):
    mock_extract = AsyncMock(return_value=(
        [
            {"type": "abstract", "content": "This paper reviews small data ML.", "page_hint": "p.1", "category": "small_data"},
            {"type": "text", "content": "Machine learning with small data is challenging.", "page_hint": "p.1", "category": "small_data"},
            {"type": "table_row", "content": "Method: Transfer Learning, Accuracy: 0.95", "page_hint": "p.3 Table", "category": "transfer_learning"},
        ],
        {"pymupdf_text": 2, "pymupdf_table": 1, "vlm_figure": 0, "vlm_pages_processed": 0},
    ))
    monkeypatch.setattr(vlm_service, "extract_from_pdf", mock_extract)


# ── Mock Search ──

@pytest.fixture(autouse=True)
def mock_search(monkeypatch):
    monkeypatch.setattr(search_service, "search", AsyncMock(return_value=[
        {
            "chunk_id": "c1", "doc_id": "d1", "doc_title": "Test Paper",
            "chunk_text": "Small data ML review.", "page_hint": "p.2",
            "category": "small_data", "similarity": 0.92,
        },
        {
            "chunk_id": "c2", "doc_id": "d1", "doc_title": "Test Paper",
            "chunk_text": "Transfer learning approach.", "page_hint": "p.5",
            "category": "transfer_learning", "similarity": 0.87,
        },
    ]))


# ── Mock arXiv ──

@pytest.fixture(autouse=True)
def mock_arxiv(monkeypatch):
    monkeypatch.setattr(arxiv_service, "search", AsyncMock(return_value=[
        {
            "arxiv_id": "2311.07126", "title": "How to Do ML with Small Data",
            "authors": ["Author A"], "abstract": "A review...", "published": "2023-11",
            "pdf_url": "https://arxiv.org/pdf/2311.07126", "already_ingested": False,
        }
    ]))


# ── AsyncClient ──

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
