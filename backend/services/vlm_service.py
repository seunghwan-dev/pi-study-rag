"""
VLM Service — 3-stage PDF extraction pipeline.

Stage 1: PyMuPDF text extraction (free, all pages)
Stage 2: PyMuPDF table detection (free, all pages)
Stage 3: Azure/Local VLM for figure-heavy pages only (paid, selective)

Category classification via local LLM (Gemma 4 E4B, free).
"""

import os
import json
import time
import base64
import asyncio
import logging

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# --- Provider selection ---
VLM_PROVIDER = os.getenv("VLM_PROVIDER", "azure")

# --- Azure OpenAI config ---
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_KEY", "")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

TEXT_THRESHOLD = 100       # chars: pages with less text may need VLM
CHUNK_SPLIT_SIZE = 1000    # split long text chunks at this length
CATEGORY_BATCH_SIZE = 10   # chunks per LLM classification call

VLM_PROMPT = """You are a document analysis assistant for academic papers.
Analyze this page image and extract visual content (figures, graphs, diagrams).

Rules:
1. FIGURES/GRAPHS: Describe axis labels, trends, key data points, and captions.
2. EQUATIONS: Extract in LaTeX format if possible.
3. Any text visible but not machine-readable.

Output: JSON array of chunks.
Each: {"type": "figure|equation|text", "content": "...", "page_hint": "p.N"}"""

CATEGORY_PROMPT = """Classify each text into ONE category:
small_data | digital_twin | physics_ml | transfer_learning |
synthetic_data | materials | manufacturing | nlp_science |
pi_general | meta_factory

Texts:
{texts}

Output JSON only, no markdown:
{{"categories": ["category1", "category2", ...]}}"""


# ── Stage 1: PyMuPDF text extraction ──

def _extract_text_pymupdf(page, page_num: int) -> list[dict]:
    """Extract text chunks from a single PDF page using PyMuPDF."""
    text = page.get_text("text").strip()
    if not text:
        return []

    chunks = []

    # First page: extract abstract separately
    if page_num == 1 and len(text) > 50:
        abstract_text = text[:500].strip()
        chunks.append({
            "type": "abstract",
            "content": abstract_text,
            "page_hint": "p.1",
            "category": None,
        })
        text = text[500:].strip()

    if not text:
        return chunks

    # Split long text into ~1000 char chunks
    if len(text) > CHUNK_SPLIT_SIZE * 2:
        parts = []
        for i in range(0, len(text), CHUNK_SPLIT_SIZE):
            part = text[i:i + CHUNK_SPLIT_SIZE].strip()
            if part:
                parts.append(part)
    else:
        parts = [text]

    for part in parts:
        chunks.append({
            "type": "text",
            "content": part,
            "page_hint": f"p.{page_num}",
            "category": None,
        })

    return chunks


# ── Stage 2: PyMuPDF table detection ──

def _extract_tables_pymupdf(page, page_num: int) -> list[dict]:
    """Extract tables from a PDF page using PyMuPDF built-in table finder."""
    chunks = []
    try:
        tables = page.find_tables()
        for t_idx, table in enumerate(tables):
            rows = table.extract()
            if not rows or len(rows) < 2:
                continue

            # First row as headers
            headers = [str(h).strip() if h else f"col{i}" for i, h in enumerate(rows[0])]

            for row in rows[1:]:
                pairs = []
                for h, v in zip(headers, row):
                    val = str(v).strip() if v else ""
                    if val:
                        pairs.append(f"{h}: {val}")
                if pairs:
                    chunks.append({
                        "type": "table_row",
                        "content": ", ".join(pairs),
                        "page_hint": f"p.{page_num} Table",
                        "category": None,
                    })
    except Exception as e:
        logger.debug(f"Table extraction failed on page {page_num}: {e}")

    return chunks


# ── Stage 3: VLM for figure-heavy pages ──

def _should_use_vlm(page, force_vlm: bool = False) -> bool:
    """Determine if a page needs VLM processing."""
    if force_vlm:
        return True
    text = page.get_text("text").strip()
    images = page.get_images()
    return len(images) > 0 and len(text) < TEXT_THRESHOLD


def _get_azure_client():
    """Create Azure OpenAI async client (lazy init)."""
    from openai import AsyncAzureOpenAI
    return AsyncAzureOpenAI(
        azure_endpoint=AZURE_ENDPOINT,
        api_key=AZURE_API_KEY,
        api_version=AZURE_API_VERSION,
    )


def _page_to_base64(page) -> str:
    """Render a PDF page to base64-encoded PNG."""
    mat = fitz.Matrix(300 / 72, 300 / 72)
    pix = page.get_pixmap(matrix=mat)
    png_bytes = pix.tobytes("png")
    return base64.b64encode(png_bytes).decode("utf-8")


