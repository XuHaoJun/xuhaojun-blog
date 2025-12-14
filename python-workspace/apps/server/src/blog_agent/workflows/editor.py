"""Blog editor workflow step (simple version without review/extension)."""

from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from uuid import uuid4

from llama_index.core.workflow import Event, step
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI

from blog_agent.storage.models import PromptSuggestion

from blog_agent.config import config
from blog_agent.services.llm import get_llm
from blog_agent.storage.models import BlogPost, ContentBlock, ContentExtract, PromptSuggestion, ReviewFindings
from blog_agent.utils.logging import get_logger

# Import ReviewEvent for type hints (needed at runtime for @step decorator)
from blog_agent.workflows.reviewer import ReviewEvent

# Import at runtime for Pydantic model_rebuild()
from blog_agent.workflows.memory_manager import ConversationMemoryManager

logger = get_logger(__name__)


class EditEvent(Event):
    """Event containing edited blog post."""

    blog_post: BlogPost
    conversation_log_id: str
    prompt_suggestions: List[PromptSuggestion] = []  # T080: Include prompt suggestions (FR-014, 支援多個)
    content_blocks: list[ContentBlock] = []  # T081a, T081c: Content blocks for UI/UX support
    memory: Optional[ConversationMemoryManager] = None  # Optional memory manager for conversation history


# Rebuild model to resolve forward references
EditEvent.model_rebuild()


