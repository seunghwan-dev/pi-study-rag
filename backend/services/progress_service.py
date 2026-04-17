"""
Progress Service — study progress analytics.

Computes coverage, streak, and review recommendations
from Oracle STUDY_DOCS, STUDY_CHUNKS, and STUDY_HISTORY.
"""

import json
import logging
from datetime import datetime, timedelta, timezone

from services import oracle_service

logger = logging.getLogger(__name__)

CATEGORY_LABELS = {
    "small_data": "Small Data",
    "digital_twin": "Digital Twin",
    "physics_ml": "Physics+ML",
    "transfer_learning": "Transfer Learning",
    "synthetic_data": "Synthetic Data",
    "materials": "Materials",
    "manufacturing": "Manufacturing",
    "nlp_science": "Scientific NLP",
    "pi_general": "PI General",
    "meta_factory": "Meta-Factory",
}


async def get_progress() -> dict:
    """Compute full study progress report."""
    # Gather raw data
    cat_chunks = await oracle_service.get_category_chunk_counts()
    all_source_chunks = await oracle_service.get_all_history_source_chunks()

    total_papers = await _count_table("STUDY_DOCS")
    total_chunks = await _count_table("STUDY_CHUNKS")
    total_questions = await _count_table("STUDY_HISTORY")

    # Parse all cited chunk_ids from history
    cited_chunk_ids = set()
    cited_by_category: dict[str, set] = {}
    for row in all_source_chunks:
        sc_json = row.get("source_chunks")
        if not sc_json:
            continue
        try:
            if isinstance(sc_json, str):
                chunks = json.loads(sc_json)
            else:
                chunks = sc_json
            if isinstance(chunks, list):
                for c in chunks:
                    cid = c.get("chunk_id", "")
                    cat = c.get("category", "")
                    if cid:
                        cited_chunk_ids.add(cid)
                        if cat:
                            cited_by_category.setdefault(cat, set()).add(cid)
        except (json.JSONDecodeError, TypeError):
            continue

    unique_cited = len(cited_chunk_ids)
    overall_coverage = round(unique_cited / total_chunks, 4) if total_chunks > 0 else 0

    # Overview
    overview = {
        "total_papers": total_papers,
        "total_chunks": total_chunks,
        "total_questions": total_questions,
        "unique_chunks_cited": unique_cited,
        "overall_coverage": overall_coverage,
    }

    # By category
    now = datetime.now(timezone.utc)
    by_category = []
    for cat, label in CATEGORY_LABELS.items():
        chunk_count = cat_chunks.get(cat, 0)
        chunks_cited = len(cited_by_category.get(cat, set()))
        coverage = round(chunks_cited / chunk_count, 4) if chunk_count > 0 else 0

        stats = await oracle_service.get_history_stats(cat)
        question_count = stats["count"]
        last_studied = stats["last_studied"]

        days_since = None
        review_status = "not_started"
        if last_studied:
            if isinstance(last_studied, str):
                last_studied = datetime.fromisoformat(last_studied)
            if last_studied.tzinfo is None:
                last_studied = last_studied.replace(tzinfo=timezone.utc)
            days_since = (now - last_studied).days
            if days_since <= 7:
                review_status = "recent"
            elif days_since <= 14:
                review_status = "review_recommended"
            else:
                review_status = "review_needed"

        by_category.append({
            "category": cat,
            "label": label,
            "chunk_count": chunk_count,
            "chunks_cited": chunks_cited,
            "coverage": coverage,
            "question_count": question_count,
            "last_studied": last_studied.isoformat() if last_studied else None,
            "days_since_last": days_since,
            "review_status": review_status,
        })

    # Study streak
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    streak_today = await oracle_service.count_history_since(today_start)
    streak_week = await oracle_service.count_history_since(week_ago)
    streak_month = await oracle_service.count_history_since(month_ago)

    study_streak = {
        "today": streak_today,
        "this_week": streak_week,
        "this_month": streak_month,
    }

    # Recommendation
    recommendation = _pick_recommendation(by_category)

    return {
        "overview": overview,
        "by_category": by_category,
        "study_streak": study_streak,
        "recommendation": recommendation,
    }


def _pick_recommendation(by_category: list[dict]) -> dict | None:
    """Pick the category most in need of review."""
    candidates = [
        c for c in by_category
        if c["review_status"] in ("review_recommended", "review_needed")
        and c["chunk_count"] > 0
    ]
    if not candidates:
        return None

    # Sort by coverage ascending (lowest first), then days_since descending
    candidates.sort(key=lambda c: (c["coverage"], -(c["days_since_last"] or 0)))
    best = candidates[0]

    days = best["days_since_last"] or 0
    pct = round(best["coverage"] * 100, 1)
    return {
        "category": best["category"],
        "message": f"「{best['label']}」を復習しましょう",
        "reason": f"{days}日間未学習・カバー率{pct}%",
    }


async def _count_table(table: str) -> int:
    """Count rows in a table."""
    pool = await oracle_service._get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row = await cursor.fetchone()
            return row[0]