async def _call_azure_vlm(client, image_b64: str, page_num: int) -> list[dict]:
    """Call Azure GPT-4o Vision for a single page image with 3 retries."""
    delays = [1, 2, 4]

    for attempt in range(3):
        try:
            start = time.time()
            response = await client.chat.completions.create(
                model=AZURE_DEPLOYMENT,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VLM_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_b64}",
                                "detail": "high",
                            },
                        },
                    ],
                }],
                max_tokens=4096,
                temperature=0.0,
            )
            elapsed = time.time() - start
            raw = response.choices[0].message.content.strip()

            # Strip markdown fences
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()

            chunks = json.loads(raw)
            if isinstance(chunks, dict):
                chunks = [chunks]

            for chunk in chunks:
                if not chunk.get("page_hint"):
                    chunk["page_hint"] = f"p.{page_num} Fig"
                chunk["category"] = None

            logger.info(f"VLM page {page_num}: {len(chunks)} chunks in {elapsed:.1f}s (attempt {attempt+1})")
            return chunks

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"VLM page {page_num} JSON parse failed (attempt {attempt+1}): {e}")
            if attempt < 2:
                await asyncio.sleep(delays[attempt])
        except Exception as e:
            logger.error(f"VLM page {page_num} API error (attempt {attempt+1}): {e}")
            if attempt < 2:
                await asyncio.sleep(delays[attempt])

    logger.error(f"VLM page {page_num} all retries failed.")
    return [{
        "type": "figure",
        "content": f"[VLM extraction failed for page {page_num}]",
        "page_hint": f"p.{page_num} Fig",
        "category": None,
    }]


# ── Category classification (local LLM, free) ──

async def _classify_categories_batch(chunks: list[dict]) -> list[str]:
    """Classify chunks into categories using local LLM in batches."""
    from services import llm_service

    all_categories = []

    for i in range(0, len(chunks), CATEGORY_BATCH_SIZE):
        batch = chunks[i:i + CATEGORY_BATCH_SIZE]
        texts = "\n".join(
            f"{j+1}. {c.get('content', '')[:200]}"
            for j, c in enumerate(batch)
        )
        prompt = CATEGORY_PROMPT.format(texts=texts)

        try:
            raw = await llm_service.generate(
                prompt=prompt,
                system_prompt="Output JSON only. No markdown.",
                model_mode="fast",
                temperature=0.1,
            )
            parsed = _parse_json(raw)
            cats = parsed.get("categories", [])
            # Pad or trim to match batch size
            while len(cats) < len(batch):
                cats.append("pi_general")
            all_categories.extend(cats[:len(batch)])
        except Exception as e:
            logger.warning(f"Category classification failed: {e}")
            all_categories.extend(["pi_general"] * len(batch))

    return all_categories


def _parse_json(text: str) -> dict:
    """Parse JSON from LLM response, stripping markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    if text.startswith("json"):
        text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


# ── Main pipeline ──

VALID_CATEGORIES = {
    "small_data", "digital_twin", "physics_ml", "transfer_learning",
    "synthetic_data", "materials", "manufacturing", "nlp_science",
    "pi_general", "meta_factory",
}


async def extract_from_pdf(
    pdf_path: str, force_vlm: bool = False
) -> tuple[list[dict], dict]:
    """
    3-stage PDF extraction pipeline.

    Returns:
        (chunks, stats) where chunks is a list of dicts and stats
        contains extraction method counts.
    """
    logger.info(f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    logger.info(f"PDF has {num_pages} pages")

    all_chunks: list[dict] = []
    stats = {"pymupdf_text": 0, "pymupdf_table": 0, "vlm_figure": 0, "vlm_pages_processed": 0}

    vlm_pages = []

    for page_num_0, page in enumerate(doc):
        page_num = page_num_0 + 1

        # Stage 1: Text extraction
        text_chunks = _extract_text_pymupdf(page, page_num)
        stats["pymupdf_text"] += len(text_chunks)
        all_chunks.extend(text_chunks)

        # Stage 2: Table extraction
        table_chunks = _extract_tables_pymupdf(page, page_num)
        stats["pymupdf_table"] += len(table_chunks)
        all_chunks.extend(table_chunks)

        # Stage 3: Mark pages needing VLM
        if VLM_PROVIDER != "none" and _should_use_vlm(page, force_vlm):
            vlm_pages.append((page_num, page))

    doc.close()

    # Stage 3: VLM processing (only for flagged pages)
    if vlm_pages and VLM_PROVIDER == "azure":
        client = _get_azure_client()
        # Re-open doc for rendering (closed above for memory)
        doc2 = fitz.open(pdf_path)
        for page_num, _ in vlm_pages:
            page = doc2[page_num - 1]
            b64 = _page_to_base64(page)
            vlm_chunks = await _call_azure_vlm(client, b64, page_num)
            stats["vlm_figure"] += len(vlm_chunks)
            stats["vlm_pages_processed"] += 1
            all_chunks.extend(vlm_chunks)
        doc2.close()
    elif vlm_pages and VLM_PROVIDER == "local":
        logger.warning("Local VLM not yet implemented. Skipping figure pages.")

    logger.info(
        f"Extraction complete: {len(all_chunks)} chunks "
        f"(text={stats['pymupdf_text']}, table={stats['pymupdf_table']}, "
        f"vlm={stats['vlm_figure']}, vlm_pages={stats['vlm_pages_processed']})"
    )

    # Category classification via local LLM
    if all_chunks:
        logger.info(f"Classifying {len(all_chunks)} chunks into categories...")
        categories = await _classify_categories_batch(all_chunks)
        for chunk, cat in zip(all_chunks, categories):
            if cat in VALID_CATEGORIES:
                chunk["category"] = cat
            else:
                chunk["category"] = "pi_general"

    return all_chunks, stats
