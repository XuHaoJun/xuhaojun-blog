"""Conversation memory management using LlamaIndex Memory + fact extraction."""

from typing import List, Optional

from llama_index.core.llms import ChatMessage, TextBlock
from llama_index.core.memory import FactExtractionMemoryBlock, Memory
from llama_index.core.prompts.rich import RichPromptTemplate

from blog_agent.config import config
from blog_agent.services.llm import get_llm
from blog_agent.storage.models import Message
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


class RobustFactExtractionMemoryBlock(FactExtractionMemoryBlock):
    """
    增強版事實抽取區塊。
    顯式將對話歷史注入到 Prompt 中，解決 LLM 有時無法讀取 system prompt 之前的對話歷史的問題。
    """
    async def _aput(self, messages: List[ChatMessage]) -> None:
        """Extract facts from new messages and add them to the facts list."""
        if not messages:
            return

        existing_facts_text = ""
        if self.facts:
            existing_facts_text = "\n".join(
                [f"<fact>{fact}</fact>" for fact in self.facts]
            )

        # 1. 顯式序列化對話歷史
        conversation_text = ""
        for msg in messages:
            role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            content = msg.content or ""
            conversation_text += f"[{role}]: {content}\n\n"

        # 2. 將對話歷史與現有事實傳入 Prompt (需配合 Prompt Template 中的 {{ conversation }})
        prompt_messages = self.fact_extraction_prompt_template.format_messages(
            existing_facts=existing_facts_text,
            conversation=conversation_text
        )

        # 3. 呼叫 LLM
        # 注意：我們這裡只傳入 prompt_messages，因為對話歷史已經包含在 Prompt 裡面了。
        # 這樣可以避免 token 重複，也能讓 LLM 更專注於指令。
        response = await self.llm.achat(messages=prompt_messages)

        # 4. 解析與儲存 (沿用父類別邏輯)
        facts_text = response.message.content or ""
        new_facts = self._parse_facts_xml(facts_text)

        for fact in new_facts:
            if fact not in self.facts:
                self.facts.append(fact)

        # 5. 濃縮事實 (若超過上限)
        if len(self.facts) > self.max_facts:
            existing_facts_text = "\n".join(
                [f"<fact>{fact}</fact>" for fact in self.facts]
            )
            # 濃縮時只需要事實清單，不需要對話歷史
            prompt_messages = self.fact_condense_prompt_template.format_messages(
                existing_facts=existing_facts_text,
                max_facts=self.max_facts,
            )
            response = await self.llm.achat(messages=prompt_messages)
            new_facts = self._parse_facts_xml(response.message.content or "")
            self.facts = new_facts


