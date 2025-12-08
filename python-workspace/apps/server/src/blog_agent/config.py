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
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen3:14b")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Tavily API
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if cls.LLM_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER is 'openai'")
        if not cls.TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY is required")


config = Config()

