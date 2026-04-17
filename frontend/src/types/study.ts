// Backend API type definitions

export interface SourceSchema {
  doc_title: string;
  page_hint: string | null;
  similarity: number | null;
}

export interface IngestResponse {
  doc_id: string;
  title: string;
  doc_type: string;
  chunks_created: number;
  chunks_filtered: number;
  categories_detected: string[];
  chunks_by_method: Record<string, number> | null;
  vlm_pages_processed: number;
}

export interface PaperSchema {
  arxiv_id: string;
  title: string;
  authors: string[];
  abstract: string;
  published: string;
  pdf_url: string;
  already_ingested: boolean;
}

export interface SearchPapersResponse {
  papers: PaperSchema[];
  total_found: number;
}

export interface FetchPaperResponse {
  doc_id: string;
  title: string;
  chunks_created: number;
  chunks_filtered: number;
  categories_detected: string[];
  processing_time_sec: number;
  chunks_by_method: Record<string, number> | null;
  vlm_pages_processed: number;
}

export interface AskResponse {
  answer: string | null;
  hint: string | null;
  follow_up_question: string | null;
  has_direct_answer: boolean;
  sources: SourceSchema[];
  mode: string;
  model_mode: string;
  processing_time_sec: number;
}

export interface HistoryItem {
  history_id: string;
  question: string;
  answer_preview: string;
  study_mode: string;
  model_mode: string;
  category: string | null;
  quiz_score: string | null;
  created_at: string | null;
}

export interface CategoryItem {
  category: string;
  label: string;
  chunk_count: number;
}

export interface ProgressOverview {
  total_papers: number;
  total_chunks: number;
  total_questions: number;
  unique_chunks_cited: number;
  overall_coverage: number;
}

export interface CategoryProgress {
  category: string;
  label: string;
  chunk_count: number;
  chunks_cited: number;
  coverage: number;
  question_count: number;
  last_studied: string | null;
  days_since_last: number | null;
  review_status: string;
}

export interface ProgressResponse {
  overview: ProgressOverview;
  by_category: CategoryProgress[];
  study_streak: { today: number; this_week: number; this_month: number };
  recommendation: { category: string; message: string; reason: string } | null;
}

export interface SurveyRecommendation {
  paper: {
    title: string;
    authors: string[];
    arxiv_id: string;
    pdf_url: string;
    is_open_access: boolean;
  };
  connection: string;
  target_category: string;
  relevance: number;
}

export interface SurveyResponse {
  monologue: string[];
  analysis: {
    strongest: Record<string, unknown> | null;
    weakest: Record<string, unknown> | null;
    recent_trend: string | null;
    auto_keywords: string[];
  };
  recommendations: SurveyRecommendation[];
  total_found: number;
  total_recommended: number;
}

export interface QuizGenerateResponse {
  quiz_id: string;
  question: string;
  source: { doc_title: string; page_hint: string };
  category: string;
  difficulty: string;
}

export interface QuizEvaluateResponse {
  score: string;
  feedback: string;
  complete_answer: string;
  source: string;
  mastery_update: string;
}