class BlogEditor:
    """Blog editor step for generating final blog post."""

    def __init__(self, llm: Optional[Union["Ollama", "OpenAI"]] = None):
        """Initialize blog editor."""
        self.llm = llm or get_llm()

    @step
    async def edit(self, ev: ReviewEvent) -> EditEvent:  # type: ignore
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
            prompt_suggestions = ev.prompt_suggestions  # T080: Get prompt suggestions from ReviewEvent (支援多個)
            memory = ev.memory  # Get memory from event

            # Generate blog post using LLM, incorporating review findings (T061)
            # Use first prompt suggestion for blog content generation (backward compatibility)
            first_prompt_suggestion = prompt_suggestions[0] if prompt_suggestions else None
            blog_content = await self._generate_blog_content(
                content_extract, review_findings, first_prompt_suggestion
            )

            # Extract metadata (title, summary, tags)
            title = await self._generate_title(content_extract)
            summary = await self._generate_summary(content_extract)
            tags = content_extract.core_concepts[:5]  # Use core concepts as tags

            # Build structured metadata from conversation log (FR-015: preserve timestamps, participants)
            blog_metadata = self._build_blog_metadata(
                conversation_log_metadata, content_extract, review_findings, errors, prompt_suggestions
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

            # Content blocks are no longer generated - system now displays original conversation content
            logger.info(
                "Blog post created without content blocks",
                conversation_log_id=str(conversation_log_id),
            )

            return EditEvent(
                blog_post=blog_post,
                conversation_log_id=conversation_log_id,
                prompt_suggestions=prompt_suggestions,
                content_blocks=[],  # Empty for backward compatibility
                memory=memory,
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

        prompt = f"""你是一位擁有深厚技術背景的資深工程師，也是讀者身邊那位聰明、誠實且樂於分享的朋友。
請基於以下對話內容，撰寫一篇技術部落格文章。

核心觀點 (Key Insights)：
{chr(10).join('- ' + insight for insight in content_extract.key_insights)}

核心概念 (Core Concepts)：
{', '.join(content_extract.core_concepts)}

原始素材 (Context)：
{content_extract.filtered_content}
{review_context}

寫作原則與要求 (Soul Guidelines)：
1. **語氣與風格**：
   - 就像在跟一位聰明的同事解釋技術難題，語氣自信、直接、熱情，但不要傲慢。
   - **嚴禁 AI 式廢話**：不要使用 "總而言之"、"讓我們深入探討"、"就像織錦一樣" 等填充詞。直接切入重點。
   - 展現智識好奇心 (Intellectual Curiosity)，探索概念背後的 "為什麼"，而不僅是 "是什麼"。

2. **結構與內容**：
   - 使用 Markdown 格式。
   - 將對話中的問答碎片，重組成連貫的敘事流 (Narrative Flow)。
   - **實質性幫助 (Substantive Helpfulness)**：讀者是成年人，不要過度簡化，也不要過度警告 (除非涉及安全紅線)。提供具體、可操作的建議。

3. **處理審閱問題 (Handling Issues)**：
   - 參考上述的「審閱問題」與「改進建議」。
   - **誠實 (Honesty)**：如果原始素材有邏輯斷層或不清楚之處，請運用你的知識庫進行合理的推論並補充，但若無法確定，請保持「校準過的懷疑」(Calibrated Uncertainty)，不要捏造事實。
   - 對於事實不一致處，請在文中以專業角度澄清，幫助讀者建立正確的心理模型。

請直接輸出文章內容，不需包含開場白或額外說明。"""

        # Use writing temperature (0.5) for blog content generation
        writing_llm = get_llm(temperature=config.LLM_TEMPERATURE_WRITING)
        response = await writing_llm.acomplete(prompt)
        blog_content = response.text.strip()
        
        # T080: Add prompt suggestions section to blog content (FR-014)
        # Note: This is kept for backward compatibility, but blog content is no longer displayed in frontend
        if prompt_suggestion and prompt_suggestion.original_prompt:
            prompt_section = self._format_prompt_suggestions([prompt_suggestion])
            blog_content += f"\n\n{prompt_section}"
        
        return blog_content

    async def _generate_title(self, content_extract: ContentExtract) -> str:
        """Generate blog post title."""
        prompt = f"""請為這篇技術文章構思一個標題。

核心觀點：
{chr(10).join('- ' + insight for insight in content_extract.key_insights)}

要求：
1. **拒絕陳腔濫調**：不要使用 "揭密"、"解鎖...的力量"、"終極指南" 這類行銷話術。
2. **實質與精準**：標題應直接反映文章解決的具體技術問題或提供的核心洞見。
3. **風格**：簡潔、專業，像是一個開發者會在 Hacker News 或技術論壇上點擊的標題。
4. 長度控制在 60 個字元以內。

請只輸出標題本身，不要加引號。"""

        # Use creative temperature (0.6) for title generation
        creative_llm = get_llm(temperature=config.LLM_TEMPERATURE_CREATIVE)
        response = await creative_llm.acomplete(prompt)
        # Clean up title (remove quotes, extra spaces)
        title = response.text.strip().strip('"').strip("'").strip()
        return title[:200]  # Limit length

    async def _generate_summary(self, content_extract: ContentExtract) -> str:
        """Generate blog post summary."""
        prompt = f"""請為這篇文章撰寫一段摘要（TL;DR）。

核心觀點：
{chr(10).join('- ' + insight for insight in content_extract.key_insights)}

要求：
1. **尊重讀者時間**：不要寫 "這篇文章將會討論..."，直接說出文章的結論和價值。
2. **高密度資訊**：用 2-3 句話濃縮最關鍵的技術決策或洞見。
3. **語氣**：客觀、冷靜、有洞察力。

請只輸出摘要內容。"""

        # Use creative temperature (0.6) for summary generation
        creative_llm = get_llm(temperature=config.LLM_TEMPERATURE_CREATIVE)
        response = await creative_llm.acomplete(prompt)
        return response.text.strip()[:500]  # Limit length

    def _format_prompt_suggestions(self, prompt_suggestions: List[PromptSuggestion]) -> str:
        """
        T081: Format prompt suggestions as side-by-side comparison (FR-014).
        
        Formats the prompt suggestions section for inclusion in the blog post.
        Now supports multiple prompt suggestions.
        """
        section = "## 提示詞優化建議\n\n"
        
        for idx, prompt_suggestion in enumerate(prompt_suggestions, 1):
            if idx > 1:
                section += "\n---\n\n"
            
            section += f"### 提示詞 {idx}\n\n"
            section += f"#### 原始提示詞\n\n{prompt_suggestion.original_prompt}\n\n"
            
            if prompt_suggestion.analysis:
                section += f"#### 分析\n\n{prompt_suggestion.analysis}\n\n"
            
            if prompt_suggestion.better_candidates:
                section += "#### 改進版本\n\n"
                for i, candidate in enumerate(prompt_suggestion.better_candidates[:5], 1):  # Show top 5
                    section += f"##### 版本 {i}\n\n{candidate.prompt}\n\n"
            
            if prompt_suggestion.reasoning:
                section += f"#### 改進理由\n\n{prompt_suggestion.reasoning}\n\n"
        
        return section

    def _build_blog_metadata(
        self,
        conversation_log_metadata: Optional[Dict[str, Any]],
        content_extract: ContentExtract,
        review_findings: Optional[ReviewFindings] = None,
        errors: Optional[List[str]] = None,
        prompt_suggestions: Optional[List[PromptSuggestion]] = None,
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
        
        # Add prompt suggestions metadata (T080, FR-014)
        if prompt_suggestions:
            total_candidates = sum(len(ps.better_candidates) for ps in prompt_suggestions)
            metadata["prompt_suggestions"] = {
                "count": len(prompt_suggestions),
                "has_suggestions": total_candidates > 0,
                "total_candidates_count": total_candidates,
            }
        
        return metadata

    # _create_content_blocks method removed - system now displays original conversation content instead

