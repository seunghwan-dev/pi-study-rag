"""
LLM Service — Ollama HTTP API client.

Calls local Ollama instance for text generation using Gemma 4 models.
"""

import os
import logging
import httpx

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL_FAST = os.getenv("OLLAMA_MODEL_FAST", "gemma4:e4b")


async def generate(
    prompt: str,
    system_prompt: str = "",
    model_mode: str = "fast",
    temperature: float = 0.3,
) -> str:
    """
    Generate text using Ollama API (non-streaming).

    model_mode kept for backward compatibility; single model (Gemma 4 E4B) is always used.
    """
    del model_mode
    model = OLLAMA_MODEL_FAST
    url = f"{OLLAMA_HOST}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }

    logger.info(f"LLM generate: model={model}, prompt_len={len(prompt)}")

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    response_text = data.get("response", "").strip()
    logger.info(f"LLM response: {len(response_text)} chars")
    return response_text
