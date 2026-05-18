"""
Oracle Database Service for PI Study RAG.

Manages connection pooling (oracledb thin mode) and auto-creates
STUDY_DOCS, STUDY_CHUNKS, STUDY_HISTORY tables with HNSW vector
indexes and Oracle Text (BM25) indexes on first startup.
"""

import os
import json
import re
import logging
import oracledb

logger = logging.getLogger(__name__)

# DSN format: user/password@host:port/service
ORACLE_DSN = os.getenv("ORACLE_DSN")
if not ORACLE_DSN:
    raise RuntimeError(
        "ORACLE_DSN environment variable is required. "
        "Set it in .env (see .env.example for format)."
    )

_pool = None


def _parse_dsn(dsn: str) -> tuple[str, str, str]:
    """Parse 'user/password@host:port/service' into (user, password, connect_string)."""
    match = re.match(r"^(.+?)/(.+?)@(.+)$", dsn)
    if not match:
        raise ValueError(f"Invalid ORACLE_DSN format: {dsn}")
    return match.group(1), match.group(2), match.group(3)


async def _get_pool():
    """Get or create async connection pool (thin mode, no Instant Client)."""
    global _pool
    if _pool is None:
        user, password, connect_string = _parse_dsn(ORACLE_DSN)
        _pool = oracledb.create_pool_async(
            user=user,
            password=password,
            dsn=connect_string,
            min=2,
            max=5,
        )
    return _pool


# ---------------------------------------------------------------------------
# DDL statements -- executed once on startup if tables do not exist
# ---------------------------------------------------------------------------

_DDL_STUDY_DOCS = """
CREATE TABLE STUDY_DOCS (
    doc_id         VARCHAR2(64)   PRIMARY KEY,
    title          VARCHAR2(500)  NOT NULL,
    doc_type       VARCHAR2(20)   NOT NULL,
    source         VARCHAR2(200),
    source_domain  VARCHAR2(200),
    authors        VARCHAR2(1000),
    published_at   VARCHAR2(20),
    url            VARCHAR2(500),
    chunk_count    NUMBER         DEFAULT 0,
    chunks_filtered NUMBER        DEFAULT 0,
    uploaded_at    TIMESTAMP      DEFAULT SYSTIMESTAMP
)
"""

_DDL_STUDY_CHUNKS = """
CREATE TABLE STUDY_CHUNKS (
    chunk_id       VARCHAR2(64)   PRIMARY KEY,
    doc_id         VARCHAR2(64)   REFERENCES STUDY_DOCS,
    chunk_type     VARCHAR2(20)   NOT NULL,
    chunk_text     CLOB           NOT NULL,
    page_hint      VARCHAR2(50),
    category       VARCHAR2(50),
    is_sanitized   NUMBER(1)      DEFAULT 0,
    embedding      VECTOR(1024)   NOT NULL,
    created_at     TIMESTAMP      DEFAULT SYSTIMESTAMP
)
"""

_DDL_STUDY_HISTORY = """
CREATE TABLE STUDY_HISTORY (
    history_id     VARCHAR2(64)   PRIMARY KEY,
    question       CLOB           NOT NULL,
    answer         CLOB           NOT NULL,
    study_mode     VARCHAR2(20)   NOT NULL,
    model_mode     VARCHAR2(20)   NOT NULL,
    source_chunks  JSON,
    category       VARCHAR2(50),
    quiz_score     VARCHAR2(20),
    quiz_feedback  CLOB,
    user_answer    CLOB,
    created_at     TIMESTAMP      DEFAULT SYSTIMESTAMP
)
"""

# HNSW vector index for cosine similarity search on chunk embeddings
_DDL_VECTOR_INDEX = """
CREATE VECTOR INDEX idx_study_chunks_vec
    ON STUDY_CHUNKS(embedding)
    ORGANIZATION NEIGHBOR PARTITIONS
    DISTANCE COSINE
    WITH TARGET ACCURACY 95
"""

# Oracle Text (BM25) full-text index on chunk_text for keyword search
_DDL_BM25_INDEX = """
CREATE INDEX idx_study_chunks_text
    ON STUDY_CHUNKS(chunk_text)
    INDEXTYPE IS CTXSYS.CONTEXT
"""

_DDL_STATEMENTS = [
    ("STUDY_DOCS", _DDL_STUDY_DOCS),
    ("STUDY_CHUNKS", _DDL_STUDY_CHUNKS),
    ("STUDY_HISTORY", _DDL_STUDY_HISTORY),
]

_INDEX_STATEMENTS = [
    ("idx_study_chunks_vec", _DDL_VECTOR_INDEX),
    ("idx_study_chunks_text", _DDL_BM25_INDEX),
]


