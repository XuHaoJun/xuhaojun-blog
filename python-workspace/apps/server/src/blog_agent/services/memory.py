"""Service for conversation memory and fact extraction."""

from typing import List, Optional
from llama_index.core import SummaryIndex, Document
from blog_agent.storage.models import ConversationMessage
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)

class MemoryService:
    """Service for extracting facts from conversation history."""

    def __init__(self):
        """Initialize service."""
        pass

    async def extract_facts(
        self, 
        messages: List[ConversationMessage], 
        max_characters: int = 5000
    ) -> str:
        """
        Extract key facts from a list of messages.
        
        Args:
            messages: List of conversation messages.
            max_characters: Maximum characters for the output.
            
        Returns:
            Extracted facts as a string.
        """
        if not messages:
            return ""

        # Format messages for LlamaIndex
        text_content = "\n\n".join([
            f"{msg.role.capitalize()}: {msg.content}" 
            for msg in messages 
            if msg.role != "system"
        ])

        try:
            # Create a document from the conversation history
            doc = Document(text=text_content)
            
            # Use SummaryIndex for high-level extraction
            # Note: In a real-world scenario, we might use a more specific prompt
            index = SummaryIndex.from_documents([doc])
            
            query_engine = index.as_query_engine(
                response_mode="tree_summarize"
            )
            
            prompt = (
                "請從以下對話紀錄中提取核心事實、決策點與技術細節。 "
                "請使用條列式（bullet points）呈現，並確保內容簡潔且保留最重要的背景資訊。 "
                f"輸出字數請控制在 {max_characters} 字以內。"
            )
            
            response = await query_engine.aquery(prompt)
            extracted_facts = str(response)

            # Ensure we respect the character limit
            if len(extracted_facts) > max_characters:
                logger.warning(
                    "Extracted facts exceeded character limit, truncating",
                    limit=max_characters,
                    actual=len(extracted_facts)
                )
                extracted_facts = extracted_facts[:max_characters]

            return extracted_facts

        except Exception as e:
            logger.error("Failed to extract facts", error=str(e), exc_info=True)
            # Fallback: simple truncation if LlamaIndex fails
            return text_content[:max_characters]