class ConversationMemoryManager:
    """Manages conversation memory using LlamaIndex Memory + FactExtractionMemoryBlock."""
    
    def __init__(self, memory: Optional[Memory] = None, session_id: Optional[str] = None):
        """
        Initialize memory manager.
        
        Args:
            memory: Optional existing LlamaIndex Memory instance.
                   If None, creates a new one with default settings.
            session_id: Optional session id for LlamaIndex Memory persistence.
        """
        if memory is not None:
            self.memory = memory
            self._fact_block: Optional[FactExtractionMemoryBlock] = None
            return

        llm = get_llm(temperature=0.1)

        fact_extraction_prompt = RichPromptTemplate(
            """你是一個精準的「事實抽取」系統，負責從對話中擷取關鍵資訊。

指示：
1. 請閱讀以下 <conversation> 標籤中的對話內容：
<conversation>
{{ conversation }}
</conversation>

2. 抽取以下類型的資訊：
   - 使用者的偏好、需求、限制（例如：「我想做...」、「我希望...」、「只能用...」）
   - 對話中討論的主題與要點（例如：「討論系統架構設計」、「探討 API 整合方式」）
   - 任務的具體要求（例如：文章主題、風格、長度）
   - 重要的上下文背景（包含 AI 建議的技術架構、步驟流程、關鍵工具名稱）
3. 請注意：
   - 使用者的意圖、計畫或詢問的問題本身，都屬於應該提取的「需求」與「上下文」事實。
   - 請保留具體的技術名詞（如 Python, React, PostgreSQL），不要過度概括。
4. 不要加入推測或詮釋，只提取明確提到的內容
5. 不要重複已存在於 existing_facts 的事實
6. 每個事實用一個 <fact> XML 標籤呈現
7. 請使用「正體中文」輸出
8. 除了硬性事實，請同時提取對話中提到的核心邏輯與關鍵推理過程。

<existing_facts>
{{ existing_facts }}
</existing_facts>

請回傳詳細的事實清單，格式範例如下：
<facts>
  <fact>具體事實 fact 1</fact>
  <fact>具體事實 fact 2</fact>
</facts>

請盡量完整提取對話中的關鍵資訊，不要遺漏技術細節。
"""
        )

        fact_condense_prompt = RichPromptTemplate(
            """你是一個精準的「事實濃縮」系統，負責把現有事實整理成更精簡的清單。

指示：
1. 請閱讀現有事實清單 existing_facts
2. 請將事實濃縮為少於 {{ max_facts }} 條
3. 保留以下類型的資訊：
   - 使用者的偏好、需求、限制
   - 對話中討論的主題與要點
   - 任務的具體要求（例如：文章主題、風格、長度）
   - 重要的上下文背景
4. 合併語意相近或重複的事實
5. 每個事實用一個 <fact> XML 標籤呈現
6. 請使用「正體中文」輸出

<existing_facts>
{{ existing_facts }}
</existing_facts>

請只回傳以下格式：
<facts>
  <fact>具體事實 1</fact>
  <fact>具體事實 2</fact>
</facts>
"""
        )

        fact_block = RobustFactExtractionMemoryBlock(
            name="extracted_info",
            llm=llm,
            max_facts=config.MEMORY_MAX_FACTS,
            priority=1,
            fact_extraction_prompt_template=fact_extraction_prompt,
            fact_condense_prompt_template=fact_condense_prompt,
        )
        self._fact_block = fact_block

        self.memory = Memory.from_defaults(
            session_id=session_id or "blog_agent",
            token_limit=config.MEMORY_TOKEN_LIMIT,
            chat_history_token_ratio=0.8,
            token_flush_size=config.MEMORY_TOKEN_LIMIT // 10,
            memory_blocks=[fact_block],
            insert_method="system",
            async_database_uri="sqlite+aiosqlite:///:memory:",
            )
        logger.debug(
        "Created new LlamaIndex Memory",
            token_limit=config.MEMORY_TOKEN_LIMIT,
            max_facts=config.MEMORY_MAX_FACTS,
        )
    
    @classmethod
    async def from_messages(cls, messages: List[Message]) -> "ConversationMemoryManager":
        """
        Create memory manager from Message list.
        
        Args:
            messages: List of Message objects to initialize memory with
            
        Returns:
            ConversationMemoryManager instance with messages loaded
        """
        manager = cls()

        # Important: LlamaIndex SQL chat store currently errors on empty inserts for Memory.aput_messages.
        # The first user prompt may have an empty historical context (messages[:0] == []).
        if not messages:
            logger.debug("Initialized memory from messages (empty history)")
            return manager
        
        chat_messages = [ChatMessage(role=msg.role, content=msg.content) for msg in messages]
        await manager.memory.aput_messages(chat_messages)

        # Proactively extract facts even if the memory queue doesn't exceed the flush threshold yet.
        # (Memory only waterfalls messages to memory blocks when the short-term token budget is exceeded.)
        try:
            fact_block = manager._fact_block
            if fact_block is None:
                # Fallback: locate a fact extraction block from the underlying memory
                for block in manager.memory.memory_blocks:
                    if isinstance(block, FactExtractionMemoryBlock):
                        fact_block = block
                        break
            if fact_block is not None and chat_messages:
                # Check signature of _aput in our custom class vs standard
                # Our custom RobustFactExtractionMemoryBlock._aput takes 'messages' as argument
                # Standard FactExtractionMemoryBlock._aput also takes 'messages'
                # But here we are calling it manually.
                # Note: memory.aput_messages() calls block.aput() internally when flushing?
                # Actually, memory blocks are usually updated via 'put' or 'aput' on the block itself.
                # LlamaIndex Memory.put calls block.put.
                
                # We call it manually here to ensure facts are extracted from the loaded history
                # immediately, not just when token limit is reached.
                await fact_block._aput(chat_messages)
        except Exception as e:
            # Do not fail workflow if fact extraction fails (e.g., LLM temporarily unavailable).
            logger.warning("Failed to extract facts from messages", error=str(e))
        
        logger.debug("Initialized memory from messages", message_count=len(messages))
        return manager
    
    async def get_context_text(self) -> str:
        """
        Get conversation context as a string.
        
        Returns:
            String representation of conversation history with extracted facts + recent turns
        """
        history = await self.memory.aget()
        
        # Convert ChatMessage list to formatted string (including any injected memory blocks)
        context_parts = []
        for msg in history:
            role = msg.role
            role_str = role.value if hasattr(role, "value") else str(role)

            content_parts: List[str] = []
            seen: set[str] = set()

            def _add_content(text: str) -> None:
                t = text.strip()
                if t and t not in seen:
                    seen.add(t)
                    content_parts.append(t)

            if msg.content and msg.content.strip():
                _add_content(msg.content)

            blocks = getattr(msg, "blocks", None)
            if blocks:
                for block in blocks:
                    if isinstance(block, TextBlock) and block.text and block.text.strip():
                        _add_content(block.text)

            if not content_parts:
                continue

            context_parts.append(f"{role_str}: " + "\n".join(content_parts))
        
        context = "\n".join(context_parts)
        logger.debug("Retrieved context text from memory", history_length=len(history))
        return context
    
    async def get_all_messages(self) -> List[ChatMessage]:
        """
        Get all messages from memory (including any persisted messages).
        
        Returns:
            List of ChatMessage objects
        """
        return await self.memory.aget_all()

    async def get_extracted_facts(self) -> str:
        """
        Get only the extracted facts from memory as a bulleted list.
        
        Returns:
            String representation of facts
        """
        import re
        history = await self.memory.aget()
        
        # Look for the injected facts in the blocks of the latest message
        for msg in history:
            blocks = getattr(msg, "blocks", None)
            if not blocks:
                continue
                
            for block in blocks:
                # LlamaIndex wraps the content in XML tags
                if hasattr(block, "text") and "<extracted_info>" in block.text:
                    content = block.text
                    logger.debug("Parsing memory block for facts", content_length=len(content))
                    
                    # Extract the part between <extracted_info> tags
                    match = re.search(r"<extracted_info>(.*?)</extracted_info>", content, re.DOTALL)
                    if match:
                        inner_content = match.group(1).strip()
                        
                        # Clean up the <facts> wrapper if the LLM included it
                        inner_content = re.sub(r"</?facts>", "", inner_content).strip()
                        
                        # Extract individual facts between <fact> tags
                        facts = re.findall(r"<fact>(.*?)</fact>", inner_content, re.DOTALL)
                        if facts:
                            result = "\n".join([f"- {f.strip()}" for f in facts if f.strip()])
                            logger.debug("Successfully extracted facts", fact_count=len(facts))
                            return result
                        
                        # Fallback: if there are no <fact> tags but there's content, 
                        # try to return it after stripping other XML-like tags
                        clean_content = re.sub(r"<[^>]+>", "", inner_content).strip()
                        if clean_content:
                            logger.debug("No <fact> tags but found other content", content_preview=clean_content[:50])
                            return clean_content
        
        logger.debug("No facts found in any memory blocks")
        return ""
    
    async def put(self, message: Message) -> None:
        """
        Add a new message to memory.
        
        Args:
            message: Message object to add
        """
        chat_msg = ChatMessage(role=message.role, content=message.content)
        await self.memory.aput(chat_msg)
        logger.debug("Added message to memory", role=message.role)
    
    def get_memory(self) -> Memory:
        """
        Get the underlying LlamaIndex Memory instance.
        
        Returns:
            LlamaIndex Memory instance
        """
        return self.memory
