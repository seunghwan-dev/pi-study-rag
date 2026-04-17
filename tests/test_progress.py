"""Tests for GET /api/v1/study/progress."""

from unittest.mock import AsyncMock
from services import progress_service


VALID_REVIEW_STATUSES = {"recent", "review_recommended", "review_needed", "not_started"}


async def test_progress_has_overview(client, monkeypatch):
    """Progress should include overview with total_papers, total_chunks, overall_coverage."""
    monkeypatch.setattr(progress_service, "_count_table", AsyncMock(return_value=10))

    resp = await client.get("/api/v1/study/progress")
    assert resp.status_code == 200
    data = resp.json()
    overview = data["overview"]
    assert "total_papers" in overview
    assert "total_chunks" in overview
    assert "overall_coverage" in overview
    assert isinstance(overview["overall_coverage"], float)


async def test_progress_review_status(client, monkeypatch):
    """Each category in by_category should have a valid review_status."""
    monkeypatch.setattr(progress_service, "_count_table", AsyncMock(return_value=10))

    resp = await client.get("/api/v1/study/progress")
    data = resp.json()
    assert len(data["by_category"]) > 0
    for cat in data["by_category"]:
        assert "review_status" in cat
        assert cat["review_status"] in VALID_REVIEW_STATUSES
