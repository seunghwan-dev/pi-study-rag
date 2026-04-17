"""
Security audit logger for the ingestion pipeline.

Provides structured logging for injection detection, fetch events,
and domain validation results.
"""

import logging

security_logger = logging.getLogger("security.audit")
security_logger.setLevel(logging.INFO)


def log_injection_detected(doc_id: str, chunk_id: str, pattern: str):
    """Log a detected prompt-injection pattern in a chunk."""
    security_logger.warning(
        f"INJECTION_DETECTED | doc={doc_id} | chunk={chunk_id} | pattern={pattern}"
    )


def log_fetch_success(url: str, doc_id: str, chunks: int):
    """Log a successful document fetch and extraction."""
    security_logger.info(
        f"FETCH_SUCCESS | url={url} | doc={doc_id} | chunks={chunks}"
    )


def log_domain_rejected(url: str, domain: str):
    """Log a rejected fetch attempt due to domain not in allowlist."""
    security_logger.warning(
        f"DOMAIN_REJECTED | url={url} | domain={domain}"
    )
