"""
Study Router — PDF ingestion, paper search, RAG Q&A, history, and progress.

POST /api/v1/study/ingest        — Upload & ingest a PDF
POST /api/v1/study/search-papers — Search arXiv for papers
POST /api/v1/study/fetch-paper   — Fetch & ingest a paper by URL
POST /api/v1/study/ask           — RAG Q&A (tutor / socratic mode)
GET  /api/v1/study/history       — Q&A history
GET  /api/v1/study/categories    — Category chunk counts
GET  /api/v1/study/progress      — Study progress analytics
"""

import os
import uuid
import time
import logging
import tempfile
import re
from collections import Counter

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query

from fastapi.responses import JSONResponse

from schemas.study import (
    IngestResponse,
    SearchPapersRequest,
    SearchPapersResponse,
    PaperSchema,
    FetchPaperRequest,
    FetchPaperResponse,
    AskRequest,
    AskResponse,
    SourceSchema,
    HistoryItem,
    CategoryItem,
    ProgressResponse,
    ProgressOverview,
    CategoryProgress,
    StudyStreak,
    ProgressRecommendation,
    SurveyResponse,
    SurveyAnalysis,
    SurveyRecommendation,
    SurveyPaperSchema,
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizEvaluateRequest,
    QuizEvaluateResponse,
)
from services import vlm_service, embedding_service, oracle_service, arxiv_service
from services import search_service, llm_service, history_service, progress_service
from services import survey_agent, quiz_service
from services.paper_fetcher import fetch_and_ingest
from services.duplicate_checker import DuplicateDocumentError
from security.whitelist import DomainNotAllowedError
from security.sanitizer import sanitize_chunk
from security.audit import log_injection_detected, log_domain_rejected
from prompts.tutor import TUTOR_SYSTEM_PROMPT, format_tutor_prompt
from prompts.socratic import SOCRATIC_SYSTEM_PROMPT, format_socratic_prompt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/study", tags=["study"])

VALID_CATEGORIES = {
    "small_data", "digital_twin", "physics_ml", "transfer_learning",
    "synthetic_data", "materials", "manufacturing", "nlp_science",
    "pi_general", "meta_factory",
}


def _derive_doc_id(filename: str) -> str:
    """Convert filename to a URL-safe document ID."""
    name = os.path.splitext(filename)[0]
    doc_id = re.sub(r"[^a-zA-Z0-9]", "-", name).lower().strip("-")
    doc_id = re.sub(r"-+", "-", doc_id)
    return doc_id[:60]


def _extract_title(chunks: list[dict], filename: str) -> str:
    """Extract title from first text chunk, or fall back to filename."""
    for chunk in chunks:
        if chunk.get("type") in ("abstract", "text"):
            content = chunk.get("content", "")
            first_line = content.split("\n")[0].strip()
            if len(first_line) > 10:
                return first_line[:200]
    return os.path.splitext(filename)[0]


