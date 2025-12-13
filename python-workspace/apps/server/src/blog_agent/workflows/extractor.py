"""Content extraction workflow step.

Aligned with Anthropic's Soul Overview principles:
- Focuses on underlying goals, not just surface content
- Uses semantic understanding instead of hard-coded rules
- Provides structured, precise output
- Considers contextual value and user wellbeing
"""

from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

from llama_index.core import PromptTemplate
from llama_index.core.workflow import Event, step
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI

from blog_agent.services.llm import get_llm
from blog_agent.storage.models import ContentExtract, Message
from blog_agent.utils.logging import get_logger
from blog_agent.workflows.schemas import ConversationAnalysis
from blog_agent.workflows.memory_manager import ConversationMemoryManager

if TYPE_CHECKING:
    from blog_agent.workflows.memory_manager import ConversationMemoryManager

logger = get_logger(__name__)


class ExtractEvent(Event):
    """Event containing extracted content."""

    content_extract: ContentExtract
    conversation_log_id: str  # UUID as string for workflow
    conversation_log_metadata: Optional[Dict[str, Any]] = None  # Metadata from conversation log (timestamps, participants, etc.) (FR-015)
    quality_warning: str = ""  # Optional warning for low-quality content
    memory: Optional[ConversationMemoryManager] = None  # Optional memory manager for conversation history


class ExtractStartEvent(Event):
    """Start event for extraction step."""

    messages: List[Message]
    conversation_log_id: str  # UUID as string
    conversation_log_metadata: Optional[Dict[str, Any]] = None  # Metadata from conversation log (timestamps, participants, etc.) (FR-015)
    memory: Optional[ConversationMemoryManager] = None  # Optional memory manager for conversation history


# Rebuild models to resolve forward references
ExtractEvent.model_rebuild()
ExtractStartEvent.model_rebuild()


