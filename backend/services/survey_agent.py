"""
Survey Agent — autonomous 5-step paper discovery pipeline.

Analyzes the user's knowledge base, identifies gaps, generates search
keywords, explores arXiv, and evaluates paper relevance.
"""

import asyncio
import json
import logging

from services import history_service, progress_service, arxiv_service, llm_service
from services.arxiv_service import ArxivRateLimitError
from services.progress_service import CATEGORY_LABELS
from prompts.survey import (
    SURVEY_KEYWORD_PROMPT,
    SURVEY_CONNECTION_PROMPT,
    SURVEY_TREND_PROMPT,
)

logger = logging.getLogger(__name__)

MAX_PAPERS_TO_ANALYZE = 10
RELEVANCE_THRESHOLD = 0.7


async def run_survey() -> dict:
    """
    Run the 5-step autonomous survey agent.
    Returns monologue, analysis, recommendations, and discovery counts.
    """
    monologue = []
    analysis = {}
    recommendations = []
    total_found = 0

    try:
        # ── Step 0: Check data sufficiency ──
        progress = await progress_service.get_progress()
        if progress["overview"]["total_questions"] == 0:
            return {
                "monologue": ["まだ学習履歴がありません。先に質問やクイズを試してください。"],
                "analysis": {
                    "strongest": None,
                    "weakest": None,
                    "recent_trend": "データ不足",
                    "auto_keywords": [],
                },
                "recommendations": [],
                "total_found": 0,
                "total_recommended": 0,
            }

        # ── Step 1: Analyze existing knowledge base ──
        monologue.append("あなたの知識ベースを分析しています...")
        by_cat = progress["by_category"]

        # Filter to categories with chunks
        active_cats = [c for c in by_cat if c["chunk_count"] > 0]
        if not active_cats:
            active_cats = by_cat

        strongest = max(active_cats, key=lambda c: c["coverage"])
        weakest = min(active_cats, key=lambda c: c["coverage"])

        monologue.append(
            f"{strongest['label']}({strongest['coverage']*100:.0f}%)が最も強く、"
            f"{weakest['label']}({weakest['coverage']*100:.0f}%)が最も弱いです。"
        )
        analysis["strongest"] = {
            "category": strongest["category"],
            "label": strongest["label"],
            "coverage": strongest["coverage"],
        }
        analysis["weakest"] = {
            "category": weakest["category"],
            "label": weakest["label"],
            "coverage": weakest["coverage"],
        }

        # ── Step 2: Analyze recent learning trend ──
        recent = await history_service.get_recent(limit=20)
        if not recent:
            trend = "まだ学習履歴がありません"
        else:
            questions_list = "\n".join(
                f"- {r['question']}" for r in recent
            )
            trend_prompt = SURVEY_TREND_PROMPT.format(questions_list=questions_list)
            trend = await llm_service.generate(
                prompt=trend_prompt,
                system_prompt="Respond with a single short phrase in Japanese.",
                model_mode="fast",
                temperature=0.3,
            )
            trend = trend.strip().strip('"').strip("'")

        monologue.append(f"最近の学習パターンから、{trend}への関心が深まっています。")
        analysis["recent_trend"] = trend

        # ── Step 3: LLM generates search keywords (4 strategies) ──
        categories_summary = _build_categories_summary(by_cat)
        keyword_prompt = SURVEY_KEYWORD_PROMPT.format(
            categories_summary=categories_summary,
            trend=trend,
            weakest=weakest["label"],
        )

        kw_response = await llm_service.generate(
            prompt=keyword_prompt,
            system_prompt="Output JSON only. No markdown.",
            model_mode="fast",
            temperature=0.5,
        )

        keywords = _parse_keywords(kw_response)
        monologue.append(f"4つの戦略でキーワードを生成しました。")
        analysis["auto_keywords"] = keywords

        # ── Step 4: Explore arXiv + deduplicate ──
        all_papers = []
        seen_ids = set()
        for i, kw in enumerate(keywords):
            if i > 0:
                await asyncio.sleep(3.0)  # polite delay between searches
            try:
                papers = await arxiv_service.search(query=kw, max_results=5)
                for p in papers:
                    if not p["already_ingested"] and p["arxiv_id"] not in seen_ids:
                        seen_ids.add(p["arxiv_id"])
                        all_papers.append(p)
            except ArxivRateLimitError:
                logger.warning(f"arXiv rate limited on '{kw}', skipping remaining keywords")
                break
            except Exception as e:
                logger.warning(f"arXiv search failed for '{kw}': {e}")

        total_found = len(all_papers)
        monologue.append(
            f"arxivで4つの切り口から探索し、{total_found}件を発見しました。"
        )

        # ── Step 5: LLM evaluates paper connections ──
        for paper in all_papers[:MAX_PAPERS_TO_ANALYZE]:
            try:
                conn_prompt = SURVEY_CONNECTION_PROMPT.format(
                    paper_title=paper["title"],
                    paper_abstract=paper.get("abstract", "")[:500],
                    categories_summary=categories_summary,
                )
                conn_response = await llm_service.generate(
                    prompt=conn_prompt,
                    system_prompt="Output JSON only. No markdown.",
                    model_mode="fast",
                    temperature=0.2,
                )
                conn_data = _parse_connection(conn_response)
                if conn_data and conn_data.get("relevance", 0) >= RELEVANCE_THRESHOLD:
                    recommendations.append({
                        "paper": {
                            "title": paper["title"],
                            "authors": paper.get("authors", []),
                            "arxiv_id": paper["arxiv_id"],
                            "pdf_url": paper.get("pdf_url", ""),
                            "is_open_access": True,
                        },
                        "connection": conn_data.get("connection", ""),
                        "target_category": conn_data.get("target_category", ""),
                        "relevance": conn_data.get("relevance", 0),
                    })
            except Exception as e:
                logger.warning(f"Connection analysis failed for '{paper['title'][:40]}': {e}")

        monologue.append(
            f"うち{len(recommendations)}件が既存知識と接続可能です。"
        )

    except Exception as e:
        logger.error(f"Survey agent error: {e}")
        monologue.append(f"エラーが発生しました: {str(e)[:100]}")

    return {
        "monologue": monologue,
        "analysis": analysis,
        "recommendations": recommendations,
        "total_found": total_found,
        "total_recommended": len(recommendations),
    }