@router.post("/ingest", response_model=IngestResponse)
async def ingest_pdf(
    file: UploadFile = File(...),
    doc_type: str = Form("paper"),
    title: str = Form(None),
    source: str = Form(None),
    source_domain: str = Form(None),
):
    """
    Ingest a PDF document into the RAG pipeline.
    Pipeline: PDF -> page images -> VLM extraction -> embedding -> Oracle storage.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Save uploaded file to temp
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Step 1: 3-stage extraction (text + tables + VLM)
        logger.info(f"Starting extraction for: {file.filename}")
        raw_chunks, extraction_stats = await vlm_service.extract_from_pdf(tmp_path)

        if not raw_chunks:
            raise HTTPException(status_code=422, detail="Extraction produced zero chunks from PDF.")

        # Derive doc metadata
        doc_id = _derive_doc_id(file.filename)
        doc_title = title or _extract_title(raw_chunks, file.filename)

        # Step 2: Filter, normalize, and sanitize chunks
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

            # Sanitize against prompt injection
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
        if sanitized_count > 0:
            logger.info(f"Sanitized {sanitized_count} chunks in doc '{doc_id}'")

        if not valid_chunks:
            raise HTTPException(status_code=422, detail="All extracted chunks were filtered out.")

        # Step 3: Embed all chunk texts
        logger.info(f"Embedding {len(valid_chunks)} chunks")
        texts = [c["content"] for c in valid_chunks]
        embeddings = await embedding_service.embed_passages(texts)

        # Step 4: Insert doc into Oracle
        await oracle_service.insert_doc({
            "doc_id": doc_id,
            "title": doc_title,
            "doc_type": doc_type,
            "source": source,
            "source_domain": source_domain,
        })

        # Step 5: Insert chunks into Oracle
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

        # Step 6: Sync text index (non-fatal)
        try:
            await oracle_service.sync_text_index()
        except Exception as e:
            logger.warning(f"Text index sync deferred: {e}")

        # Update doc chunk count
        await oracle_service.update_doc_chunk_count(
            doc_id, len(valid_chunks), chunks_filtered
        )

        categories_detected = list({c["category"] for c in valid_chunks})

        logger.info(
            f"Ingestion complete: {doc_id} | {len(valid_chunks)} chunks | "
            f"{chunks_filtered} filtered | categories: {categories_detected}"
        )

        return IngestResponse(
            doc_id=doc_id,
            title=doc_title,
            doc_type=doc_type,
            chunks_created=len(valid_chunks),
            chunks_filtered=chunks_filtered,
            categories_detected=categories_detected,
            chunks_by_method=extraction_stats,
            vlm_pages_processed=extraction_stats.get("vlm_pages_processed", 0),
        )

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/search-papers", response_model=SearchPapersResponse)
async def search_papers(req: SearchPapersRequest):
    """
    Search for academic papers on arXiv.
    Returns papers with already_ingested flag checked against Oracle.
    """
    if req.source != "arxiv":
        raise HTTPException(status_code=400, detail=f"Unsupported source: {req.source}. Only 'arxiv' is supported.")

    try:
        papers = await arxiv_service.search(req.query, max_results=req.max_results)
    except arxiv_service.ArxivRateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))

    return SearchPapersResponse(
        papers=[PaperSchema(**p) for p in papers],
        total_found=len(papers),
    )


@router.post("/fetch-paper", response_model=FetchPaperResponse)
async def fetch_paper(req: FetchPaperRequest):
    """
    Fetch a paper PDF from a whitelisted URL and run the full ingestion pipeline.
    Returns 403 if domain not allowed, 409 if document already ingested.
    """
    try:
        result = await fetch_and_ingest(
            pdf_url=req.pdf_url,
            title=req.title,
            source=req.source,
        )
        return FetchPaperResponse(**result)

    except DomainNotAllowedError as e:
        log_domain_rejected(e.url, e.domain)
        return JSONResponse(
            status_code=403,
            content={
                "error": "DOMAIN_NOT_ALLOWED",
                "message": f"Domain '{e.domain}' is not in the allowed list.",
                "hint": "Add trusted domains to backend/security/whitelist.py",
            },
        )

    except DuplicateDocumentError as e:
        return JSONResponse(
            status_code=409,
            content={
                "error": "DUPLICATE",
                "existing_doc_id": e.existing_doc_id,
                "message": "Document already ingested.",
            },
        )


@router.post("/ask", response_model=AskResponse)
async def ask_question(req: AskRequest):
    """
    RAG Q&A endpoint. Retrieves relevant chunks, then generates an answer
    using the local LLM in tutor or socratic mode.
    """
    start = time.time()

    # Step 1: Hybrid search (vector + BM25 + RRF)
    results = await search_service.search(
        query=req.question,
        category_filter=req.category_filter,
        top_n=10,
    )

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No relevant passages found. Try ingesting papers first.",
        )

    # Step 2: Build prompt based on mode
    if req.mode == "tutor":
        prompt = format_tutor_prompt(results, req.question)
        system_prompt = TUTOR_SYSTEM_PROMPT
    else:
        prompt = format_socratic_prompt(results, req.question)
        system_prompt = SOCRATIC_SYSTEM_PROMPT

    # Step 3: Generate LLM response
    raw_response = await llm_service.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        model_mode=req.model_mode,
    )

    # Step 4: Build sources list
    sources = [
        SourceSchema(
            doc_title=r.get("doc_title", "Unknown"),
            page_hint=r.get("page_hint"),
            similarity=r.get("similarity"),
        )
        for r in results
    ]

    elapsed = round(time.time() - start, 1)

    # Step 5: Determine dominant category from search results
    cat_counts = Counter(r.get("category") for r in results if r.get("category"))
    dominant_category = cat_counts.most_common(1)[0][0] if cat_counts else None

    # Step 6: Build source_chunks for history
    history_sources = [
        {
            "doc_id": r.get("doc_id", ""),
            "chunk_id": r.get("chunk_id", ""),
            "page_hint": r.get("page_hint", ""),
            "similarity": r.get("similarity", 0),
            "category": r.get("category", ""),
        }
        for r in results
    ]

    # Step 7: Parse response based on mode
    if req.mode == "socratic":
        hint, follow_up = _parse_socratic_response(raw_response)
        answer_text = raw_response
        response = AskResponse(
            hint=hint,
            follow_up_question=follow_up,
            has_direct_answer=False,
            sources=sources,
            mode="socratic",
            model_mode=req.model_mode,
            processing_time_sec=elapsed,
        )
    else:
        answer_text = raw_response
        response = AskResponse(
            answer=raw_response,
            has_direct_answer=True,
            sources=sources,
            mode="tutor",
            model_mode=req.model_mode,
            processing_time_sec=elapsed,
        )

    # Step 8: Save to history (non-blocking, non-fatal)
    try:
        await history_service.save_history(
            question=req.question,
            answer=answer_text,
            study_mode=req.mode,
            model_mode=req.model_mode,
            source_chunks=history_sources,
            category=dominant_category,
        )
    except Exception as e:
        logger.warning(f"Failed to save history: {e}")

    return response


def _parse_socratic_response(text: str) -> tuple[str, str]:
    """Parse HINT: and FOLLOW_UP: from Socratic LLM response."""
    hint = text
    follow_up = ""

    if "HINT:" in text and "FOLLOW_UP:" in text:
        parts = text.split("FOLLOW_UP:", 1)
        hint_part = parts[0]
        follow_up = parts[1].strip() if len(parts) > 1 else ""
        if "HINT:" in hint_part:
            hint = hint_part.split("HINT:", 1)[1].strip()
        else:
            hint = hint_part.strip()
    elif "HINT:" in text:
        hint = text.split("HINT:", 1)[1].strip()
    elif "FOLLOW_UP:" in text:
        parts = text.split("FOLLOW_UP:", 1)
        hint = parts[0].strip()
        follow_up = parts[1].strip()

    return hint, follow_up


@router.get("/history", response_model=list[HistoryItem])
async def get_history(
    category: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """Retrieve Q&A history, optionally filtered by category."""
    rows = await history_service.get_history(category_filter=category, limit=limit)
    return [HistoryItem(**r) for r in rows]


@router.get("/categories", response_model=list[CategoryItem])
async def get_categories():
    """Return all categories with their chunk counts."""
    from services.progress_service import CATEGORY_LABELS
    cat_counts = await oracle_service.get_category_chunk_counts()
    items = []
    for cat, label in CATEGORY_LABELS.items():
        items.append(CategoryItem(
            category=cat,
            label=label,
            chunk_count=cat_counts.get(cat, 0),
        ))
    return items


@router.get("/progress", response_model=ProgressResponse)
async def get_progress():
    """Return full study progress analytics."""
    data = await progress_service.get_progress()
    return ProgressResponse(
        overview=ProgressOverview(**data["overview"]),
        by_category=[CategoryProgress(**c) for c in data["by_category"]],
        study_streak=StudyStreak(**data["study_streak"]),
        recommendation=ProgressRecommendation(**data["recommendation"]) if data["recommendation"] else None,
    )


@router.get("/survey", response_model=SurveyResponse)
async def run_survey():
    """
    Run the autonomous 5-step survey agent.
    Analyzes knowledge gaps, generates keywords, explores arXiv,
    and recommends papers with connection analysis.
    """
    result = await survey_agent.run_survey()

    recs = []
    for r in result.get("recommendations", []):
        recs.append(SurveyRecommendation(
            paper=SurveyPaperSchema(**r["paper"]),
            connection=r["connection"],
            target_category=r["target_category"],
            relevance=r["relevance"],
        ))

    return SurveyResponse(
        monologue=result.get("monologue", []),
        analysis=SurveyAnalysis(**result.get("analysis", {})),
        recommendations=recs,
        total_found=result.get("total_found", 0),
        total_recommended=result.get("total_recommended", 0),
    )


@router.post("/quiz/generate", response_model=QuizGenerateResponse)
async def quiz_generate(req: QuizGenerateRequest):
    """Generate a quiz question from a random chunk."""
    try:
        result = await quiz_service.generate_quiz(
            category=req.category,
            model_mode=req.model_mode,
            difficulty=req.difficulty,
        )
        return QuizGenerateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/quiz/evaluate", response_model=QuizEvaluateResponse)
async def quiz_evaluate(req: QuizEvaluateRequest):
    """Evaluate a user's answer to a quiz question."""
    try:
        result = await quiz_service.evaluate_quiz(
            quiz_id=req.quiz_id,
            user_answer=req.user_answer,
            model_mode=req.model_mode,
        )
        return QuizEvaluateResponse(**result)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
