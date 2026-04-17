"""
PI Study RAG Backend.

FastAPI application for paper ingestion, RAG queries, and study management.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.oracle_service import ensure_tables
from routers import study

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="PI Study RAG Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(study.router)


@app.on_event("startup")
async def startup():
    await ensure_tables()


@app.get("/health")
async def health():
    return {"status": "healthy"}
