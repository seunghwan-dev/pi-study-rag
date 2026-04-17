"""Tests for POST /api/v1/study/ask (socratic mode)."""

from unittest.mock import AsyncMock
from services import llm_service, oracle_service


async def test_socratic_returns_hint(client, monkeypatch):
    """Socratic mode should parse HINT and FOLLOW_UP from LLM response."""
    monkeypatch.setattr(
        llm_service, "generate",
        AsyncMock(return_value="HINT: Think about data scarcity.\nFOLLOW_UP: How does transfer learning help?"),
    )
    resp = await client.post(
        "/api/v1/study/ask",
        json={"question": "What is small data?", "mode": "socratic", "model_mode": "fast"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["hint"] is not None
    assert "data scarcity" in data["hint"]
    assert data["follow_up_question"] is not None
    assert "transfer learning" in data["follow_up_question"]


async def test_socratic_has_direct_answer_false(client, monkeypatch):
    """Socratic mode should set has_direct_answer to False."""
    monkeypatch.setattr(
        llm_service, "generate",
        AsyncMock(return_value="HINT: Consider the data.\nFOLLOW_UP: Why?"),
    )
    resp = await client.post(
        "/api/v1/study/ask",
        json={"question": "test", "mode": "socratic"},
    )
    data = resp.json()
    assert data["has_direct_answer"] is False
    assert data["mode"] == "socratic"


async def test_socratic_saves_history_mode(client, monkeypatch):
    """History should be saved with study_mode='socratic'."""
    monkeypatch.setattr(
        llm_service, "generate",
        AsyncMock(return_value="HINT: hint\nFOLLOW_UP: question?"),
    )
    mock_insert = AsyncMock(return_value="hist-002")
    monkeypatch.setattr(oracle_service, "insert_history", mock_insert)

    await client.post(
        "/api/v1/study/ask",
        json={"question": "test socratic", "mode": "socratic"},
    )

    assert mock_insert.called
    record = mock_insert.call_args[0][0]
    assert record["study_mode"] == "socratic"
