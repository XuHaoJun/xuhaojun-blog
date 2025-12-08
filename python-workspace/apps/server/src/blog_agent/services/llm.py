"""LlamaIndex LLM initialization helper."""

from typing import Union

from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI

from blog_agent.config import config
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


def get_llm() -> Union[Ollama, OpenAI]:
    """
    Get LlamaIndex LLM instance configured from environment.
    
    Supports both Ollama (default) and OpenAI providers.
    
    Returns:
        Configured LLM instance (Ollama or OpenAI)
    """
    if config.LLM_PROVIDER.lower() == "ollama":
        llm = Ollama(
            model=config.LLM_MODEL,
            temperature=config.LLM_TEMPERATURE,
            base_url=config.OLLAMA_BASE_URL,
            request_timeout=120.0,  # Ollama can be slower, increase timeout
        )
        logger.debug("Initialized LlamaIndex Ollama LLM", model=config.LLM_MODEL, base_url=config.OLLAMA_BASE_URL)
    elif config.LLM_PROVIDER.lower() == "openai":
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER is 'openai'")
        llm = OpenAI(
            api_key=config.OPENAI_API_KEY,
            model=config.LLM_MODEL,
            temperature=config.LLM_TEMPERATURE,
        )
        logger.debug("Initialized LlamaIndex OpenAI LLM", model=config.LLM_MODEL)
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {config.LLM_PROVIDER}. Must be 'ollama' or 'openai'")
    
    # Set as default in Settings for LlamaIndex workflows
    Settings.llm = llm
    
    return llm