async def _table_exists(cursor, table_name: str) -> bool:
    await cursor.execute(
        "SELECT COUNT(*) FROM user_tables WHERE table_name = :1",
        [table_name],
    )
    row = await cursor.fetchone()
    return row[0] > 0


async def _index_exists(cursor, index_name: str) -> bool:
    await cursor.execute(
        "SELECT COUNT(*) FROM user_indexes WHERE index_name = :1",
        [index_name.upper()],
    )
    row = await cursor.fetchone()
    return row[0] > 0


async def ensure_tables():
    """Create tables and indexes if they do not exist. Called on app startup."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            for table_name, ddl in _DDL_STATEMENTS:
                if not await _table_exists(cursor, table_name):
                    logger.info(f"Creating table: {table_name}")
                    await cursor.execute(ddl)
                else:
                    logger.info(f"Table already exists: {table_name}")

            # Grant CTXAPP for Oracle Text sync (needed for BM25 index)
            try:
                await cursor.execute("GRANT CTXAPP TO PDBADMIN")
            except oracledb.DatabaseError:
                pass  # Already granted or not applicable

            for index_name, ddl in _INDEX_STATEMENTS:
                if not await _index_exists(cursor, index_name):
                    logger.info(f"Creating index: {index_name}")
                    try:
                        await cursor.execute(ddl)
                    except oracledb.DatabaseError as e:
                        # Vector index requires data in table; BM25 may need CTXAPP
                        logger.warning(f"Index creation deferred ({index_name}): {e}")
                else:
                    logger.info(f"Index already exists: {index_name}")

        await conn.commit()
    logger.info("DDL initialization complete")


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

async def insert_doc(doc: dict) -> str:
    """Insert or replace a document in STUDY_DOCS."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM STUDY_CHUNKS WHERE doc_id = :1", [doc["doc_id"]]
            )
            await cursor.execute(
                "DELETE FROM STUDY_DOCS WHERE doc_id = :1", [doc["doc_id"]]
            )
            await cursor.execute(
                """INSERT INTO STUDY_DOCS
                   (doc_id, title, doc_type, source, source_domain,
                    authors, published_at, url)
                   VALUES (:1, :2, :3, :4, :5, :6, :7, :8)""",
                [
                    doc["doc_id"],
                    doc["title"],
                    doc["doc_type"],
                    doc.get("source"),
                    doc.get("source_domain"),
                    doc.get("authors"),
                    doc.get("published_at"),
                    doc.get("url"),
                ],
            )
            await conn.commit()
    logger.info(f"Inserted doc: {doc['doc_id']}")
    return doc["doc_id"]


async def insert_chunks(chunks: list[dict]) -> int:
    """Bulk insert chunks into STUDY_CHUNKS with CLOB + VECTOR handling."""
    if not chunks:
        return 0

    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            cursor.setinputsizes(
                None,                       # chunk_id
                None,                       # doc_id
                None,                       # chunk_type
                oracledb.DB_TYPE_CLOB,      # chunk_text
                None,                       # page_hint
                None,                       # category
                None,                       # is_sanitized
                oracledb.DB_TYPE_VECTOR,    # embedding
            )
            rows = []
            for c in chunks:
                embedding = c.get("embedding")
                if embedding is not None:
                    embedding = json.dumps(embedding)
                rows.append([
                    c["chunk_id"],
                    c["doc_id"],
                    c["chunk_type"],
                    c["chunk_text"],
                    c.get("page_hint"),
                    c.get("category"),
                    c.get("is_sanitized", 0),
                    embedding,
                ])
            await cursor.executemany(
                """INSERT INTO STUDY_CHUNKS
                   (chunk_id, doc_id, chunk_type, chunk_text,
                    page_hint, category, is_sanitized, embedding)
                   VALUES (:1, :2, :3, :4, :5, :6, :7, :8)""",
                rows,
            )
        await conn.commit()

    count = len(chunks)
    logger.info(f"Inserted {count} chunks for doc '{chunks[0]['doc_id']}'")
    return count


