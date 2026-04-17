"""
History Service — save and retrieve Q&A history.

Wraps oracle_service for STUDY_HISTORY operations.
"""

import uuid
import json
import logging

from services import oracle_service

logger = logging.getLogger(__name__)


async def save_history(
    question: str,
    answer: str,
    study_mode: str,
    model_mode: str,
    source_chunks: list[dict] | None = None,
    category: str | None = None,
    quiz_score: str | None = None,
    quiz_feedback: str | None = None,
    user_answer: str | None = None,
) -> str:
    """Save a Q&A interaction to STUDY_HISTORY."""
    history_id = str(uuid.uuid4())[:32]

    record = {
        "history_id": history_id,
        "question": question,
        "answer": answer,
        "study_mode": study_mode,
        "model_mode": model_mode,
        "source_chunks": source_chunks,
        "category": category,
        "quiz_score": quiz_score,
        "quiz_feedback": quiz_feedback,
        "user_answer": user_answer,
    }

    await oracle_service.insert_history(record)
    logger.info(f"Saved history: {history_id} (mode={study_mode}, cat={category})")
    return history_id


async def get_history(
    category_filter: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Retrieve recent history entries, optionally filtered by category."""
    return await oracle_service.get_history_rows(category_filter, limit)


async def get_recent(limit: int = 20) -> list[dict]:
    """Retrieve most recent history entries (for progress/survey)."""
    return await oracle_service.get_history_rows(None, limit)
