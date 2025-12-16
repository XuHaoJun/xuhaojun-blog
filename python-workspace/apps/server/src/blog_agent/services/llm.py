"""LlamaIndex LLM initialization helper."""

from typing import TYPE_CHECKING, Optional, Union

from llama_index.core import Settings

from blog_agent.config import config
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)

# Try to import LLM classes - they may be in separate packages
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI


def get_llm(temperature: Optional[float] = None) -> Union["Ollama", "OpenAI"]:
    """
    Get LlamaIndex LLM instance configured from environment.
    
    Supports both Ollama (default) and OpenAI providers.
    
    Args:
        temperature: Optional temperature override. If None, uses config.LLM_TEMPERATURE.
    
    Returns:
        Configured LLM instance (Ollama or OpenAI)
    """
    # Use provided temperature or fall back to default
    temp = temperature if temperature is not None else config.LLM_TEMPERATURE
    
    if config.LLM_PROVIDER.lower() == "ollama":
        llm = Ollama(
            model=config.LLM_MODEL,
            temperature=temp,
            base_url=config.OLLAMA_BASE_URL,
            request_timeout=120.0,  # Ollama can be slower, increase timeout
            context_window=81920,
        )
        logger.debug("Initialized LlamaIndex Ollama LLM", model=config.LLM_MODEL, temperature=temp, base_url=config.OLLAMA_BASE_URL)
    elif config.LLM_PROVIDER.lower() == "openai":
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER is 'openai'")
        llm = OpenAI(
            api_key=config.OPENAI_API_KEY,
            model=config.LLM_MODEL,
            temperature=temp,
        )
        logger.debug("Initialized LlamaIndex OpenAI LLM", model=config.LLM_MODEL, temperature=temp)
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {config.LLM_PROVIDER}. Must be 'ollama' or 'openai'")
    
    # Set as default in Settings for LlamaIndex workflows
    Settings.llm = llm
    
    return llm

