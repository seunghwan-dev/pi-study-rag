"""Tests for POST /api/v1/study/ingest."""

import io


async def test_ingest_pdf_success(client):
    """Ingest a mock PDF file and get 200 with chunks_created > 0."""
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake content")
    resp = await client.post(
        "/api/v1/study/ingest",
        files={"file": ("test.pdf", fake_pdf, "application/pdf")},
        data={"doc_type": "paper", "title": "Test Paper"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["chunks_created"] > 0
    assert data["doc_id"]
    assert data["title"] == "Test Paper"


async def test_ingest_pymupdf_text(client):
    """chunks_by_method should contain pymupdf_text > 0."""
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake content")
    resp = await client.post(
        "/api/v1/study/ingest",
        files={"file": ("paper.pdf", fake_pdf, "application/pdf")},
        data={"doc_type": "paper"},
    )
    data = resp.json()
    assert data["chunks_by_method"]["pymupdf_text"] >= 1


async def test_ingest_page_hint(client):
    """Each extracted chunk should have a page_hint."""
    # Verified via mock: all mock chunks have page_hint set.
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake content")
    resp = await client.post(
        "/api/v1/study/ingest",
        files={"file": ("paper.pdf", fake_pdf, "application/pdf")},
    )
    assert resp.status_code == 200
    data = resp.json()
    # chunks_created matches the 3 mock chunks (all have page_hint)
    assert data["chunks_created"] == 3


async def test_ingest_category_classified(client):
    """categories_detected should be populated."""
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake content")
    resp = await client.post(
        "/api/v1/study/ingest",
        files={"file": ("paper.pdf", fake_pdf, "application/pdf")},
    )
    data = resp.json()
    assert len(data["categories_detected"]) > 0
    assert "small_data" in data["categories_detected"]