def _build_categories_summary(by_cat: list[dict]) -> str:
    """Build a text summary of category coverage for LLM prompts."""
    lines = []
    for c in by_cat:
        if c["chunk_count"] > 0:
            lines.append(
                f"- {c['label']} ({c['category']}): "
                f"{c['chunk_count']} chunks, {c['coverage']*100:.0f}% coverage, "
                f"{c['question_count']} questions"
            )
    return "\n".join(lines) if lines else "No categories populated yet."


def _parse_keywords(text: str) -> list[str]:
    """Parse keyword list from LLM JSON response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    if text.startswith("json"):
        text = text[4:].strip()

    try:
        data = json.loads(text)
        keywords = data.get("keywords", [])
        if isinstance(keywords, list) and len(keywords) >= 1:
            return keywords[:4]
    except (json.JSONDecodeError, KeyError):
        logger.warning(f"Failed to parse keywords JSON: {text[:200]}")

    # Fallback: generic keywords
    return [
        "small data machine learning manufacturing",
        "process informatics digital twin",
        "physics-informed neural network materials",
        "emerging trends AI manufacturing 2024",
    ]


def _parse_connection(text: str) -> dict | None:
    """Parse connection analysis JSON from LLM response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    if text.startswith("json"):
        text = text[4:].strip()

    try:
        data = json.loads(text)
        relevance = float(data.get("relevance", 0))
        return {
            "connection": data.get("connection", ""),
            "target_category": data.get("target_category", ""),
            "relevance": round(relevance, 2),
        }
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
        logger.warning(f"Failed to parse connection JSON: {e}")
        return None
