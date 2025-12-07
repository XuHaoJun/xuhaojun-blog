"""Blog editor workflow step (simple version without review/extension)."""

from typing import TYPE_CHECKING, Any, Dict, Optional

from llama_index.core.workflow import Event, step

if TYPE_CHECKING:
    from blog_agent.workflows.extractor import ExtractEvent

from blog_agent.services.llm_service import get_llm_service
from blog_agent.storage.models import BlogPost, ContentExtract
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


class EditEvent(Event):
    """Event containing edited blog post."""

    blog_post: BlogPost
    conversation_log_id: str


class BlogEditor:
    """Blog editor step for generating final blog post."""

    def __init__(self, llm_service=None):
        """Initialize blog editor."""
        self.llm_service = llm_service or get_llm_service()

    @step
    async def edit(self, ev: "ExtractEvent") -> EditEvent:  # type: ignore
        """Generate blog post from extracted content with structured metadata."""
        try:
            content_extract = ev.content_extract
            conversation_log_id = ev.conversation_log_id
            conversation_log_metadata = ev.conversation_log_metadata or {}

            # Generate blog post using LLM
            blog_content = await self._generate_blog_content(content_extract)

            # Extract metadata (title, summary, tags)
            title = await self._generate_title(content_extract)
            summary = await self._generate_summary(content_extract)
            tags = content_extract.core_concepts[:5]  # Use core concepts as tags

            # Build structured metadata from conversation log (FR-015: preserve timestamps, participants)
            blog_metadata = self._build_blog_metadata(conversation_log_metadata, content_extract)

            blog_post = BlogPost(
                conversation_log_id=conversation_log_id,
                title=title,
                summary=summary,
                tags=tags,
                content=blog_content,
                metadata=blog_metadata,
                status="draft",
            )

            return EditEvent(
                blog_post=blog_post,
                conversation_log_id=conversation_log_id,
            )

        except Exception as e:
            logger.error("Blog editing failed", error=str(e), exc_info=True)
            raise

    async def _generate_blog_content(self, content_extract: ContentExtract) -> str:
        """Generate blog post content in Markdown format."""
        prompt = f"""請將以下對話內容改寫成一篇結構完整的技術部落格文章。

核心觀點：
{chr(10).join('- ' + insight for insight in content_extract.key_insights)}

核心概念：
{', '.join(content_extract.core_concepts)}

對話內容：
{content_extract.filtered_content}

要求：
1. 使用 Markdown 格式
2. 包含標題、前言、正文、總結
3. 保持技術深度與可讀性
4. 將對話中的問答轉換成流暢的敘述
5. 突出核心觀點與概念

請直接輸出完整的 Markdown 文章，不要額外說明。"""

        response = await self.llm_service.generate(prompt)
        return response.strip()

    async def _generate_title(self, content_extract: ContentExtract) -> str:
        """Generate blog post title."""
        prompt = f"""根據以下核心觀點，生成一個吸引人的部落格文章標題。

核心觀點：
{chr(10).join('- ' + insight for insight in content_extract.key_insights)}

核心概念：
{', '.join(content_extract.core_concepts)}

要求：
1. 標題要簡潔有力
2. 能反映文章核心內容
3. 適合技術部落格風格

請只輸出標題，不要額外說明。"""

        response = await self.llm_service.generate(prompt)
        # Clean up title (remove quotes, extra spaces)
        title = response.strip().strip('"').strip("'").strip()
        return title[:200]  # Limit length

    async def _generate_summary(self, content_extract: ContentExtract) -> str:
        """Generate blog post summary."""
        prompt = f"""根據以下核心觀點，生成一篇簡短的摘要（100-150字）。

核心觀點：
{chr(10).join('- ' + insight for insight in content_extract.key_insights)}

要求：
1. 摘要要簡潔明瞭
2. 涵蓋文章主要內容
3. 適合放在文章開頭或 metadata

請只輸出摘要，不要額外說明。"""

        response = await self.llm_service.generate(prompt)
        return response.strip()[:500]  # Limit length

    def _build_blog_metadata(self, conversation_log_metadata: Optional[Dict[str, Any]], content_extract: ContentExtract) -> Dict[str, Any]:
        """
        Build structured metadata for blog post from conversation log metadata (FR-015).
        
        Args:
            conversation_log_metadata: Metadata extracted from conversation log
            content_extract: Content extract with key insights and concepts
            
        Returns:
            Dictionary containing structured blog metadata
        """
        metadata = {}
        
        # Preserve timestamps from conversation log (FR-015)
        if "timestamps" in conversation_log_metadata:
            metadata["conversation_timestamps"] = conversation_log_metadata["timestamps"]
        
        # Preserve participants from conversation log (FR-015)
        if "participants" in conversation_log_metadata:
            metadata["conversation_participants"] = conversation_log_metadata["participants"]
        
        # Add language if available
        if "language" in conversation_log_metadata:
            metadata["language"] = conversation_log_metadata["language"]
        
        # Add message count if available
        if "message_count" in conversation_log_metadata:
            metadata["message_count"] = conversation_log_metadata["message_count"]
        
        # Add key insights and core concepts for reference
        metadata["key_insights"] = content_extract.key_insights
        metadata["core_concepts"] = content_extract.core_concepts
        
        return metadata

