"""Tests for POST /api/v1/study/ask (tutor mode)."""


async def test_tutor_returns_answer(client):
    """Tutor mode should return an answer string."""
    resp = await client.post(
        "/api/v1/study/ask",
        json={"question": "What is small data ML?", "mode": "tutor", "model_mode": "fast"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] is not None
    assert len(data["answer"]) > 0
    assert data["mode"] == "tutor"
    assert data["has_direct_answer"] is True


async def test_tutor_has_sources(client):
    """Response should include sources with doc_title, page_hint, similarity."""
    resp = await client.post(
        "/api/v1/study/ask",
        json={"question": "What is transfer learning?", "mode": "tutor"},
    )
    data = resp.json()
    assert len(data["sources"]) > 0
    src = data["sources"][0]
    assert "doc_title" in src
    assert "page_hint" in src
    assert "similarity" in src
    assert src["doc_title"] == "Test Paper"


async def test_tutor_category_filter(client, monkeypatch):
    """category_filter should be passed to the search service."""
    from services import search_service
    captured = {}

    async def mock_search(query, category_filter=None, **kwargs):
        captured["category_filter"] = category_filter
        return [
            {"chunk_id": "c1", "doc_id": "d1", "doc_title": "P",
             "chunk_text": "text", "page_hint": "p.1",
             "category": "small_data", "similarity": 0.9},
        ]

    monkeypatch.setattr(search_service, "search", mock_search)

    await client.post(
        "/api/v1/study/ask",
        json={"question": "test", "mode": "tutor", "category_filter": "small_data"},
    )
    assert captured["category_filter"] == "small_data"
