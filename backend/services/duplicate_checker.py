"""
Duplicate Document Checker.

Prevents re-ingesting the same document by checking URL exact match
and title similarity against existing STUDY_DOCS records.
"""

import logging
from difflib import SequenceMatcher

from services import oracle_service

logger = logging.getLogger(__name__)

TITLE_SIMILARITY_THRESHOLD = 0.9


class DuplicateDocumentError(Exception):
    """Raised when a document is already ingested."""

    def __init__(self, existing_doc_id: str, match_type: str):
        self.existing_doc_id = existing_doc_id
        self.match_type = match_type
        super().__init__(f"Duplicate document: {existing_doc_id} (match: {match_type})")


async def check_duplicate(
    title: str, url: str | None = None
) -> dict:
    """
    Check if a document is already ingested.

    Returns {"is_duplicate": bool, "existing_doc_id": str|None, "match_type": str}.
    Match types: "url", "title", "none".
    """
    # 1st pass: exact URL match
    if url:
        if await oracle_service.check_url_exists(url):
            docs = await oracle_service.get_all_doc_titles()
            for doc in docs:
                if doc["url"] == url:
                    logger.info(f"Duplicate detected (URL match): {url} -> {doc['doc_id']}")
                    return {
                        "is_duplicate": True,
                        "existing_doc_id": doc["doc_id"],
                        "match_type": "url",
                    }

    # 2nd pass: title similarity
    if title:
        docs = await oracle_service.get_all_doc_titles()
        title_lower = title.lower().strip()
        for doc in docs:
            existing_title = (doc["title"] or "").lower().strip()
            ratio = SequenceMatcher(None, title_lower, existing_title).ratio()
            if ratio > TITLE_SIMILARITY_THRESHOLD:
                logger.info(
                    f"Duplicate detected (title similarity {ratio:.2f}): "
                    f"'{title}' -> {doc['doc_id']}"
                )
                return {
                    "is_duplicate": True,
                    "existing_doc_id": doc["doc_id"],
                    "match_type": "title",
                }

    return {
        "is_duplicate": False,
        "existing_doc_id": None,
        "match_type": "none",
    }
