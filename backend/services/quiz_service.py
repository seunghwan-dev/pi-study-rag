"""
Quiz Service — generate exam questions and evaluate answers.

Uses random chunks from Oracle, LLM for question generation and grading,
and history service for persistence.
"""

import json
import re
import uuid
import logging

from services import oracle_service, llm_service, history_service
from prompts.quiz import QUIZ_GENERATE_PROMPT, QUIZ_EVALUATE_PROMPT

logger = logging.getLogger(__name__)

# In-memory cache of active quizzes (cleared after evaluation)
_active_quizzes: dict[str, dict] = {}


async def generate_quiz(
    category: str | None = None,
    model_mode: str = "fast",
    difficulty: str = "auto",
) -> dict:
    """
    Generate a quiz question from a random chunk.
    Returns quiz_id, question, source, category, difficulty.
    """
    # Step 1: Get random chunk
    chunk = await oracle_service.get_random_chunk(category)
    if not chunk:
        raise ValueError("No chunks available for quiz generation.")

    # Step 2: Get doc title
    doc_title = await oracle_service.get_doc_title(chunk["doc_id"])

    # Step 3: Generate question via LLM
    prompt = QUIZ_GENERATE_PROMPT.format(
        chunk_text=chunk["chunk_text"][:2000],
        doc_title=doc_title,
        page_hint=chunk.get("page_hint", ""),
    )
    if difficulty != "auto":
        prompt += f"\nTarget difficulty level: {difficulty}."

    raw = await llm_service.generate(
        prompt=prompt,
        system_prompt="Output JSON only. No markdown.",
        model_mode=model_mode,
        temperature=0.5,
    )

    parsed = _parse_json(raw)
    question = parsed.get("question", raw)
    difficulty = parsed.get("difficulty", "intermediate")

    # Step 4: Cache quiz data
    quiz_id = str(uuid.uuid4())[:16]
    _active_quizzes[quiz_id] = {
        "chunk_id": chunk["chunk_id"],
        "chunk_text": chunk["chunk_text"],
        "doc_id": chunk["doc_id"],
        "doc_title": doc_title,
        "page_hint": chunk.get("page_hint", ""),
        "category": chunk.get("category", ""),
        "question": question,
    }

    logger.info(f"Quiz generated: {quiz_id} (cat={chunk.get('category')}, diff={difficulty})")

    return {
        "quiz_id": quiz_id,
        "question": question,
        "source": {
            "doc_title": doc_title,
            "page_hint": chunk.get("page_hint", ""),
        },
        "category": chunk.get("category", ""),
        "difficulty": difficulty,
    }


async def evaluate_quiz(
    quiz_id: str,
    user_answer: str,
    model_mode: str = "fast",
) -> dict:
    """
    Evaluate a user's answer against the original chunk.
    Returns score, feedback, complete_answer, source.
    """
    # Step 1: Retrieve quiz data
    quiz = _active_quizzes.get(quiz_id)
    if not quiz:
        raise KeyError(f"Quiz not found: {quiz_id}. It may have expired or already been evaluated.")

    # Step 2: Evaluate via LLM
    prompt = QUIZ_EVALUATE_PROMPT.format(
        question=quiz["question"],
        chunk_text=quiz["chunk_text"][:2000],
        user_answer=user_answer,
    )

    raw = await llm_service.generate(
        prompt=prompt,
        system_prompt="Output JSON only. No markdown.",
        model_mode=model_mode,
        temperature=0.2,
    )

    parsed = _parse_json(raw)
    score = parsed.get("score", "partially_correct")
    feedback = parsed.get("feedback", raw)
    complete_answer = parsed.get("complete_answer", "")
    source = parsed.get("source", "")
    if not _is_valid_source(source):
        source = "論文本文"

    # Step 3: Save to history
    try:
        await history_service.save_history(
            question=quiz["question"],
            answer=complete_answer or feedback,
            study_mode="quiz",
            model_mode=model_mode,
            source_chunks=[{
                "doc_id": quiz["doc_id"],
                "chunk_id": quiz["chunk_id"],
                "page_hint": quiz["page_hint"],
                "category": quiz["category"],
            }],
            category=quiz["category"],
            quiz_score=score,
            quiz_feedback=feedback,
            user_answer=user_answer,
        )
    except Exception as e:
        logger.warning(f"Failed to save quiz history: {e}")

    # Step 4: Remove from cache
    del _active_quizzes[quiz_id]

    logger.info(f"Quiz evaluated: {quiz_id} -> {score}")

    return {
        "score": score,
        "feedback": feedback,
        "complete_answer": complete_answer,
        "source": source,
        "mastery_update": "quiz_score saved",
    }


def _is_valid_source(s: str) -> bool:
    """Validate source field: short Japanese phrase or empty.

    Rejects English prose, long strings, and section codes that the LLM
    sometimes emits despite prompt rules.
    """
    if not s or not s.strip():
        return True
    s = s.strip()
    if len(s) > 30:
        return False
    if re.search(r"[A-Za-z]{4,}", s):
        return False
    return True


def _parse_json(text: str) -> dict:
    """Parse JSON from LLM response, stripping markdown fences and preamble."""
    text = text.strip()
    # Strip markdown fences (```json ... ```)
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    if text.lower().startswith("json"):
        text = text[4:].strip()

    # If LLM added preamble before the JSON object, extract it
    brace = text.find("{")
    if brace > 0:
        text = text[brace:]

    # Trim anything after the closing brace
    depth, end = 0, -1
    for i, ch in enumerate(text):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end > 0:
        text = text[: end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse quiz JSON: {text[:200]}")
        return {}
