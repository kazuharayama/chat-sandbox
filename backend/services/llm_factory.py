import logging
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from core.config import Settings
from models.agent_config import LLMModelInfo

logger = logging.getLogger(__name__)


def create_llm(model: LLMModelInfo, settings: Settings) -> BaseChatModel:
    """Create a LangChain chat model instance based on provider type."""
    config = model.config or {}

    if model.provider == "azure_openai":
        return AzureChatOpenAI(
            azure_deployment=model.deployment_name,
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=config.get("api_version", settings.azure_openai_api_version),
            temperature=model.temperature or 0.7,
            max_tokens=model.max_tokens,
            streaming=True,
        )
    elif model.provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise ImportError("langchain-ollama is required for Ollama provider. Run: pip install langchain-ollama")
        return ChatOllama(
            model=model.deployment_name,
            base_url=config.get("base_url", "http://ollama:11434"),
            temperature=model.temperature or 0.7,
            num_predict=model.max_tokens,
        )
    elif model.provider == "vllm":
        return ChatOpenAI(
            model=model.deployment_name,
            base_url=config.get("base_url", "http://vllm:8000/v1"),
            api_key="not-needed",
            temperature=model.temperature or 0.7,
            max_tokens=model.max_tokens,
            streaming=True,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {model.provider}")


_llm_cache: dict[str, tuple[BaseChatModel, float]] = {}
_CACHE_TTL = 60.0  # seconds


def get_or_create_llm(model: LLMModelInfo, settings: Settings) -> BaseChatModel:
    """Get a cached LLM instance or create a new one. TTL-based cache."""
    import time
    cache_key = f"{model.id}:{model.temperature}:{model.max_tokens}"
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
