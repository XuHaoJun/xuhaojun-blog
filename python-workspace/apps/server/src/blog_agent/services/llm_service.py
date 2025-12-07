"""LLM service abstraction."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from blog_agent.config import config
from blog_agent.utils.errors import ExternalServiceError
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


class LLMService(ABC):
    """Abstract LLM service interface."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate text from prompt."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate structured output matching schema."""
        pass


class OpenAILLMService(LLMService):
    """OpenAI LLM service implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        temperature: float = 0.7,
    ):
        self.api_key = api_key or config.OPENAI_API_KEY
        self.model = model or config.LLM_MODEL
        self.temperature = temperature or config.LLM_TEMPERATURE

        if not self.api_key:
            raise ValueError("OpenAI API key is required")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate text using OpenAI API."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error("OpenAI API call failed", error=str(e), exc_info=True)
            raise ExternalServiceError(
                service_name="OpenAI",
                message=str(e),
                details={"model": self.model, "prompt_length": len(prompt)},
            ) from e

    async def generate_structured(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate structured output using OpenAI function calling."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )

            import json

            content = response.choices[0].message.content or "{}"
            return json.loads(content)

        except Exception as e:
            logger.error("OpenAI structured generation failed", error=str(e), exc_info=True)
            raise ExternalServiceError(
                service_name="OpenAI",
                message=str(e),
                details={"model": self.model, "prompt_length": len(prompt)},
            ) from e


def get_llm_service() -> LLMService:
    """Get LLM service instance."""
    return OpenAILLMService()