async def vector_search(query_vector: list[float], max_results: int = 10) -> list[dict]:
    """Cosine similarity search on STUDY_CHUNKS using HNSW index."""
    sql = """
        SELECT c.chunk_id, c.chunk_type, c.chunk_text, c.page_hint,
               c.category, c.doc_id,
               d.title,
               VECTOR_DISTANCE(c.embedding, :query_vec, COSINE) as distance
        FROM STUDY_CHUNKS c
        JOIN STUDY_DOCS d ON c.doc_id = d.doc_id
        ORDER BY distance
        FETCH FIRST :max_results ROWS ONLY
    """
    pool = await _get_pool()
    results = []
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            cursor.setinputsizes(query_vec=oracledb.DB_TYPE_VECTOR)
            await cursor.execute(sql, {
                "query_vec": json.dumps(query_vector),
                "max_results": max_results,
            })
            rows = await cursor.fetchall()
            for row in rows:
                chunk_text = row[2]
                if hasattr(chunk_text, "read"):
                    chunk_text = await chunk_text.read()
                results.append({
                    "chunk_id": row[0],
                    "chunk_type": row[1],
                    "chunk_text": str(chunk_text),
                    "page_hint": row[3],
                    "category": row[4],
                    "doc_id": row[5],
                    "doc_title": row[6],
                    "similarity": round(1.0 - float(row[7]), 4),
                    "search_method": "vector",
                })
    return results


async def bm25_search(query_text: str, max_results: int = 10) -> list[dict]:
    """Oracle Text (BM25) full-text search on STUDY_CHUNKS."""
    # Strip special chars that break CONTAINS syntax, join with AND
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", query_text).strip()
    words = [w for w in cleaned.split() if len(w) >= 2]
    if not words:
        return []
    escaped_query = " AND ".join(words)

    sql = """
        SELECT c.chunk_id, c.chunk_type, c.chunk_text, c.page_hint,
               c.category, c.doc_id,
               d.title,
               SCORE(1) as relevance_score
        FROM STUDY_CHUNKS c
        JOIN STUDY_DOCS d ON c.doc_id = d.doc_id
        WHERE CONTAINS(c.chunk_text, :query_text, 1) > 0
        ORDER BY relevance_score DESC
        FETCH FIRST :max_results ROWS ONLY
    """
    pool = await _get_pool()
    results = []
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(sql, {
                "query_text": escaped_query,
                "max_results": max_results,
            })
            rows = await cursor.fetchall()
            for row in rows:
                bm25_score = float(row[7]) if row[7] else 0
                normalized = min(0.80 + (bm25_score / 500), 1.0)
                chunk_text = row[2]
                if hasattr(chunk_text, "read"):
                    chunk_text = await chunk_text.read()
                results.append({
                    "chunk_id": row[0],
                    "chunk_type": row[1],
                    "chunk_text": str(chunk_text),
                    "page_hint": row[3],
                    "category": row[4],
                    "doc_id": row[5],
                    "doc_title": row[6],
                    "similarity": round(normalized, 4),
                    "search_method": "bm25",
                })
    return results


async def sync_text_index():
    """Sync Oracle Text index after bulk inserts."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "BEGIN CTX_DDL.SYNC_INDEX('idx_study_chunks_text'); END;"
            )
        await conn.commit()


async def update_doc_chunk_count(doc_id: str, chunk_count: int, chunks_filtered: int):
    """Update chunk counts on STUDY_DOCS after ingestion."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                """UPDATE STUDY_DOCS
                   SET chunk_count = :1, chunks_filtered = :2
                   WHERE doc_id = :3""",
                [chunk_count, chunks_filtered, doc_id],
            )
        await conn.commit()
    logger.info(f"Updated chunk count for doc '{doc_id}': {chunk_count} chunks, {chunks_filtered} filtered")


async def check_url_exists(url: str) -> bool:
    """Check if a URL already exists in STUDY_DOCS."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT COUNT(*) FROM STUDY_DOCS WHERE url = :1", [url]
            )
            row = await cursor.fetchone()
            return row[0] > 0


async def get_all_doc_titles() -> list[dict]:
    """Return all doc_id, title, url from STUDY_DOCS for duplicate checking."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT doc_id, title, url FROM STUDY_DOCS"
            )
            rows = await cursor.fetchall()
            return [
                {"doc_id": r[0], "title": r[1], "url": r[2]}
                for r in rows
            ]


async def get_random_chunk(category: str | None = None) -> dict | None:
    """Select a random chunk from STUDY_CHUNKS, optionally filtered by category."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            if category:
                sql = """SELECT chunk_id, doc_id, chunk_text, page_hint, category
                         FROM STUDY_CHUNKS WHERE category = :cat
                         ORDER BY DBMS_RANDOM.VALUE
                         FETCH FIRST 1 ROWS ONLY"""
                await cursor.execute(sql, {"cat": category})
            else:
                sql = """SELECT chunk_id, doc_id, chunk_text, page_hint, category
                         FROM STUDY_CHUNKS
                         ORDER BY DBMS_RANDOM.VALUE
                         FETCH FIRST 1 ROWS ONLY"""
                await cursor.execute(sql)
            row = await cursor.fetchone()
            if not row:
                return None
            chunk_text = row[2]
            if hasattr(chunk_text, "read"):
                chunk_text = await chunk_text.read()
            return {
                "chunk_id": row[0],
                "doc_id": row[1],
                "chunk_text": str(chunk_text),
                "page_hint": row[3],
                "category": row[4],
            }


