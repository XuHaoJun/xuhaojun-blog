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

from blog_agent.config import config
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
        self.llm = llm or get_llm(temperature=config.LLM_TEMPERATURE_ANALYSIS)

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
                memory = await ConversationMemoryManager.from_messages(messages)

            # Filter out noise (greetings, small talk) - keep simple heuristic for efficiency
            filtered_messages = self._filter_noise(messages)

            # Check if content is substantive using LLM semantic judgment (Soul Overview aligned)
            # has_substantive = await self._has_substantive_content(filtered_messages)
            
            # if not has_substantive:
            #     logger.warning("Conversation has minimal substantive content")
            #     # Still generate but mark as low-quality
            #     # Get or create memory manager for error case too
            #     memory = ev.memory
            #     if memory is None:
            #         memory = ConversationMemoryManager.from_messages(messages)
                
            #     return ExtractEvent(
            #         content_extract=ContentExtract(
            #             conversation_log_id=conversation_log_id,
            #             key_insights=[],
            #             core_concepts=[],
            #             filtered_content="",
            #         ),
            #         conversation_log_id=conversation_log_id,
            #         conversation_log_metadata=ev.conversation_log_metadata or {},
            #         quality_warning="Low quality: minimal substantive content",
            #         memory=memory,
            #     )

            # Use structured extraction to get insights, concepts, and user intent in one call
            # Create memory manager for filtered messages to get summarized context
            filtered_memory = await ConversationMemoryManager.from_messages(filtered_messages)
            analysis = await self._extract_structured_analysis(filtered_messages, filtered_memory)

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

    async def _extract_structured_analysis(
        self, 
        messages: List[Message],
        memory: ConversationMemoryManager
    ) -> ConversationAnalysis:
        """Extract structured analysis using LLM with Pydantic output.
        
        Aligned with Soul Overview principles:
        - Focuses on underlying goals, not just surface content
        - Provides contextual value assessment
        - Ensures structured, precise output
        
        Uses ChatSummaryMemoryBuffer to get summarized context for better token efficiency.
        """
        # Use memory manager to get context text (facts + recent turns) instead of raw message concatenation
        conversation_text = await memory.get_context_text()

        template_str = """請以一位具備深度洞察力的專家身份分析此對話。請仔細閱讀對話內容，並填寫以下所有欄位：

## 對話內容：
{conversation_text}

## 分析要求：

### 1. key_insights（核心洞察）
請提取 3-5 個對話中的核心洞察，這些洞察應該：
- 專注於解決問題的本質和使用者的潛在目標
- 具體且可行動，避免空泛的陳述
- 反映對話中產生的獨特價值或新穎觀點
- 每個洞察應該是一個完整的句子，說明具體的發現或建議

**重要**：必須至少提取 3 個洞察，如果對話內容不足，請基於現有內容進行合理推斷。

### 2. core_concepts（核心概念）
請提取對話中涉及的技術術語或關鍵主題，最多 10 個：
- 可以是技術名詞、工具名稱、方法論、概念等
- 每個概念應該是一個簡潔的詞彙或短語
- 按照在對話中的重要性和出現頻率排序

**重要**：必須至少提取 3 個核心概念，如果對話內容不足，請基於現有內容進行合理推斷。

### 3. user_intent（使用者潛在目標）
請分析使用者表面問了什麼，但他真正想解決的深層問題是什麼：
- 不要只重複表面的問題
- 要挖掘使用者背後的真實需求或目標
- 應該是一個完整的句子，說明使用者的深層意圖

**重要**：必須提供一個具體的使用者意圖描述，不能為空。

### 4. substantive_score（實質價值評分）
請評估這段對話的實質價值，給出 1-10 的評分：
- 評分標準：是否包含具體的問題解決、知識交換或創意發想
- 1-3 分：幾乎沒有實質內容，主要是寒暄或無意義的對話
- 4-6 分：有一些實質內容，但較為淺層或零散
- 7-8 分：有明確的實質內容，包含具體的問題解決或知識交換
- 9-10 分：非常有價值的對話，包含深度洞察、創新想法或完整的問題解決方案

**重要**：必須給出一個 1-10 之間的整數評分，不能使用預設值。

## 重要提醒：
- 所有欄位都必須填寫，不能為空或使用預設值
- 如果對話內容較少，請基於現有內容進行合理的分析和推斷
- 專注於對話中產生的獨特價值，而不僅僅是重複已知信息
- 確保輸出具體且有意義，避免泛泛而談

請開始分析並填寫所有欄位。"""

        prompt_tmpl = PromptTemplate(template_str)
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

    def _combine_content(self, messages: List[Message]) -> str:
        """Combine filtered messages into content string."""
        return "\n\n".join(f"{msg.role}: {msg.content}" for msg in messages)

