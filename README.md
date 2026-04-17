# PI Study RAG

Personal knowledge base for Process Informatics research.
Search and learn from academic papers with VLM + RAG hybrid search.

> ⚠️ For personal study use only. Not intended for production deployment.
> All data sources are open-access papers and public documents.
> No copyrighted materials are stored in this repository.

## Features
- **Paper Ingestion** — Upload PDFs or fetch from arxiv. 3-stage extraction: PyMuPDF text → table detection → selective VLM (37x faster, $0 cost)
- **RAG Q&A** — Hybrid search (Vector HNSW + BM25 + RRF) with paper citations
- **Two Learning Modes** — Tutor (direct answers) and Socratic (guided thinking)
- **Local LLM** — Gemma 4 E4B via Ollama (runs on RTX 4070 SUPER 12GB)
- **Quiz Mode** — AI generates questions, evaluates answers, tracks mastery
- **Survey Agent** — Autonomous paper discovery with 4 strategies (Reinforce/Deepen/Bridge/Discover)
- **Learning Dashboard** — Coverage tracking, review status, study streak
- **3-Layer Security** — Domain whitelist → chunk sanitization → LLM prompt defense

## Live Demo

👉 [Try the demo (no Docker required)](https://seunghwan-dev.github.io/pi-study-rag/)

Frontend auto-detects backend availability and falls back to mock data when offline.

## Architecture
![Architecture](docs/architecture.svg)

## Tech Stack
| Component | Technology |
|-----------|-----------|
| VLM | GPT-4o Vision / Gemma 4 Vision (switchable) |
| RAG | Oracle 26ai (Vector HNSW + BM25 + RRF, k=60) |
| LLM | Gemma 4 E4B via Ollama |
| Embedding | multilingual-e5-large (1024dim) |
| Backend | FastAPI (Python), 10 API endpoints, 32 tests |
| Frontend | React 18 + TypeScript + Tailwind CSS v4 |

## Quick Start
```bash
git clone https://github.com/seunghwan-dev/pi-study-rag.git
cd pi-study-rag
cp .env.example .env
docker compose up -d
docker exec pi-study-rag-ollama-1 ollama pull gemma4:e4b
cd frontend && npm install && npm run dev
```

## Demo Mode
Frontend works without Docker — auto-detects backend and switches to mock data.
```bash
cd frontend && npm install && npm run dev
```

## API Endpoints (10)
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/study/ingest | Upload PDF → 3-stage extraction → Oracle |
| POST | /api/v1/study/ask | RAG Q&A (Tutor/Socratic modes) |
| POST | /api/v1/study/search-papers | Search arxiv for papers |
| POST | /api/v1/study/fetch-paper | Auto-download + ingest |
| GET | /api/v1/study/history | Study history |
| GET | /api/v1/study/categories | Category list |
| GET | /api/v1/study/progress | Coverage + review status |
| GET | /api/v1/study/survey | Survey agent |
| POST | /api/v1/study/quiz/generate | Quiz generation |
| POST | /api/v1/study/quiz/evaluate | Quiz evaluation |

## Security
1. **Domain Whitelist** — Only trusted academic sources
2. **Chunk Sanitization** — Prompt injection patterns filtered
3. **LLM Prompt Defense** — Retrieved passages marked as data-only

## 3-Stage Extraction Pipeline
| Stage | Method | Cost |
|-------|--------|------|
| Text | PyMuPDF | Free |
| Tables | PyMuPDF find_tables() | Free |
| Figures | GPT-4o Vision (selective) | ~$0.02/page |

Before: 22 pages → 1347s, $0.50 / After: 22 pages → 36s, $0.00 (**37x faster**)

## Pipeline Reuse from FieldOps-AI
| Aspect | FieldOps-AI | PI Study RAG |
|--------|-------------|-------------|
| Domain | Manufacturing | PI research |
| LLM | Qwen 2.5 7B | Gemma 4 E4B |
| Unique | ML+RAG Fusion | Survey + Quiz + 3-stage |

Same architecture, different domain.