class ContentExtractor:
    """Content extraction step for blog workflow."""

    def __init__(self, llm: Optional[Union[Ollama, OpenAI]] = None):
        """Initialize content extractor."""
        self.llm = llm or get_llm()

    async def extract(self, ev: ExtractStartEvent) -> ExtractEvent:
        """Extract key insights and core concepts from conversation.
        
        Uses structured output aligned with Soul Overview principles:
        - Semantic understanding instead of hard rules
        - Focus on underlying goals and contextual value
        - Precise, structured extraction
        """
        try:
            messages = ev.messages
            conversation_log_id = ev.conversation_log_id
            
            # Get or create memory manager
            memory = ev.memory
            if memory is None:
                memory = ConversationMemoryManager.from_messages(messages)

            # Filter out noise (greetings, small talk) - keep simple heuristic for efficiency
            filtered_messages = self._filter_noise(messages)

            # Check if content is substantive using LLM semantic judgment (Soul Overview aligned)
            has_substantive = await self._has_substantive_content(filtered_messages)
            
            if not has_substantive:
                logger.warning("Conversation has minimal substantive content")
                # Still generate but mark as low-quality
                # Get or create memory manager for error case too
                memory = ev.memory
                if memory is None:
                    memory = ConversationMemoryManager.from_messages(messages)
                
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
                    memory=memory,
                )

            # Use structured extraction to get insights, concepts, and user intent in one call
            analysis = await self._extract_structured_analysis(filtered_messages)

            # Combine filtered content
            filtered_content = self._combine_content(filtered_messages)

            # Determine quality warning based on substantive score
            quality_warning = ""
            if analysis.substantive_score < 3:
                quality_warning = f"Low substantive value detected (score: {analysis.substantive_score}/10)"

            content_extract = ContentExtract(
                conversation_log_id=conversation_log_id,
                key_insights=analysis.key_insights[:5],  # Limit to 5
                core_concepts=analysis.core_concepts[:10],  # Limit to 10
                filtered_content=filtered_content,
            )

            return ExtractEvent(
                content_extract=content_extract,
                conversation_log_id=conversation_log_id,
                conversation_log_metadata=ev.conversation_log_metadata or {},
                quality_warning=quality_warning,
                memory=memory,
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

    async def _has_substantive_content(self, messages: List[Message]) -> bool:
        """Check if conversation has substantive content using LLM semantic judgment.
        
        Aligned with Soul Overview: focuses on value exchange rather than surface patterns.
        Even short conversations can be substantive if they solve specific user problems.
        """
        if not messages:
            return False
        
        # Quick heuristic check first for efficiency
        total_length = sum(len(msg.content) for msg in messages)
        if total_length < 50:  # Very short, likely not substantive
            return False

        # Use LLM for semantic judgment (Soul Overview aligned)
        # Preview first few messages to avoid token waste
        preview_messages = messages[:6]
        conversation_text = "\n".join([f"{m.role}: {m.content}" for m in preview_messages])
        
        template_str = """你是一位資深的主編。請判斷以下對話是否包含「實質性內容」(Substantive Content)。

判斷標準（基於 Anthropic 的 "Helpfulness" 原則）：
1. 是否包含具體的問題解決、知識交換或創意發想？
2. 是否超越了單純的寒暄 (Small talk) 或無意義的噪音？
3. 即使對話簡短，如果解決了使用者的特定疑惑，也算有實質內容。
4. 是否有價值交換發生，而不僅僅是表面的互動？

對話預覽：
{conversation_text}

請只回答 "YES" 或 "NO"，不要有其他說明。"""

        try:
            prompt_tmpl = PromptTemplate(template_str)
            response = await self.llm.acomplete(prompt_tmpl.format(conversation_text=conversation_text))
            result = response.text.strip().upper()
            return "YES" in result or result == "YES"
        except Exception as e:
            logger.warning("Failed to use LLM for substantive check, falling back to heuristic", error=str(e))
            # Fallback to simple heuristic
            return total_length >= 200 and len(messages) >= 2

    async def _extract_structured_analysis(self, messages: List[Message]) -> ConversationAnalysis:
        """Extract structured analysis using LLM with Pydantic output.
        
        Aligned with Soul Overview principles:
        - Focuses on underlying goals, not just surface content
        - Provides contextual value assessment
        - Ensures structured, precise output
        """
        conversation_text = "\n\n".join(
            f"{msg.role}: {msg.content}" for msg in messages
        )

        template_str = """請以一位具備深度洞察力的專家身份分析此對話。不要只總結表面文字，請挖掘以下層面：

1. **使用者潛在目標 (Underlying Goals)**：使用者表面問了什麼，但他真正想解決的深層問題是什麼？
2. **核心洞察 (Key Insights)**：對話中產生了哪些具體的、可行動的、或新穎的觀點？這些洞察應該專注於解決問題的本質。
3. **核心概念 (Core Concepts)**：對話中涉及的技術術語或關鍵主題。
4. **脈絡價值 (Contextual Value)**：這段對話對使用者的長期福祉或知識體系有何幫助？請給出 1-10 的評分。

重要原則：
- 如果對話涉及敏感、危險或不道德的主題，請不要提取具體的執行步驟，而是提取關於安全原則或道德考量的洞察。
- 確保洞察具體且不空泛，避免泛泛而談。
- 專注於對話中產生的獨特價值，而不僅僅是重複已知信息。

對話內容：
{conversation_text}

請依據上述對話，填寫分析報告。"""

        try:
            prompt_tmpl = PromptTemplate(template_str)
            
            # Try structured output first
            if hasattr(self.llm, 'astructured_predict'):
                try:
                    analysis = await self.llm.astructured_predict(
                        ConversationAnalysis,
                        prompt_tmpl,
                        conversation_text=conversation_text,
                    )
                    logger.info("Extracted structured analysis", 
                               insights_count=len(analysis.key_insights),
                               concepts_count=len(analysis.core_concepts),
                               substantive_score=analysis.substantive_score)
                    return analysis
                except Exception as structured_error:
                    logger.warning("astructured_predict failed, using fallback", error=str(structured_error))
                    return await self._extract_analysis_fallback(messages, conversation_text)
            else:
                # Fallback to text completion with parsing
                logger.warning("LLM does not support structured_predict, using fallback")
                return await self._extract_analysis_fallback(messages, conversation_text)
        except Exception as e:
            logger.warning("Structured extraction failed, using fallback", error=str(e))
            return await self._extract_analysis_fallback(messages, conversation_text)

    async def _extract_analysis_fallback(self, messages: List[Message], conversation_text: str) -> ConversationAnalysis:
        """Fallback method when structured output is not available."""
        # Use separate extraction methods as fallback
        key_insights = await self._extract_insights(messages)
        core_concepts = await self._extract_concepts(messages)
        
        # Simple heuristic for substantive score
        total_length = sum(len(msg.content) for msg in messages)
        substantive_score = min(10, max(1, total_length // 200))
        
        return ConversationAnalysis(
            key_insights=key_insights,
            core_concepts=core_concepts,
            user_intent="",  # Cannot extract without structured output
            substantive_score=substantive_score,
        )

    async def _extract_insights(self, messages: List[Message]) -> List[str]:
        """Extract key insights using LLM (fallback method)."""
        conversation_text = "\n\n".join(
            f"{msg.role}: {msg.content}" for msg in messages
        )

        prompt = f"""請以一位具備深度洞察力的專家身份分析此對話。不要只總結表面文字，請挖掘以下層面：

1. **使用者潛在目標 (Underlying Goals)**：使用者表面問了什麼，但他真正想解決的深層問題是什麼？
2. **核心洞察 (Key Insights)**：對話中產生了哪些具體的、可行動的、或新穎的觀點？
3. **脈絡價值 (Contextual Value)**：這段對話對使用者的長期福祉或知識體系有何幫助？

對話內容：
{conversation_text}

請輸出 3-5 條深刻的洞察（Insight），確保內容具體且不空泛。請用繁體中文條列式輸出，每個洞察一行，不需標題。

如果對話涉及敏感、危險或不道德的主題，請不要提取具體的執行步驟，而是提取關於安全原則或道德考量的洞察。"""

        response = await self.llm.acomplete(prompt)

        # Parse response into list
        insights = [
            line.strip()
            for line in response.text.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]

        return insights[:5]  # Limit to 5

    async def _extract_concepts(self, messages: List[Message]) -> List[str]:
        """Extract core concepts using LLM (fallback method)."""
        conversation_text = "\n\n".join(
            f"{msg.role}: {msg.content}" for msg in messages
        )

        prompt = f"""請從以下對話中提取核心概念（Core Concepts），這些是對話中討論的主要技術或主題。

對話內容：
{conversation_text}

請以簡潔的列表形式輸出核心概念，每個概念一行。只輸出概念名稱，不要額外說明。"""

        response = await self.llm.acomplete(prompt)

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

