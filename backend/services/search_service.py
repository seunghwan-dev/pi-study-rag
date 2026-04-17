"""
Hybrid Search Service — Vector (HNSW) + BM25 + RRF.

Runs vector and BM25 searches in parallel, then combines results
using Reciprocal Rank Fusion (k=60).
"""

import asyncio
import logging

from services.embedding_service import embed_query
from services.oracle_service import vector_search, bm25_search

logger = logging.getLogger(__name__)

RRF_K = 60


def _reciprocal_rank_fusion(
    vector_results: list[dict],
    bm25_results: list[dict],
    k: int = RRF_K,
) -> list[dict]:
    """
    Combine two ranked lists using Reciprocal Rank Fusion.
    k=60 is the standard default (Cormack et al., 2009).
    """
    scores: dict[str, float] = {}
    result_map: dict[str, dict] = {}

    for rank, r in enumerate(vector_results):
        cid = r["chunk_id"]
        scores[cid] = scores.get(cid, 0) + 1 / (k + rank + 1)
        result_map[cid] = r

    for rank, r in enumerate(bm25_results):
        cid = r["chunk_id"]
        scores[cid] = scores.get(cid, 0) + 1 / (k + rank + 1)
        if cid not in result_map:
            result_map[cid] = r

    sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    combined = []
    for chunk_id, rrf_score in sorted_ids:
        entry = dict(result_map[chunk_id])
        entry["search_method"] = "hybrid"
        entry["rrf_score"] = round(rrf_score, 6)
        combined.append(entry)

    return combined


async def search(
    query: str,
    category_filter: str | None = None,
    k: int = 60,
    top_n: int = 10,
) -> list[dict]:
    """
    Hybrid search: embed query -> vector + BM25 in parallel -> RRF fusion.
    Returns top_n results with chunk_text, doc_title, similarity, etc.
    """
    # Step 1: Embed query with "query:" prefix
    query_vector = await embed_query(query)

    # Step 2 & 3: Run vector and BM25 in parallel
    vec_task = vector_search(query_vector, max_results=k)
    bm25_task = bm25_search(query, max_results=k)
    vector_results, bm25_results = await asyncio.gather(
        vec_task, bm25_task, return_exceptions=True
    )

    # Handle BM25 failures gracefully (index may not be synced)
    if isinstance(vector_results, Exception):
        logger.error(f"Vector search failed: {vector_results}")
        vector_results = []
    if isinstance(bm25_results, Exception):
        logger.warning(f"BM25 search failed (may need index sync): {bm25_results}")
        bm25_results = []

    # Apply category filter if specified
    if category_filter:
        vector_results = [r for r in vector_results if r.get("category") == category_filter]
        bm25_results = [r for r in bm25_results if r.get("category") == category_filter]

    # Step 4: RRF fusion
    if vector_results and bm25_results:
        combined = _reciprocal_rank_fusion(vector_results, bm25_results)
    elif vector_results:
        combined = vector_results
    elif bm25_results:
        combined = bm25_results
    else:
        combined = []

    results = combined[:top_n]

    logger.info(
        f"Search '{query[:50]}': {len(vector_results)} vector + "
        f"{len(bm25_results)} bm25 -> {len(results)} hybrid results"
    )
    return results
