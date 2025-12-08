"""Blog editor workflow step (simple version without review/extension)."""

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from llama_index.core.workflow import Event, step
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI

from blog_agent.storage.models import PromptSuggestion

if TYPE_CHECKING:
    from blog_agent.workflows.reviewer import ReviewEvent

from blog_agent.services.llm import get_llm
from blog_agent.storage.models import BlogPost, ContentBlock, ContentExtract, PromptSuggestion, ReviewFindings
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


class EditEvent(Event):
    """Event containing edited blog post."""

    blog_post: BlogPost
    conversation_log_id: str
    prompt_suggestion: Optional[PromptSuggestion] = None  # T080: Include prompt suggestions (FR-014)
    content_blocks: list[ContentBlock] = []  # T081a, T081c: Content blocks for UI/UX support


class BlogEditor:
    """Blog editor step for generating final blog post."""

    def __init__(self, llm: Optional[Union[Ollama, OpenAI]] = None):
        """Initialize blog editor."""
        self.llm = llm or get_llm()

    @step
    async def edit(self, ev: "ReviewEvent") -> EditEvent:  # type: ignore
        """
        Generate blog post from extracted content with structured metadata, incorporating review findings.
        
        T080: Include prompt suggestions section in blog post (FR-014).
        """
        try:
            content_extract = ev.content_extract
            review_findings = ev.review_findings
            conversation_log_id = ev.conversation_log_id
            conversation_log_metadata = ev.conversation_log_metadata or {}
            errors = ev.errors or []
            prompt_suggestion = ev.prompt_suggestion  # T080: Get prompt suggestion from ReviewEvent

            # Generate blog post using LLM, incorporating review findings (T061)
            blog_content = await self._generate_blog_content(
                content_extract, review_findings, prompt_suggestion
            )

            # Extract metadata (title, summary, tags)
            title = await self._generate_title(content_extract)
            summary = await self._generate_summary(content_extract)
            tags = content_extract.core_concepts[:5]  # Use core concepts as tags

            # Build structured metadata from conversation log (FR-015: preserve timestamps, participants)
            blog_metadata = self._build_blog_metadata(
                conversation_log_metadata, content_extract, review_findings, errors, prompt_suggestion
            )

            blog_post = BlogPost(
                conversation_log_id=conversation_log_id,
                title=title,
                summary=summary,
                tags=tags,
                content=blog_content,
                metadata=blog_metadata,
                status="draft",
            )

            # T081a, T081c: Create ContentBlock objects from blog post content
            # Note: blog_post.id will be set after saving to database, so we'll create blocks later
            # For now, we'll prepare the blocks structure
            content_blocks = await self._create_content_blocks(
                blog_content, prompt_suggestion
            )

            return EditEvent(
                blog_post=blog_post,
                conversation_log_id=conversation_log_id,
                prompt_suggestion=prompt_suggestion,
                content_blocks=content_blocks,  # T081a, T081c: Include content blocks
            )

        except Exception as e:
            logger.error("Blog editing failed", error=str(e), exc_info=True)
            raise

    async def _generate_blog_content(
        self,
        content_extract: ContentExtract,
        review_findings: ReviewFindings,
        prompt_suggestion: Optional[PromptSuggestion] = None,
    ) -> str:
        """Generate blog post content in Markdown format, incorporating review findings (T061)."""
        # Build review context for LLM
        review_context = ""
        if review_findings.issues:
            logical_gaps = review_findings.issues.get("logical_gaps", [])
            factual_inconsistencies = review_findings.issues.get("factual_inconsistencies", [])
            unclear_explanations = review_findings.issues.get("unclear_explanations", [])

            if logical_gaps or factual_inconsistencies or unclear_explanations:
                review_context = "\n\n審閱發現的問題（請在生成文章時處理或說明）：\n"
                if logical_gaps:
                    review_context += f"\n邏輯斷層 ({len(logical_gaps)} 個)：\n"
                    for gap in logical_gaps[:3]:  # Show top 3
                        review_context += f"- {gap.get('description', '')}\n"
                if factual_inconsistencies:
                    review_context += f"\n事實不一致 ({len(factual_inconsistencies)} 個)：\n"
                    for inc in factual_inconsistencies[:3]:  # Show top 3
                        review_context += f"- {inc.get('description', '')}\n"
                if unclear_explanations:
                    review_context += f"\n不清楚的解釋 ({len(unclear_explanations)} 個)：\n"
                    for unclear in unclear_explanations[:3]:  # Show top 3
                        review_context += f"- {unclear.get('description', '')} (建議：{unclear.get('suggestion', '')})\n"

        if review_findings.improvement_suggestions:
            review_context += "\n\n改進建議：\n"
            for suggestion in review_findings.improvement_suggestions[:5]:  # Top 5
                review_context += f"- {suggestion}\n"

        prompt = f"""請將以下對話內容改寫成一篇結構完整的技術部落格文章。

核心觀點：
{chr(10).join('- ' + insight for insight in content_extract.key_insights)}

核心概念：
{', '.join(content_extract.core_concepts)}

對話內容：
{content_extract.filtered_content}
{review_context}

要求：
1. 使用 Markdown 格式
2. 包含標題、前言、正文、總結
3. 保持技術深度與可讀性
4. 將對話中的問答轉換成流暢的敘述
5. 突出核心觀點與概念
6. 根據審閱發現的問題和改進建議，在文章中處理或說明這些問題
7. 如果發現邏輯斷層，請補充必要的連接說明
8. 如果發現不清楚的解釋，請提供更詳細的說明或範例
9. 如果發現事實不一致，請在文章中澄清或標註需要驗證

請直接輸出完整的 Markdown 文章，不要額外說明。"""

        response = await self.llm.complete(prompt)
        blog_content = response.text.strip()
        
        # T080: Add prompt suggestions section to blog content (FR-014)
        if prompt_suggestion and prompt_suggestion.original_prompt:
            prompt_section = self._format_prompt_suggestions(prompt_suggestion)
            blog_content += f"\n\n{prompt_section}"
        
        return blog_content

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

        response = await self.llm.complete(prompt)
        # Clean up title (remove quotes, extra spaces)
        title = response.text.strip().strip('"').strip("'").strip()
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

        response = await self.llm.complete(prompt)
        return response.text.strip()[:500]  # Limit length

    def _format_prompt_suggestions(self, prompt_suggestion: PromptSuggestion) -> str:
        """
        T081: Format prompt suggestions as side-by-side comparison (FR-014).
        
        Formats the prompt suggestions section for inclusion in the blog post.
        """
        section = "## 提示詞優化建議\n\n"
        
        section += f"### 原始提示詞\n\n{prompt_suggestion.original_prompt}\n\n"
        
        if prompt_suggestion.analysis:
            section += f"### 分析\n\n{prompt_suggestion.analysis}\n\n"
        
        if prompt_suggestion.better_candidates:
            section += "### 改進版本\n\n"
            for i, candidate in enumerate(prompt_suggestion.better_candidates[:5], 1):  # Show top 5
                section += f"#### 版本 {i}\n\n{candidate}\n\n"
        
        if prompt_suggestion.reasoning:
            section += f"### 改進理由\n\n{prompt_suggestion.reasoning}\n\n"
        
        return section

    def _build_blog_metadata(
        self,
        conversation_log_metadata: Optional[Dict[str, Any]],
        content_extract: ContentExtract,
        review_findings: Optional[ReviewFindings] = None,
        errors: Optional[List[str]] = None,
        prompt_suggestion: Optional[PromptSuggestion] = None,
    ) -> Dict[str, Any]:
        """
        Build structured metadata for blog post from conversation log metadata (FR-015).
        
        Args:
            conversation_log_metadata: Metadata extracted from conversation log
            content_extract: Content extract with key insights and concepts
            review_findings: Review findings from content review step (T061)
            errors: List of errors that cannot be auto-corrected (T062)
            
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
        
        # Add review findings metadata (T061)
        if review_findings:
            metadata["review_summary"] = {
                "logical_gaps_count": len(review_findings.issues.get("logical_gaps", [])),
                "factual_inconsistencies_count": len(
                    review_findings.issues.get("factual_inconsistencies", [])
                ),
                "unclear_explanations_count": len(
                    review_findings.issues.get("unclear_explanations", [])
                ),
                "fact_checking_needs_count": len(review_findings.fact_checking_needs),
                "improvement_suggestions_count": len(review_findings.improvement_suggestions),
            }
        
        # Add errors that require human attention (T062)
        if errors:
            metadata["review_errors"] = errors
        
        # Add prompt suggestion metadata (T080, FR-014)
        if prompt_suggestion:
            metadata["prompt_suggestion"] = {
                "has_suggestions": bool(prompt_suggestion.better_candidates),
                "candidates_count": len(prompt_suggestion.better_candidates),
            }
        
        return metadata

    async def _create_content_blocks(
        self, blog_content: str, prompt_suggestion: Optional[PromptSuggestion] = None
    ) -> list[ContentBlock]:
        """
        T081a, T081c: Create ContentBlock objects from blog post content.
        
        Splits the blog content into structured blocks for UI/UX support.
        Each block can optionally be associated with a prompt suggestion.
        
        T081b: Associates ContentBlocks with PromptSuggestions when content is related to prompts.
        """
        import re
        blocks = []
        
        # Split content into blocks by markdown headers (## and ###)
        # This creates natural sections that can be displayed side-by-side with prompts
        # Pattern: Split by ## (level 2 headers) or ### (level 3 headers)
        # We'll preserve the headers in each block
        section_pattern = r'\n(##+\s+[^\n]+)'
        sections = re.split(section_pattern, blog_content)
        
        block_order = 0
        
        # First part (before any headers) is introduction
        if sections and sections[0].strip():
            intro = sections[0].strip()
            if intro:
                # T081b: Associate intro with prompt_suggestion if available
                # The intro often contains content generated from the original prompt
                block = ContentBlock(
                    blog_post_id=uuid4(),  # Placeholder, will be set after blog_post is saved
                    block_order=block_order,
                    text=intro,
                    prompt_suggestion_id=prompt_suggestion.id if prompt_suggestion and prompt_suggestion.id else None,
                )
                blocks.append(block)
                block_order += 1
        
        # Process remaining sections (header + content pairs)
        i = 1
        while i < len(sections):
            if i + 1 < len(sections):
                header = sections[i].strip()  # The header (## Title)
                content = sections[i + 1].strip()  # The content after header
                
                if content:
                    section_text = f"{header}\n\n{content}"
                    
                    # T081b: Associate with prompt_suggestion if this section is related to prompts
                    prompt_suggestion_id = None
                    if prompt_suggestion and prompt_suggestion.id:
                        # Check if this section contains prompt-related keywords
                        prompt_keywords = ["提示詞", "prompt", "優化", "建議", "候選", "candidate"]
                        if any(keyword in section_text.lower() for keyword in prompt_keywords):
                            prompt_suggestion_id = prompt_suggestion.id
                        # Also associate if this is one of the first few sections (likely related to original prompt)
                        elif block_order < 3:
                            prompt_suggestion_id = prompt_suggestion.id
                    
                    block = ContentBlock(
                        blog_post_id=uuid4(),  # Placeholder, will be set after blog_post is saved
                        block_order=block_order,
                        text=section_text,
                        prompt_suggestion_id=prompt_suggestion_id,
                    )
                    blocks.append(block)
                    block_order += 1
            i += 2
        
        # If no sections found, create a single block with all content
        if not blocks:
            block = ContentBlock(
                blog_post_id=uuid4(),  # Placeholder
                block_order=0,
                text=blog_content,
                prompt_suggestion_id=prompt_suggestion.id if prompt_suggestion and prompt_suggestion.id else None,
            )
            blocks.append(block)
        
        logger.info(
            "Content blocks created",
            blocks_count=len(blocks),
            has_prompt_association=any(b.prompt_suggestion_id for b in blocks),
        )
        
        return blocks

