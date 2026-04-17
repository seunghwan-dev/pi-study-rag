"""
Paper Fetcher Service.

Downloads a PDF from a whitelisted URL, runs the full VLM ingestion
pipeline, and stores results in Oracle.
"""

import os
import re
import time
import logging
from urllib.parse import urlparse

import httpx

from security.whitelist import validate_url
from security.sanitizer import sanitize_chunk
from security.audit import log_injection_detected, log_fetch_success
from services.duplicate_checker import check_duplicate, DuplicateDocumentError
from services import vlm_service, embedding_service, oracle_service

logger = logging.getLogger(__name__)

PAPERS_DIR = "/app/papers"

VALID_CATEGORIES = {
    "small_data", "digital_twin", "physics_ml", "transfer_learning",
    "synthetic_data", "materials", "manufacturing", "nlp_science",
    "pi_general", "meta_factory",
}


def _url_to_doc_id(url: str) -> str:
    """Derive a doc_id from a URL path."""
    path = urlparse(url).path.rstrip("/")
    name = path.split("/")[-1]
    # Only strip common document extensions, not arXiv-style version suffixes
    base, ext = os.path.splitext(name)
    if ext.lower() in (".pdf", ".html", ".htm"):
        name = base
    doc_id = re.sub(r"[^a-zA-Z0-9]", "-", name).lower().strip("-")
    doc_id = re.sub(r"-+", "-", doc_id)
    return doc_id[:60]


async def fetch_and_ingest(
    pdf_url: str,
    title: str | None = None,
    source: str | None = None,
    doc_type: str = "paper",
) -> dict:
    """
    Download a PDF from a whitelisted URL and run the full ingestion pipeline.

    Returns dict with doc_id, title, chunks_created, chunks_filtered,
    categories_detected, processing_time_sec.
    """
    start = time.time()

    # Step 1: Validate domain
    validate_url(pdf_url)

    # Step 2: Check duplicate
    dup = await check_duplicate(title or "", pdf_url)
    if dup["is_duplicate"]:
        raise DuplicateDocumentError(dup["existing_doc_id"], dup["match_type"])

    # Step 3: Download PDF
    os.makedirs(PAPERS_DIR, exist_ok=True)
    doc_id = _url_to_doc_id(pdf_url)
    pdf_path = os.path.join(PAPERS_DIR, f"{doc_id}.pdf")

    logger.info(f"Downloading PDF: {pdf_url}")
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        resp = await client.get(pdf_url)
        resp.raise_for_status()
    with open(pdf_path, "wb") as f:
        f.write(resp.content)
    logger.info(f"PDF saved: {pdf_path} ({len(resp.content)} bytes)")

    source_domain = urlparse(pdf_url).netloc

    try:
        # Step 4: 3-stage extraction (text + tables + VLM)
        logger.info(f"Starting extraction for: {doc_id}")
        raw_chunks, extraction_stats = await vlm_service.extract_from_pdf(pdf_path)

        if not raw_chunks:
            raise RuntimeError("Extraction produced zero chunks from PDF.")

        # Derive title from chunks if not provided
        doc_title = title
        if not doc_title:
            for chunk in raw_chunks:
                if chunk.get("type") in ("abstract", "text"):
                    content = chunk.get("content", "")
                    first_line = content.split("\n")[0].strip()
                    if len(first_line) > 10:
                        doc_title = first_line[:200]
                        break
        if not doc_title:
            doc_title = doc_id

        # Step 5: Filter, normalize, sanitize
        valid_chunks = []
        sanitized_count = 0
        for chunk in raw_chunks:
            raw_content = chunk.get("content", "")
            if isinstance(raw_content, dict):
                import json as _json
                raw_content = _json.dumps(raw_content, ensure_ascii=False)
            chunk_content = str(raw_content).strip()
            if not chunk_content or len(chunk_content) < 5:
                continue
            category = chunk.get("category", "pi_general")
            if category not in VALID_CATEGORIES:
                category = "pi_general"

            sanitized_text, was_modified = sanitize_chunk(chunk_content, doc_id)
            if was_modified:
                chunk_id = f"{doc_id}-{len(valid_chunks):04d}"
                log_injection_detected(doc_id, chunk_id, "see sanitizer log")
                sanitized_count += 1

            valid_chunks.append({
                "chunk_type": chunk.get("type", "text"),
                "content": sanitized_text,
                "page_hint": chunk.get("page_hint"),
                "category": category,
                "is_sanitized": 1 if was_modified else 0,
            })

        chunks_filtered = len(raw_chunks) - len(valid_chunks)

        if not valid_chunks:
            raise RuntimeError("All extracted chunks were filtered out.")

        # Step 6: Embed
        logger.info(f"Embedding {len(valid_chunks)} chunks")
        texts = [c["content"] for c in valid_chunks]
        embeddings = await embedding_service.embed_passages(texts)

        # Step 7: Insert doc + chunks into Oracle
        await oracle_service.insert_doc({
            "doc_id": doc_id,
            "title": doc_title,
            "doc_type": doc_type,
            "source": source,
            "source_domain": source_domain,
            "url": pdf_url,
        })

        db_chunks = []
        for i, chunk in enumerate(valid_chunks):
            db_chunks.append({
                "chunk_id": f"{doc_id}-{i:04d}",
                "doc_id": doc_id,
                "chunk_type": chunk["chunk_type"],
                "chunk_text": chunk["content"],
                "page_hint": chunk["page_hint"],
                "category": chunk["category"],
                "is_sanitized": chunk["is_sanitized"],
                "embedding": embeddings[i],
            })

        await oracle_service.insert_chunks(db_chunks)

        # Sync text index (non-fatal)
        try:
            await oracle_service.sync_text_index()
        except Exception as e:
            logger.warning(f"Text index sync deferred: {e}")

        # Step 8: Update chunk count
        await oracle_service.update_doc_chunk_count(
            doc_id, len(valid_chunks), chunks_filtered
        )

        categories_detected = list({c["category"] for c in valid_chunks})
        elapsed = round(time.time() - start, 1)

        log_fetch_success(pdf_url, doc_id, len(valid_chunks))
        logger.info(
            f"Fetch+ingest complete: {doc_id} | {len(valid_chunks)} chunks | "
            f"{elapsed}s | categories: {categories_detected}"
        )

        return {
            "doc_id": doc_id,
            "title": doc_title,
            "chunks_created": len(valid_chunks),
            "chunks_filtered": chunks_filtered,
            "categories_detected": categories_detected,
            "processing_time_sec": elapsed,
            "chunks_by_method": extraction_stats,
            "vlm_pages_processed": extraction_stats.get("vlm_pages_processed", 0),
        }

    finally:
        # Keep the PDF in papers/ for reference
        pass
