"""Tests for GET /api/v1/study/history."""

from unittest.mock import AsyncMock
from services import oracle_service, history_service


async def test_history_returns_items(client):
    """History endpoint should return a list with history_id."""
    resp = await client.get("/api/v1/study/history")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "history_id" in data[0]
    assert "study_mode" in data[0]


async def test_history_category_filter(client, monkeypatch):
    """category query param should be forwarded through the service layer."""
    mock_get = AsyncMock(return_value=[
        {"history_id": "h2", "question": "Q", "answer_preview": "A",
         "study_mode": "tutor", "model_mode": "fast", "category": "small_data",
         "quiz_score": None, "created_at": "2026-04-15T10:00:00"}
    ])
    monkeypatch.setattr(history_service, "get_history", mock_get)

    resp = await client.get("/api/v1/study/history?category=small_data&limit=5")
    assert resp.status_code == 200

    mock_get.assert_called_once_with(category_filter="small_data", limit=5)
