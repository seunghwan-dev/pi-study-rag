"""Tests for POST /api/v1/study/search-papers."""


async def test_search_papers_returns_results(client):
    """Search should return a non-empty papers list."""
    resp = await client.post(
        "/api/v1/study/search-papers",
        json={"query": "small data machine learning", "source": "arxiv"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["papers"]) > 0
    assert data["total_found"] >= 1


async def test_search_papers_has_fields(client):
    """Each paper should have title, authors, pdf_url."""
    resp = await client.post(
        "/api/v1/study/search-papers",
        json={"query": "transfer learning"},
    )
    paper = resp.json()["papers"][0]
    assert "title" in paper
    assert "authors" in paper
    assert "pdf_url" in paper
    assert paper["title"]  # non-empty


async def test_search_papers_already_ingested(client):
    """Each paper should have the already_ingested field."""
    resp = await client.post(
        "/api/v1/study/search-papers",
        json={"query": "physics informed"},
    )
    paper = resp.json()["papers"][0]
    assert "already_ingested" in paper
    assert isinstance(paper["already_ingested"], bool)
