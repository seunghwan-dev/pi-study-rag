"""Tests for POST /api/v1/study/quiz/generate and /quiz/evaluate."""

from unittest.mock import AsyncMock
from services import quiz_service


async def test_quiz_generate_returns_question(client, monkeypatch):
    """Quiz generation should return quiz_id and question."""
    monkeypatch.setattr(quiz_service, "generate_quiz", AsyncMock(return_value={
        "quiz_id": "q-001",
        "question": "What is transfer learning?",
        "source": {"doc_title": "Test Paper", "page_hint": "p.5"},
        "category": "small_data",
        "difficulty": "intermediate",
    }))
    resp = await client.post(
        "/api/v1/study/quiz/generate",
        json={"category": "small_data", "model_mode": "fast"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["quiz_id"] == "q-001"
    assert "transfer learning" in data["question"]
    assert data["difficulty"] == "intermediate"


async def test_quiz_evaluate_returns_score(client, monkeypatch):
    """Quiz evaluation should return score and feedback."""
    monkeypatch.setattr(quiz_service, "evaluate_quiz", AsyncMock(return_value={
        "score": "partially_correct",
        "feedback": "Good but incomplete.",
        "complete_answer": "Full answer here.",
        "source": "Test Paper p.5",
        "mastery_update": "quiz_score saved",
    }))
    resp = await client.post(
        "/api/v1/study/quiz/evaluate",
        json={"quiz_id": "q-001", "user_answer": "It reuses pretrained models."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == "partially_correct"
    assert "incomplete" in data["feedback"]
    assert data["mastery_update"] == "quiz_score saved"


async def test_quiz_evaluate_invalid_id(client, monkeypatch):
    """Non-existent quiz_id should return 404."""
    monkeypatch.setattr(
        quiz_service, "evaluate_quiz",
        AsyncMock(side_effect=KeyError("Quiz not found: invalid-id")),
    )
    resp = await client.post(
        "/api/v1/study/quiz/evaluate",
        json={"quiz_id": "invalid-id", "user_answer": "test"},
    )
    assert resp.status_code == 404
