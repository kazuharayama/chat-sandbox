import logging
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama

from core.config import Settings
from models.agent_config import LLMModelInfo

logger = logging.getLogger(__name__)


def create_llm(model: LLMModelInfo, settings: Settings) -> BaseChatModel:
    """Create a LangChain chat model instance based on provider type."""
    config = model.config or {}

    if model.provider == "openai_compatible":
        # Any OpenAI-compatible server: vLLM, llama.cpp, LM Studio, TGI, LocalAI, Ollama(/v1) ...
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model.deployment_name,
            base_url=config.get("base_url", settings.llm_base_url),
            api_key=config.get("api_key", "dummy"),  # local servers ignore the key
            temperature=model.temperature or 0.7,
            max_tokens=model.max_tokens,
        )

    # Default: Ollama (native API)
    return ChatOllama(
        model=model.deployment_name,
        base_url=config.get("base_url", settings.llm_base_url),
        temperature=model.temperature or 0.7,
        num_predict=model.max_tokens,
    )


_llm_cache: dict[str, tuple[BaseChatModel, float]] = {}
_CACHE_TTL = 60.0  # seconds


def get_or_create_llm(model: LLMModelInfo, settings: Settings) -> BaseChatModel:
    """Get a cached LLM instance or create a new one. TTL-based cache."""
    import time
    cache_key = f"{model.provider}:{model.id}:{model.temperature}:{model.max_tokens}"
    now = time.time()

    if cache_key in _llm_cache:
        cached_llm, cached_at = _llm_cache[cache_key]
        if now - cached_at < _CACHE_TTL:
            return cached_llm

    llm = create_llm(model, settings)
    _llm_cache[cache_key] = (llm, now)
    logger.info("Created LLM instance: provider=%s, model=%s", model.provider, model.deployment_name)
    return llm


def clear_llm_cache() -> None:
    """Clear all cached LLM instances."""
    _llm_cache.clear()
    logger.info("LLM cache cleared")
