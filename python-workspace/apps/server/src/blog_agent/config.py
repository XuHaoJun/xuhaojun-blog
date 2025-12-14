"""Environment configuration management."""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:test@localhost:5432/blog_agent",
    )

    # gRPC Server
    GRPC_PORT: int = int(os.getenv("GRPC_PORT", "50051"))
    GRPC_HOST: str = os.getenv("GRPC_HOST", "0.0.0.0")

    # LLM Service
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")  # "ollama" or "openai"
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen3:8b")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))  # Default/fallback temperature
    
    # LLM Temperature Settings (per task type)
    # Analysis tasks: extraction, review - need precision and consistency
    LLM_TEMPERATURE_ANALYSIS: float = float(os.getenv("LLM_TEMPERATURE_ANALYSIS", "0.1"))
    LLM_TEMPERATURE_REVIEW: float = float(os.getenv("LLM_TEMPERATURE_REVIEW", "0.1"))
    
    # Gap identification: needs precision but slightly more flexibility than pure analysis
    LLM_TEMPERATURE_GAP_IDENTIFICATION: float = float(os.getenv("LLM_TEMPERATURE_GAP_IDENTIFICATION", "0.2"))
    
    # Research integration: needs natural language flow
    LLM_TEMPERATURE_RESEARCH_INTEGRATION: float = float(os.getenv("LLM_TEMPERATURE_RESEARCH_INTEGRATION", "0.4"))
    
    # Writing tasks: blog content generation - needs creativity and narrative flow
    LLM_TEMPERATURE_WRITING: float = float(os.getenv("LLM_TEMPERATURE_WRITING", "0.5"))
    
    # Creative tasks: titles, summaries, prompt candidates - needs more creativity
    LLM_TEMPERATURE_CREATIVE: float = float(os.getenv("LLM_TEMPERATURE_CREATIVE", "0.6"))
    
    # Safety checks: must be deterministic and precise
    LLM_TEMPERATURE_SAFETY: float = float(os.getenv("LLM_TEMPERATURE_SAFETY", "0.0"))
    
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Embedding Service
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "ollama")  # "ollama" or "openai"
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b")

    # Tavily API
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")

    # Fact-checking method
    FACT_CHECK_METHOD: str = os.getenv("FACT_CHECK_METHOD", "LLM").upper()  # "LLM" or "TAVILY"

    # Memory Management
    MEMORY_TOKEN_LIMIT: int = int(os.getenv("MEMORY_TOKEN_LIMIT", "30000"))
    MEMORY_SUMMARIZER_MODEL: str = os.getenv("MEMORY_SUMMARIZER_MODEL", "qwen3:8b")
    MEMORY_SUMMARIZER_PROVIDER: str = os.getenv("MEMORY_SUMMARIZER_PROVIDER", "ollama")  # Empty means use LLM_PROVIDER

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if cls.LLM_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER is 'openai'")
        if cls.FACT_CHECK_METHOD == "TAVILY" and not cls.TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY is required when FACT_CHECK_METHOD is 'TAVILY'")


config = Config()

