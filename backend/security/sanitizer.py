"""
Prompt-injection sanitizer for ingested document chunks.

Scans chunk text against known injection patterns and replaces
matches with [FILTERED] to prevent LLM manipulation at query time.
"""

import re
import logging

logger = logging.getLogger(__name__)

INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore\s+previous\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+previous", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"forget\s+your\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"<s>", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
]


def sanitize_chunk(text: str, doc_id: str) -> tuple[str, bool]:
    """
    Scan text for injection patterns and replace with [FILTERED].

    Returns (sanitized_text, was_modified).
    """
    was_modified = False

    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            logger.warning(
                f"Injection pattern detected in doc '{doc_id}': {pattern.pattern}"
            )
            text = pattern.sub("[FILTERED]", text)
            was_modified = True

    return text, was_modified
