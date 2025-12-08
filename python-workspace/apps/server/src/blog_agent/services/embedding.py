"""LlamaIndex embedding initialization helper."""

from typing import List, Optional, Union

from llama_index.core import Settings

from blog_agent.config import config
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)

# Cache for embedding model instance
_embed_model_cache: Optional[Union["OllamaEmbedding", "OpenAIEmbedding"]] = None

# Try to import embedding classes - they may be in separate packages
try:
    from llama_index.embeddings.ollama import OllamaEmbedding
except ImportError:
    try:
        # Fallback: try alternative import path
        from llama_index_embeddings_ollama import OllamaEmbedding
    except ImportError:
        OllamaEmbedding = None

try:
    from llama_index.embeddings.openai import OpenAIEmbedding
except ImportError:
    try:
        # Fallback: try alternative import path
        from llama_index_embeddings_openai import OpenAIEmbedding
    except ImportError:
        OpenAIEmbedding = None


def get_embed_model() -> Union["OllamaEmbedding", "OpenAIEmbedding"]:
    """
    Get LlamaIndex embedding model instance configured from environment.
    
    Supports both Ollama (default) and OpenAI providers.
    Uses caching to avoid recreating the model instance.
    
    Returns:
        Configured embedding model instance (OllamaEmbedding or OpenAIEmbedding)
    """
    global _embed_model_cache
    
    if _embed_model_cache is not None:
        return _embed_model_cache
    
    if config.EMBEDDING_PROVIDER.lower() == "ollama":
        if OllamaEmbedding is None:
            raise ImportError(
                "OllamaEmbedding not available. Install with: pip install llama-index-embeddings-ollama"
            )
        embed_model = OllamaEmbedding(
            model_name=config.EMBEDDING_MODEL,
            base_url=config.OLLAMA_BASE_URL,
        )
        logger.debug(
            "Initialized LlamaIndex Ollama Embedding",
            model=config.EMBEDDING_MODEL,
            base_url=config.OLLAMA_BASE_URL,
        )
    elif config.EMBEDDING_PROVIDER.lower() == "openai":
        if OpenAIEmbedding is None:
            raise ImportError(
                "OpenAIEmbedding not available. Install with: pip install llama-index-embeddings-openai"
            )
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER is 'openai'")
        embed_model = OpenAIEmbedding(
            api_key=config.OPENAI_API_KEY,
            model=config.EMBEDDING_MODEL,
        )
        logger.debug("Initialized LlamaIndex OpenAI Embedding", model=config.EMBEDDING_MODEL)
    else:
        raise ValueError(
            f"Unsupported EMBEDDING_PROVIDER: {config.EMBEDDING_PROVIDER}. Must be 'ollama' or 'openai'"
        )

    # Set as default in Settings for LlamaIndex workflows
    Settings.embed_model = embed_model
    
    # Cache the model instance
    _embed_model_cache = embed_model

    return embed_model


async def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for given text.
    
    Args:
        text: Text to generate embedding for
        
    Returns:
        List of floats representing the embedding vector
    """
    embed_model = get_embed_model()
    embedding = await embed_model.aget_text_embedding(text)
    return embedding

