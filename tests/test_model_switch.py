"""Tests for model_mode switching (fast vs smart)."""


async def test_model_fast_works(client):
    """model_mode='fast' should return 200."""
    resp = await client.post(
        "/api/v1/study/ask",
        json={"question": "What is ML?", "mode": "tutor", "model_mode": "fast"},
    )
    assert resp.status_code == 200
    assert resp.json()["model_mode"] == "fast"


async def test_model_smart_works(client):
    """model_mode='smart' should return 200."""
    resp = await client.post(
        "/api/v1/study/ask",
        json={"question": "What is ML?", "mode": "tutor", "model_mode": "smart"},
    )
    assert resp.status_code == 200
    assert resp.json()["model_mode"] == "smart"
