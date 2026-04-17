"""
arXiv Search Service.

Queries the arXiv API for papers and checks ingestion status
against Oracle STUDY_DOCS.
"""

import asyncio
import logging
import xml.etree.ElementTree as ET

import httpx

from services import oracle_service

logger = logging.getLogger(__name__)

ARXIV_API_URL = "https://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"
_USER_AGENT = "PI-Study-RAG/0.3 (https://github.com/seunghwan-dev/pi-study-rag; research use)"


class ArxivRateLimitError(Exception):
    pass


async def search(query: str, max_results: int = 10) -> list[dict]:
    """
    Search arXiv for papers matching the query.
    Returns list of paper dicts with ingestion status from Oracle.
    """
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    # Polite delay to avoid 429
    await asyncio.sleep(0.5)

    async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": _USER_AGENT}) as client:
        resp = await client.get(ARXIV_API_URL, params=params)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise ArxivRateLimitError("arXiv API rate limit exceeded.")
            raise

    root = ET.fromstring(resp.text)
    entries = root.findall(f"{ATOM_NS}entry")

    papers = []
    for entry in entries:
        paper = _parse_entry(entry)
        if paper:
            papers.append(paper)

    # Batch check which papers are already ingested
    pdf_urls = [p["pdf_url"] for p in papers if p.get("pdf_url")]
    ingested_urls = set()
    for url in pdf_urls:
        if await oracle_service.check_url_exists(url):
            ingested_urls.add(url)

    for paper in papers:
        paper["already_ingested"] = paper.get("pdf_url", "") in ingested_urls

    logger.info(f"arXiv search '{query}': {len(papers)} results, {len(ingested_urls)} already ingested")
    return papers


def _parse_entry(entry: ET.Element) -> dict | None:
    """Parse a single Atom entry from the arXiv API response."""
    # arXiv ID from the <id> tag (e.g., http://arxiv.org/abs/2301.12345v1)
    id_text = _get_text(entry, f"{ATOM_NS}id")
    if not id_text:
        return None

    arxiv_id = id_text.rstrip("/").split("/")[-1]

    title = _get_text(entry, f"{ATOM_NS}title")
    if title:
        title = " ".join(title.split())  # collapse whitespace

    # Authors
    authors = []
    for author_el in entry.findall(f"{ATOM_NS}author"):
        name = _get_text(author_el, f"{ATOM_NS}name")
        if name:
            authors.append(name)

    abstract = _get_text(entry, f"{ATOM_NS}summary")
    if abstract:
        abstract = " ".join(abstract.split())

    published = _get_text(entry, f"{ATOM_NS}published")
    if published:
        published = published[:10]  # YYYY-MM-DD

    # PDF link: look for rel="related" type="application/pdf"
    # or construct from arXiv ID
    pdf_url = None
    for link in entry.findall(f"{ATOM_NS}link"):
        if link.get("title") == "pdf" or (
            link.get("type") == "application/pdf"
        ):
            pdf_url = link.get("href")
            break

    if not pdf_url and arxiv_id:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

    return {
        "arxiv_id": arxiv_id,
        "title": title or "Untitled",
        "authors": authors,
        "abstract": abstract or "",
        "published": published or "",
        "pdf_url": pdf_url or "",
        "already_ingested": False,
    }


def _get_text(element: ET.Element, tag: str) -> str | None:
    """Get text content of a child element, or None if not found."""
    child = element.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return None
