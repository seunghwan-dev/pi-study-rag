"""Tests for GET /api/v1/study/survey."""

from unittest.mock import AsyncMock
from services import survey_agent

MOCK_SURVEY_RESULT = {
    "monologue": ["Step 1...", "Step 2...", "Step 3...", "Step 4...", "Step 5..."],
    "analysis": {
        "strongest": {"category": "small_data", "label": "Small Data", "coverage": 0.6},
        "weakest": {"category": "digital_twin", "label": "Digital Twin", "coverage": 0.1},
        "recent_trend": "transfer learning",
        "auto_keywords": ["kw1", "kw2", "kw3", "kw4"],
    },
    "recommendations": [{
        "paper": {
            "title": "Test Paper", "authors": ["A"], "arxiv_id": "2401.00001",
            "pdf_url": "https://arxiv.org/pdf/2401.00001", "is_open_access": True,
        },
        "connection": "Connects to small data",
        "target_category": "small_data",
        "relevance": 0.9,
    }],
    "total_found": 5,
    "total_recommended": 1,
}


async def test_survey_returns_monologue(client, monkeypatch):
    """Survey should return a monologue list with >= 3 steps."""
    monkeypatch.setattr(survey_agent, "run_survey", AsyncMock(return_value=MOCK_SURVEY_RESULT))
    resp = await client.get("/api/v1/study/survey")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["monologue"]) >= 3


async def test_survey_has_keywords(client, monkeypatch):
    """Survey analysis should include exactly 4 auto_keywords."""
    monkeypatch.setattr(survey_agent, "run_survey", AsyncMock(return_value=MOCK_SURVEY_RESULT))
    resp = await client.get("/api/v1/study/survey")
    data = resp.json()
    assert len(data["analysis"]["auto_keywords"]) == 4


async def test_survey_has_recommendations(client, monkeypatch):
    """Each recommendation should have connection and relevance."""
    monkeypatch.setattr(survey_agent, "run_survey", AsyncMock(return_value=MOCK_SURVEY_RESULT))
    resp = await client.get("/api/v1/study/survey")
    data = resp.json()
    assert len(data["recommendations"]) >= 1
    rec = data["recommendations"][0]
    assert "connection" in rec
    assert "relevance" in rec
    assert rec["relevance"] >= 0.7