async def get_doc_title(doc_id: str) -> str:
    """Get the title of a document by doc_id."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT title FROM STUDY_DOCS WHERE doc_id = :1", [doc_id]
            )
            row = await cursor.fetchone()
            return row[0] if row else "Unknown"


async def get_history_rows(category_filter: str | None, limit: int = 20) -> list[dict]:
    """Retrieve recent history entries from STUDY_HISTORY."""
    pool = await _get_pool()
    results = []
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            if category_filter:
                sql = """SELECT history_id, question, answer, study_mode, model_mode,
                                category, quiz_score, created_at
                         FROM STUDY_HISTORY WHERE category = :cat
                         ORDER BY created_at DESC
                         FETCH FIRST :lim ROWS ONLY"""
                await cursor.execute(sql, {"cat": category_filter, "lim": limit})
            else:
                sql = """SELECT history_id, question, answer, study_mode, model_mode,
                                category, quiz_score, created_at
                         FROM STUDY_HISTORY
                         ORDER BY created_at DESC
                         FETCH FIRST :lim ROWS ONLY"""
                await cursor.execute(sql, {"lim": limit})
            rows = await cursor.fetchall()
            for row in rows:
                question = row[1]
                if hasattr(question, "read"):
                    question = await question.read()
                answer = row[2]
                if hasattr(answer, "read"):
                    answer = await answer.read()
                answer_str = str(answer) if answer else ""
                results.append({
                    "history_id": row[0],
                    "question": str(question),
                    "answer_preview": answer_str[:100],
                    "study_mode": row[3],
                    "model_mode": row[4],
                    "category": row[5],
                    "quiz_score": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                })
    return results


async def get_category_chunk_counts() -> dict[str, int]:
    """Return {category: count} from STUDY_CHUNKS."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT category, COUNT(*) FROM STUDY_CHUNKS GROUP BY category"
            )
            rows = await cursor.fetchall()
            return {r[0]: r[1] for r in rows if r[0]}


async def get_all_history_source_chunks() -> list[dict]:
    """Return all source_chunks JSON from STUDY_HISTORY for progress computation."""
    pool = await _get_pool()
    results = []
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT source_chunks FROM STUDY_HISTORY")
            rows = await cursor.fetchall()
            for row in rows:
                sc = row[0]
                if hasattr(sc, "read"):
                    sc = await sc.read()
                results.append({"source_chunks": sc})
    return results


async def get_history_stats(category: str) -> dict:
    """Return question count and last studied timestamp for a category."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                """SELECT COUNT(*), MAX(created_at)
                   FROM STUDY_HISTORY WHERE category = :cat""",
                {"cat": category},
            )
            row = await cursor.fetchone()
            return {"count": row[0] or 0, "last_studied": row[1]}


async def count_history_since(since: object) -> int:
    """Count history entries since a given timestamp."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT COUNT(*) FROM STUDY_HISTORY WHERE created_at >= :since",
                {"since": since},
            )
            row = await cursor.fetchone()
            return row[0] or 0


async def insert_history(record: dict) -> str:
    """Insert a Q&A history record into STUDY_HISTORY."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            source_chunks = record.get("source_chunks")
            if source_chunks is not None:
                source_chunks = json.dumps(source_chunks)
            cursor.setinputsizes(
                None,                       # history_id
                oracledb.DB_TYPE_CLOB,      # question
                oracledb.DB_TYPE_CLOB,      # answer
                None,                       # mode
                None,                       # model_mode
                None,                       # source_chunks (JSON)
                None,                       # category
                None,                       # quiz_score
                oracledb.DB_TYPE_CLOB,      # quiz_feedback
                oracledb.DB_TYPE_CLOB,      # user_answer
            )
            await cursor.execute(
                """INSERT INTO STUDY_HISTORY
                   (history_id, question, answer, study_mode, model_mode,
                    source_chunks, category, quiz_score, quiz_feedback, user_answer)
                   VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10)""",
                [
                    record["history_id"],
                    record["question"],
                    record["answer"],
                    record["study_mode"],
                    record["model_mode"],
                    source_chunks,
                    record.get("category"),
                    record.get("quiz_score"),
                    record.get("quiz_feedback"),
                    record.get("user_answer"),
                ],
            )
        await conn.commit()
    logger.info(f"Inserted history: {record['history_id']}")
    return record["history_id"]
