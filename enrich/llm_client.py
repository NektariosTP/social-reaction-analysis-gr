"""LLM provider abstraction: Groq → Gemini → Ollama fallback.

Returns an instructor-patched client and the model string to use.
Calling code should never hard-code a provider or model name.
"""
from __future__ import annotations

import logging

import instructor

logger = logging.getLogger(__name__)

_AUTO_CHAIN = [
    ("groq_api_key", "groq/meta-llama/llama-4-scout-17b-16e-instruct"),
    ("gemini_api_key", "gemini/gemini-2.0-flash"),
]
_OLLAMA_FALLBACK = "ollama/gemma3:4b"


def get_llm_client_and_model() -> tuple[object, str]:
    """
    Detect the first available LLM provider and return (instructor_client, model_string).

    Resolution order (matches .env.example):
      1. Explicit LLM_MODEL env var (any provider the caller sets up manually)
      2. GROQ_API_KEY  → groq/llama-4-scout
      3. GEMINI_API_KEY → gemini/gemini-2.0-flash
      4. Ollama fallback (no key needed; must be running locally)
    """
    from enrich.config import settings

    if settings.llm_model:
        model = settings.llm_model
        logger.info("[llm] Using explicit LLM_MODEL=%s", model)
        return _build_client(model), model

    for key_attr, model in _AUTO_CHAIN:
        key_val = getattr(settings, key_attr, "")
        if key_val:
            logger.info("[llm] Auto-detected provider from %s → %s", key_attr, model)
            return _build_client(model, api_key=key_val), model

    logger.warning("[llm] No API key found — falling back to Ollama (%s)", _OLLAMA_FALLBACK)
    return _build_client(_OLLAMA_FALLBACK), _OLLAMA_FALLBACK


def _build_client(model: str, api_key: str | None = None) -> object:
    """Build an instructor-patched litellm client."""
    import litellm

    if api_key:
        litellm.api_key = api_key

    return instructor.from_litellm(litellm.completion, model=model)
