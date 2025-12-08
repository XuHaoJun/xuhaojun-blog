"""LlamaIndex LLM initialization helper."""

from typing import TYPE_CHECKING, Union

from llama_index.core import Settings

from blog_agent.config import config
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)

# Try to import LLM classes - they may be in separate packages
if TYPE_CHECKING:
    from llama_index.llms.ollama import Ollama
    from llama_index.llms.openai import OpenAI
else:
    try:
        from llama_index.llms.ollama import Ollama
    except ImportError:
        try:
            # Fallback: try alternative import path
            from llama_index_llms_ollama import Ollama
        except ImportError:
            Ollama = None

    try:
        from llama_index.llms.openai import OpenAI
    except ImportError:
        try:
            # Fallback: try alternative import path
            from llama_index_llms_openai import OpenAI
        except ImportError:
            OpenAI = None


def get_llm() -> Union["Ollama", "OpenAI"]:
    """
    Get LlamaIndex LLM instance configured from environment.
    
    Supports both Ollama (default) and OpenAI providers.
    
    Returns:
        Configured LLM instance (Ollama or OpenAI)
    """
    if config.LLM_PROVIDER.lower() == "ollama":
        if Ollama is None:
            raise ImportError(
                "Ollama LLM not available. Install with: pip install llama-index-llms-ollama"
            )
        llm = Ollama(
            model=config.LLM_MODEL,
            temperature=config.LLM_TEMPERATURE,
            base_url=config.OLLAMA_BASE_URL,
            request_timeout=120.0,  # Ollama can be slower, increase timeout
        )
        logger.debug("Initialized LlamaIndex Ollama LLM", model=config.LLM_MODEL, base_url=config.OLLAMA_BASE_URL)
    elif config.LLM_PROVIDER.lower() == "openai":
        if OpenAI is None:
            raise ImportError(
                "OpenAI LLM not available. Install with: pip install llama-index-llms-openai"
            )
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

