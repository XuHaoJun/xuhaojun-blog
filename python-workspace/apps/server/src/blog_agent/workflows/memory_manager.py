"""Conversation memory management using ChatSummaryMemoryBuffer."""

from typing import List, Optional, Union

from llama_index.core.llms import ChatMessage
from llama_index.core.memory import ChatSummaryMemoryBuffer
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI

from blog_agent.config import config
from blog_agent.services.llm import get_llm
from blog_agent.storage.models import Message
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


def _get_summarizer_llm() -> Union[Ollama, OpenAI]:
    """
    Get LLM instance for summarization.
    
    Uses MEMORY_SUMMARIZER_PROVIDER if set, otherwise falls back to LLM_PROVIDER.
    For OpenAI, uses MEMORY_SUMMARIZER_MODEL (default: gpt-4o-mini) for cost efficiency.
    
    Returns:
        LLM instance configured for summarization
    """
    provider = config.MEMORY_SUMMARIZER_PROVIDER or config.LLM_PROVIDER
    
    if provider.lower() == "ollama":
        # Use the same model as main LLM for Ollama (no separate summarizer model)
        llm = Ollama(
            model=config.MEMORY_SUMMARIZER_MODEL,
            temperature=0.1,  # Lower temperature for summarization
            base_url=config.OLLAMA_BASE_URL,
            request_timeout=120.0,
            context_window=81920,
        )
        logger.debug("Initialized Ollama summarizer LLM", model=config.MEMORY_SUMMARIZER_MODEL)
    elif provider.lower() == "openai":
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI summarizer")
        # Use cheaper model for summarization
        llm = OpenAI(
            api_key=config.OPENAI_API_KEY,
            model=config.MEMORY_SUMMARIZER_MODEL,
            temperature=0.1,  # Lower temperature for summarization
        )
        logger.debug("Initialized OpenAI summarizer LLM", model=config.MEMORY_SUMMARIZER_MODEL)
    else:
        raise ValueError(f"Unsupported summarizer provider: {provider}. Must be 'ollama' or 'openai'")
    
    return llm


class ConversationMemoryManager:
    """Manages conversation memory using ChatSummaryMemoryBuffer."""
    
    def __init__(self, memory: Optional[ChatSummaryMemoryBuffer] = None):
        """
        Initialize memory manager.
        
        Args:
            memory: Optional existing ChatSummaryMemoryBuffer instance.
                   If None, creates a new one with default settings.
        """
        if memory is not None:
            self.memory = memory
        else:
            summarizer_llm = _get_summarizer_llm()
            self.memory = ChatSummaryMemoryBuffer.from_defaults(
                token_limit=config.MEMORY_TOKEN_LIMIT,
                llm=summarizer_llm,
            )
            logger.debug(
                "Created new ChatSummaryMemoryBuffer",
                token_limit=config.MEMORY_TOKEN_LIMIT,
            )
    
    @classmethod
    def from_messages(cls, messages: List[Message]) -> "ConversationMemoryManager":
        """
        Create memory manager from Message list.
        
        Args:
            messages: List of Message objects to initialize memory with
            
        Returns:
            ConversationMemoryManager instance with messages loaded
        """
        manager = cls()
        
        # Convert Message objects to ChatMessage and add to memory
        for msg in messages:
            chat_msg = ChatMessage(role=msg.role, content=msg.content)
            manager.memory.put(chat_msg)
        
        logger.debug("Initialized memory from messages", message_count=len(messages))
        return manager
    
    def get_summarized_context(self) -> str:
        """
        Get summarized conversation context as a string.
        
        Returns:
            String representation of conversation history with summaries
        """
        history = self.memory.get()
        
        # Convert ChatMessage list to formatted string
        context_parts = []
        for msg in history:
            role = msg.role
            content = msg.content
            
            # Format based on role
            if role == "system":
                # System messages (summaries) are formatted differently
                context_parts.append(f"[摘要] {content}")
            else:
                context_parts.append(f"{role}: {content}")
        
        context = "\n".join(context_parts)
        logger.debug("Retrieved summarized context", history_length=len(history))
        return context
    
    def get_all_messages(self) -> List[ChatMessage]:
        """
        Get all messages from memory (including summaries).
        
        Returns:
            List of ChatMessage objects
        """
        return self.memory.get()
    
    def put(self, message: Message) -> None:
        """
        Add a new message to memory.
        
        Args:
            message: Message object to add
        """
        chat_msg = ChatMessage(role=message.role, content=message.content)
        self.memory.put(chat_msg)
        logger.debug("Added message to memory", role=message.role)
    
    def get_memory(self) -> ChatSummaryMemoryBuffer:
        """
        Get the underlying ChatSummaryMemoryBuffer instance.
        
        Returns:
            ChatSummaryMemoryBuffer instance
        """
        return self.memory
