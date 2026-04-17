"""Tests for GET /api/v1/study/categories."""


async def test_categories_returns_list(client):
    """Categories endpoint should return a list with category, label, chunk_count."""
    resp = await client.get("/api/v1/study/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    item = data[0]
    assert "category" in item
    assert "label" in item
    assert "chunk_count" in item
    assert isinstance(item["chunk_count"], int)
