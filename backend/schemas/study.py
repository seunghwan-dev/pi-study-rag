"""
Pydantic schemas for the Study ingestion pipeline.
"""

from pydantic import BaseModel, Field


class ChunkSchema(BaseModel):
    """Single extracted chunk from a document."""
    chunk_id: str
    chunk_type: str
    content: str
    page_hint: str | None = None
    category: str | None = None


class IngestResponse(BaseModel):
    """Response from POST /api/v1/study/ingest."""
    doc_id: str
    title: str
    doc_type: str
    chunks_created: int
    chunks_filtered: int
    categories_detected: list[str]
    chunks_by_method: dict | None = None
    vlm_pages_processed: int = 0


# --- Paper search schemas ---

class PaperSchema(BaseModel):
    """Single paper result from arXiv search."""
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    published: str
    pdf_url: str
    already_ingested: bool = False


class SearchPapersRequest(BaseModel):
    """Request body for POST /api/v1/study/search-papers."""
    query: str
    source: str = "arxiv"
    max_results: int = Field(default=10, ge=1, le=50)


class SearchPapersResponse(BaseModel):
    """Response from POST /api/v1/study/search-papers."""
    papers: list[PaperSchema]
    total_found: int


class FetchPaperRequest(BaseModel):
    """Request body for fetching a paper PDF by URL."""
    pdf_url: str
    title: str | None = None
    source: str | None = None


class FetchPaperResponse(BaseModel):
    """Response from POST /api/v1/study/fetch-paper."""
    doc_id: str
    title: str
    chunks_created: int
    chunks_filtered: int
    categories_detected: list[str]
    processing_time_sec: float
    chunks_by_method: dict | None = None
    vlm_pages_processed: int = 0


# --- Ask (RAG Q&A) schemas ---

class SourceSchema(BaseModel):
    """Source citation in a RAG answer."""
    doc_title: str
    page_hint: str | None = None
    similarity: float | None = None


class AskRequest(BaseModel):
    """Request body for POST /api/v1/study/ask."""
    question: str
    mode: str = Field(default="tutor", pattern="^(tutor|socratic)$")
    model_mode: str = Field(default="fast", pattern="^(fast|smart)$")
    category_filter: str | None = None


class AskResponse(BaseModel):
    """Response from POST /api/v1/study/ask."""
    answer: str | None = None
    hint: str | None = None
    follow_up_question: str | None = None
    has_direct_answer: bool = True
    sources: list[SourceSchema]
    mode: str
    model_mode: str
    processing_time_sec: float


# --- History schemas ---

class HistoryItem(BaseModel):
    """Single history entry."""
    history_id: str
    question: str
    answer_preview: str
    study_mode: str
    model_mode: str
    category: str | None = None
    quiz_score: str | None = None
    created_at: str | None = None


# --- Categories schema ---

class CategoryItem(BaseModel):
    """Category with chunk count."""
    category: str
    label: str
    chunk_count: int


# --- Progress schemas ---

class ProgressOverview(BaseModel):
    """Top-level study statistics."""
    total_papers: int
    total_chunks: int
    total_questions: int
    unique_chunks_cited: int
    overall_coverage: float


class CategoryProgress(BaseModel):
    """Per-category progress detail."""
    category: str
    label: str
    chunk_count: int
    chunks_cited: int
    coverage: float
    question_count: int
    last_studied: str | None = None
    days_since_last: int | None = None
    review_status: str


class StudyStreak(BaseModel):
    """Activity counts over time windows."""
    today: int
    this_week: int
    this_month: int


class ProgressRecommendation(BaseModel):
    """Review recommendation for a category."""
    category: str
    message: str
    reason: str


class ProgressResponse(BaseModel):
    """Full progress report."""
    overview: ProgressOverview
    by_category: list[CategoryProgress]
    study_streak: StudyStreak
    recommendation: ProgressRecommendation | None = None


# --- Survey schemas ---

class SurveyPaperSchema(BaseModel):
    """Paper discovered by the survey agent."""
    title: str
    authors: list[str] = []
    arxiv_id: str
    pdf_url: str
    is_open_access: bool = True


class SurveyRecommendation(BaseModel):
    """Paper recommendation with connection analysis."""
    paper: SurveyPaperSchema
    connection: str
    target_category: str
    relevance: float


class SurveyAnalysis(BaseModel):
    """Survey agent analysis results."""
    strongest: dict | None = None
    weakest: dict | None = None
    recent_trend: str | None = None
    auto_keywords: list[str] = []


class SurveyResponse(BaseModel):
    """Full survey agent response."""
    monologue: list[str]
    analysis: SurveyAnalysis
    recommendations: list[SurveyRecommendation]
    total_found: int
    total_recommended: int


# --- Quiz schemas ---

class QuizGenerateRequest(BaseModel):
    """Request body for POST /api/v1/study/quiz/generate."""
    category: str | None = None
    model_mode: str = Field(default="fast", pattern="^(fast|smart)$")
    difficulty: str = Field(default="auto", pattern="^(auto|basic|intermediate|advanced)$")


class QuizGenerateResponse(BaseModel):
    """Response from quiz generation."""
    quiz_id: str
    question: str
    source: dict
    category: str
    difficulty: str


class QuizEvaluateRequest(BaseModel):
    """Request body for POST /api/v1/study/quiz/evaluate."""
    quiz_id: str
    user_answer: str
    model_mode: str = Field(default="fast", pattern="^(fast|smart)$")


class QuizEvaluateResponse(BaseModel):
    """Response from quiz evaluation."""
    score: str
    feedback: str
    complete_answer: str
    source: str
    mastery_update: str
