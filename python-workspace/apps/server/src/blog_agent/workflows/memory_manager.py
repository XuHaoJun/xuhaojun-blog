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
            """你是一個精準的「事實抽取」系統，負責從對話中擷取使用者已明確透露或對任務關鍵的資訊。\n\n指示：\n1. 請閱讀此訊息之前提供的對話片段\n2. 抽取具體、可驗證的事實（例如：偏好、個人資訊、需求、限制、背景脈絡）\n3. 不要加入主觀推測、意見、摘要或詮釋\n4. 不要重複已存在於 existing_facts 的事實\n5. 每個事實用一個 <fact> XML 標籤呈現\n6. 請使用「正體中文」輸出\n\n<existing_facts>\n{{ existing_facts }}\n</existing_facts>\n\n請只回傳以下格式（不要有任何額外文字）：\n<facts>\n  <fact>具體事實 1</fact>\n  <fact>具體事實 2</fact>\n  <!-- 視需要增加 -->\n</facts>\n\n如果沒有新事實，回傳：<facts></facts>"""
        )

        fact_condense_prompt = RichPromptTemplate(
            """你是一個精準的「事實濃縮」系統，負責把現有事實整理成更精簡的清單。\n\n指示：\n1. 請閱讀現有事實清單 existing_facts\n2. 請將事實濃縮為少於 {{ max_facts }} 條\n3. 只保留對任務重要且可驗證的事實（偏好、個人資訊、需求、限制、背景）\n4. 不要加入主觀推測、意見、摘要或詮釋\n5. 每個事實用一個 <fact> XML 標籤呈現\n6. 請使用「正體中文」輸出\n\n<existing_facts>\n{{ existing_facts }}\n</existing_facts>\n\n請只回傳以下格式（不要有任何額外文字）：\n<facts>\n  <fact>具體事實 1</fact>\n  <fact>具體事實 2</fact>\n  <!-- 視需要增加 -->\n</facts>\n\n如果沒有新事實，回傳：<facts></facts>"""
        )

        fact_block = FactExtractionMemoryBlock(
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
            token_flush_size=500,
            chat_history_token_ratio=0.2,
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
                await fact_block.aput(
                    chat_messages,
                    from_short_term_memory=True,
                    session_id=manager.memory.session_id,
                )
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
