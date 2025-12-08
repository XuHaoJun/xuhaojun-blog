"""Content extraction workflow step."""

from typing import Any, Dict, List, Optional, Union

from llama_index.core.workflow import Event, step
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI

from blog_agent.services.llm import get_llm
from blog_agent.storage.models import ContentExtract, Message
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


class ExtractEvent(Event):
    """Event containing extracted content."""

    content_extract: ContentExtract
    conversation_log_id: str  # UUID as string for workflow
    conversation_log_metadata: Optional[Dict[str, Any]] = None  # Metadata from conversation log (timestamps, participants, etc.) (FR-015)
    quality_warning: str = ""  # Optional warning for low-quality content


class ExtractStartEvent(Event):
    """Start event for extraction step."""

    messages: List[Message]
    conversation_log_id: str  # UUID as string
    conversation_log_metadata: Optional[Dict[str, Any]] = None  # Metadata from conversation log (timestamps, participants, etc.) (FR-015)


class ContentExtractor:
    """Content extraction step for blog workflow."""

    def __init__(self, llm: Optional[Union[Ollama, OpenAI]] = None):
        """Initialize content extractor."""
        self.llm = llm or get_llm()

    async def extract(self, ev: ExtractStartEvent) -> ExtractEvent:
        """Extract key insights and core concepts from conversation."""
        try:
            messages = ev.messages
            conversation_log_id = ev.conversation_log_id

            # Filter out noise (greetings, small talk)
            filtered_messages = self._filter_noise(messages)

            # Check if content is substantive (FR-025)
            if not self._has_substantive_content(filtered_messages):
                logger.warning("Conversation has minimal substantive content")
                # Still generate but mark as low-quality
                return ExtractEvent(
                    content_extract=ContentExtract(
                        conversation_log_id=conversation_log_id,
                        key_insights=[],
                        core_concepts=[],
                        filtered_content="",
                    ),
                    conversation_log_id=conversation_log_id,
                    conversation_log_metadata=ev.conversation_log_metadata or {},
                    quality_warning="Low quality: minimal substantive content",
                )

            # Extract key insights using LLM
            key_insights = await self._extract_insights(filtered_messages)

            # Extract core concepts
            core_concepts = await self._extract_concepts(filtered_messages)

            # Combine filtered content
            filtered_content = self._combine_content(filtered_messages)

            content_extract = ContentExtract(
                conversation_log_id=conversation_log_id,
                key_insights=key_insights,
                core_concepts=core_concepts,
                filtered_content=filtered_content,
            )

            return ExtractEvent(
                content_extract=content_extract,
                conversation_log_id=conversation_log_id,
                conversation_log_metadata=ev.conversation_log_metadata or {},
            )

        except Exception as e:
            logger.error("Content extraction failed", error=str(e), exc_info=True)
            raise

    def _filter_noise(self, messages: List[Message]) -> List[Message]:
        """Filter out greetings and irrelevant exchanges."""
        filtered = []

        # Simple heuristics to filter noise
        noise_patterns = [
            "你好",
            "謝謝",
            "再見",
            "hello",
            "thanks",
            "goodbye",
            "hi",
            "bye",
        ]

        for msg in messages:
            content_lower = msg.content.lower().strip()

            # Skip very short messages (likely greetings)
            if len(content_lower) < 10:
                continue

            # Skip if only contains noise patterns
            if any(pattern in content_lower for pattern in noise_patterns) and len(
                content_lower
            ) < 30:
                continue

            filtered.append(msg)

        return filtered

    def _has_substantive_content(self, messages: List[Message]) -> bool:
        """Check if conversation has substantive content (FR-025)."""
        if len(messages) < 2:
            return False

        # Check if there's meaningful exchange
        total_length = sum(len(msg.content) for msg in messages)
        if total_length < 200:  # Very short conversation
            return False

        # Check for question-answer pattern
        has_question = any(
            "?" in msg.content or "？" in msg.content or "什麼" in msg.content
            for msg in messages
        )
        has_answer = any(
            len(msg.content) > 100 for msg in messages if msg.role == "assistant"
        )

        return has_question and has_answer

    async def _extract_insights(self, messages: List[Message]) -> List[str]:
        """Extract key insights using LLM."""
        # Combine messages into text
        conversation_text = "\n\n".join(
            f"{msg.role}: {msg.content}" for msg in messages
        )

        prompt = f"""請分析以下對話，提取 3-5 個最具啟發性的核心觀點（Key Insights）。

對話內容：
{conversation_text}

請以簡潔的列表形式輸出，每個觀點一行。只輸出觀點，不要額外說明。"""

        response = await self.llm.complete(prompt)

        # Parse response into list
        insights = [
            line.strip()
            for line in response.text.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]

        return insights[:5]  # Limit to 5

    async def _extract_concepts(self, messages: List[Message]) -> List[str]:
        """Extract core concepts using LLM."""
        conversation_text = "\n\n".join(
            f"{msg.role}: {msg.content}" for msg in messages
        )

        prompt = f"""請從以下對話中提取核心概念（Core Concepts），這些是對話中討論的主要技術或主題。

對話內容：
{conversation_text}

請以簡潔的列表形式輸出核心概念，每個概念一行。只輸出概念名稱，不要額外說明。"""

        response = await self.llm.complete(prompt)

        # Parse response into list
        concepts = [
            line.strip()
            for line in response.text.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]

        return concepts[:10]  # Limit to 10

    def _combine_content(self, messages: List[Message]) -> str:
        """Combine filtered messages into content string."""
        return "\n\n".join(f"{msg.role}: {msg.content}" for msg in messages)

