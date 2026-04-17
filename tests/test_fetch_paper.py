"""Tests for POST /api/v1/study/fetch-paper."""

from unittest.mock import AsyncMock
import routers.study as study_router


async def test_fetch_paper_success(client, monkeypatch):
    """Fetch a paper from a whitelisted URL."""
    monkeypatch.setattr(study_router, "fetch_and_ingest", AsyncMock(return_value={
        "doc_id": "2311-07126",
        "title": "How to Do ML with Small Data",
        "chunks_created": 50,
        "chunks_filtered": 2,
        "categories_detected": ["small_data", "transfer_learning"],
        "processing_time_sec": 12.3,
        "chunks_by_method": {"pymupdf_text": 45, "pymupdf_table": 5, "vlm_figure": 0, "vlm_pages_processed": 0},
        "vlm_pages_processed": 0,
    }))
    resp = await client.post(
        "/api/v1/study/fetch-paper",
        json={"pdf_url": "https://arxiv.org/pdf/2311.07126", "title": "Test"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["doc_id"] == "2311-07126"
    assert data["chunks_created"] == 50


async def test_fetch_paper_duplicate(client, monkeypatch):
    """Duplicate URL should return 409."""
    from services.duplicate_checker import DuplicateDocumentError
    monkeypatch.setattr(
        study_router, "fetch_and_ingest",
        AsyncMock(side_effect=DuplicateDocumentError("2311-07126", "url")),
    )
    resp = await client.post(
        "/api/v1/study/fetch-paper",
        json={"pdf_url": "https://arxiv.org/pdf/2311.07126"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "DUPLICATE"


async def test_fetch_paper_domain_rejected(client, monkeypatch):
    """Non-whitelisted domain should return 403."""
    from security.whitelist import DomainNotAllowedError
    monkeypatch.setattr(
        study_router, "fetch_and_ingest",
        AsyncMock(side_effect=DomainNotAllowedError("https://evil.com/x.pdf", "evil.com")),
    )
    resp = await client.post(
        "/api/v1/study/fetch-paper",
        json={"pdf_url": "https://evil.com/x.pdf"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"] == "DOMAIN_NOT_ALLOWED"
