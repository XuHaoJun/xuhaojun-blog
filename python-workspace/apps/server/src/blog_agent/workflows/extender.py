"""Content extension workflow step for research and knowledge gap filling."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from llama_index.core import PromptTemplate
from llama_index.core.workflow import Event, step

from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI

from blog_agent.services.embedding import generate_embedding
from blog_agent.services.llm import get_llm
from blog_agent.services.tavily_service import get_tavily_service
from blog_agent.services.vector_store import VectorStore
from blog_agent.storage.models import ContentExtract
from blog_agent.workflows.extractor import ExtractEvent
from blog_agent.utils.errors import ExternalServiceError
from blog_agent.utils.logging import get_logger
from blog_agent.workflows.schemas import KnowledgeGapResponse

if TYPE_CHECKING:
    from blog_agent.workflows.memory_manager import ConversationMemoryManager

logger = get_logger(__name__)


class ExtendEvent(Event):
    """Event containing extended content."""

    content_extract: ContentExtract  # Updated with extended content
    conversation_log_id: str
    conversation_log_metadata: Optional[Dict[str, Any]] = None
    research_results: List[Dict[str, Any]] = []  # Research results from Tavily/KB
    knowledge_gaps: List[Dict[str, Any]] = []  # Identified knowledge gaps
    memory: Optional["ConversationMemoryManager"] = None  # Optional memory manager for conversation history


class ContentExtender:
    """Content extension step for identifying gaps and researching additional information."""

    def __init__(
        self,
        llm: Optional[Union[Ollama, OpenAI]] = None,
        tavily_service=None,
        vector_store: Optional[VectorStore] = None,
    ):
        """Initialize content extender."""
        self.llm = llm or get_llm()
        self.tavily_service = tavily_service or get_tavily_service()
        self.vector_store = vector_store or VectorStore()

    @step
    async def extend(self, ev: ExtractEvent) -> ExtendEvent:  # type: ignore
        """
        Extend content by identifying knowledge gaps and researching additional information.
        
        Steps:
        1. Identify knowledge gaps in the content
        2. Query knowledge base first (if available) (FR-018, T069)
        3. Use Tavily search for gaps not covered by KB (T066)
        4. Integrate research results naturally into content (T067)
        """
        try:
            content_extract = ev.content_extract
            conversation_log_id = ev.conversation_log_id
            memory = ev.memory  # Get memory from event

            # Step 1: Identify knowledge gaps (T065)
            knowledge_gaps = await self._identify_knowledge_gaps(content_extract)
            logger.info("Identified knowledge gaps", count=len(knowledge_gaps))

            if not knowledge_gaps:
                # No gaps found, return original content
                return ExtendEvent(
                    content_extract=content_extract,
                    conversation_log_id=conversation_log_id,
                    conversation_log_metadata=ev.conversation_log_metadata or {},
                    research_results=[],
                    knowledge_gaps=[],
                    memory=memory,
                )

            # Step 2 & 3: Research gaps (KB first, then Tavily) (T069)
            research_results = await self._research_gaps(knowledge_gaps)

            # Step 4: Integrate research into content (T067)
            extended_content = await self._integrate_research(
                content_extract, knowledge_gaps, research_results
            )

            # Update content extract with extended content
            extended_extract = ContentExtract(
                id=content_extract.id,
                conversation_log_id=content_extract.conversation_log_id,
                key_insights=content_extract.key_insights,
                core_concepts=content_extract.core_concepts,
                filtered_content=extended_content,
            )

            return ExtendEvent(
                content_extract=extended_extract,
                conversation_log_id=conversation_log_id,
                conversation_log_metadata=ev.conversation_log_metadata or {},
                research_results=research_results,
                knowledge_gaps=knowledge_gaps,
                memory=memory,
            )

        except ExternalServiceError:
            # Re-raise external service errors (FR-019)
            raise
        except Exception as e:
            logger.error("Content extension failed", error=str(e), exc_info=True)
            raise

    async def _identify_knowledge_gaps(
        self, content_extract: ContentExtract
    ) -> List[Dict[str, Any]]:
        """
        Identify areas in content that lack sufficient context or detail (T065).
        
        Aligned with Claude's Soul Overview principles:
        - Focus on substantive value, not just filling gaps
        - Understand underlying reader goals
        - Prioritize genuine helpfulness over completeness
        
        Returns:
            List of knowledge gaps, each with:
            - type: Type of gap (e.g., "missing_context", "unclear_concept", "missing_background")
            - description: Description of the gap
            - location: Where in the content the gap appears
            - query: Search query to find information about this gap
        """
        template_str = """你是一位專業、富有洞察力的編輯，目標是協助完善這篇文章，使其對讀者產生最大的實質幫助。

核心觀點：
{key_insights}

核心概念：
{core_concepts}

內容：
{content}

請分析內容，並找出阻礙讀者完全理解或應用這些觀點的「關鍵知識缺口」。不要為了填補而填補，請專注於以下層面：

1. **實用性缺口**：讀者在理解了概念後，是否缺乏執行的具體細節或步驟？(Actionable advice)
2. **脈絡缺口**：是否使用了專業術語或提及了事件，但未提供必要的背景，導致非專家讀者無法跟上？
3. **論證缺口**：某些主張是否缺乏證據、數據或反面觀點的平衡？(Intellectual honesty)
4. **盲點檢查**：是否有明顯遺漏的關鍵視角，導致觀點不夠全面？

請列出缺口，並為每個缺口提供一個「針對性極強」的搜尋查詢 (Query)，以便我們進行精準研究。"""

        try:
            key_insights_str = "\n".join("- " + insight for insight in content_extract.key_insights)
            core_concepts_str = ", ".join(content_extract.core_concepts)
            
            # Convert template string to PromptTemplate object
            prompt_tmpl = PromptTemplate(template_str)
            
            response = await self.llm.astructured_predict(
                KnowledgeGapResponse,
                prompt_tmpl,
                key_insights=key_insights_str,
                core_concepts=core_concepts_str,
                content=content_extract.filtered_content,
            )

            gaps = [gap.model_dump() for gap in response.gaps]
            logger.info("Identified knowledge gaps", count=len(gaps))
            return gaps

        except Exception as e:
            logger.warning("Failed to identify knowledge gaps", error=str(e))
            return []

    async def _research_gaps(
        self, knowledge_gaps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Research knowledge gaps using KB first, then Tavily (T066, T069).
        
        Args:
            knowledge_gaps: List of identified knowledge gaps
            
        Returns:
            List of research results, each with:
            - gap: The original gap information
            - source: "knowledge_base" or "tavily"
            - results: Research results from the source
        """
        research_results = []

        for gap in knowledge_gaps:
            query = gap.get("query", "")
            if not query:
                continue

            gap_results = {
                "gap": gap,
                "source": None,
                "results": [],
            }

            # Step 1: Try knowledge base first (T069, FR-018)
            kb_results = await self._query_knowledge_base(query)
            if kb_results:
                gap_results["source"] = "knowledge_base"
                gap_results["results"] = kb_results
                logger.info(
                    "Found KB results for gap",
                    query=query,
                    results_count=len(kb_results),
                )
            else:
                # Step 2: Use Tavily if KB has no results (T066)
                try:
                    tavily_results = await self.tavily_service.search(
                        query=query,
                        max_results=3,  # Limit results per gap
                        search_depth="advanced",
                    )
                    if tavily_results:
                        gap_results["source"] = "tavily"
                        gap_results["results"] = tavily_results
                        logger.info(
                            "Found Tavily results for gap",
                            query=query,
                            results_count=len(tavily_results),
                        )
                except ExternalServiceError as e:
                    # Tavily failure should stop processing (FR-019)
                    logger.error("Tavily search failed during gap research", query=query, error=str(e))
                    raise

            if gap_results["results"]:
                research_results.append(gap_results)

        return research_results

    async def _filter_bad_results(
        self, research_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter out low-quality or irrelevant research results.
        
        Aligned with Claude's Soul Overview principles:
        - Agentic Safety: Don't integrate harmful or low-quality content
        - Quality over quantity: Better to skip than to mislead
        
        Args:
            research_results: List of research results to filter
            
        Returns:
            Filtered list of high-quality, relevant research results
        """
        if not research_results:
            return []

        filtered = []
        for result in research_results:
            gap = result.get("gap", {})
            results = result.get("results", [])
            
            if not results:
                continue

            # Filter results based on quality indicators
            quality_results = []
            for r in results:
                # Check for low-quality indicators
                content = r.get("content", "") or r.get("text", "")
                title = r.get("title", "")
                url = r.get("url", "")
                
                # Skip if content is too short or empty
                if len(content) < 50:
                    continue
                
                # Skip if title/content suggests spam or low quality
                spam_indicators = ["click here", "buy now", "advertisement", "sponsored"]
                if any(indicator.lower() in (title + content).lower() for indicator in spam_indicators):
                    continue
                
                # For Tavily results, check URL quality
                if url:
                    low_quality_domains = ["spam", "ad", "clickbait"]
                    if any(domain in url.lower() for domain in low_quality_domains):
                        continue
                
                quality_results.append(r)
            
            # Only include gap if it has at least one quality result
            if quality_results:
                filtered.append({
                    "gap": gap,
                    "source": result.get("source"),
                    "results": quality_results,
                })
        
        logger.info(
            "Filtered research results",
            original_count=len(research_results),
            filtered_count=len(filtered),
        )
        return filtered

    async def _query_knowledge_base(self, query: str) -> List[Dict[str, Any]]:
        """
        Query personal knowledge base if available (T068, FR-018).
        
        Args:
            query: Search query
            
        Returns:
            List of knowledge base results, empty if KB not available or no results
        """
        try:
            # Generate embedding for the query
            query_embedding = await generate_embedding(query)
            logger.debug("Generated embedding for KB query", query=query, embedding_dim=len(query_embedding))
            
            # Query knowledge base with the embedding
            results = await self.vector_store.query_knowledge_base(
                query=query,
                query_embedding=query_embedding,
            )
            
            logger.info("Knowledge base query completed", query=query, results_count=len(results))
            return results

        except Exception as e:
            logger.warning("Knowledge base query failed", query=query, error=str(e))
            # Return empty list on failure (KB is optional, FR-018)
            return []

    async def _integrate_research(
        self,
        content_extract: ContentExtract,
        knowledge_gaps: List[Dict[str, Any]],
        research_results: List[Dict[str, Any]],
    ) -> str:
        """
        Integrate research results naturally into content (T067).
        
        Aligned with Claude's Soul Overview principles:
        - Honesty & Calibration: Only assert when research supports it
        - Non-deceptive: Distinguish facts from opinions
        - Genuine Helpfulness: Focus on reader value, not length
        
        Args:
            content_extract: Original content extract
            knowledge_gaps: Identified knowledge gaps
            research_results: Research results from KB/Tavily
            
        Returns:
            Extended content with research integrated naturally
        """
        if not research_results:
            # No research to integrate, return original content
            return content_extract.filtered_content

        # Filter low-quality results before integration
        filtered_results = await self._filter_bad_results(research_results)
        if not filtered_results:
            logger.info("All research results filtered out as low-quality, returning original content")
            return content_extract.filtered_content

        # Build research context for LLM
        research_context = "\n\n研究補充資訊：\n"
        for result in filtered_results:
            gap = result["gap"]
            source = result["source"]
            results = result["results"]

            research_context += f"\n缺口：{gap.get('description', '')}\n"
            research_context += f"來源：{source}\n"

            if source == "tavily":
                for r in results[:2]:  # Use top 2 results per gap
                    research_context += f"- {r.get('title', '')}: {r.get('content', '')[:200]}...\n"
                    research_context += f"  來源：{r.get('url', '')}\n"
            elif source == "knowledge_base":
                for r in results[:2]:
                    research_context += f"- {r.get('content', '')[:200]}...\n"

        prompt = f"""請以一位博學、客觀且誠實的共同作者身分，將研究資料整合進原始內容中。

原始內容：
{content_extract.filtered_content}

{research_context}

**整合原則 (基於 Claude 的核心價值)：**

1. **誠實與校準 (Honesty & Calibration)**：
   - 僅在研究資料充分支持時才進行斷言。
   - 如果研究結果與原始觀點有衝突，請以「平衡觀點」的方式呈現，不要直接覆蓋或隱瞞，展現對複雜議題的細膩處理。
   - 如果搜尋結果對填補缺口沒有幫助，請**忽略該結果**，不要強行插入無關資訊。

2. **避免誤導 (Non-deceptive)**：
   - 清楚區分「事實」與「觀點」。
   - 引用來源時請精確，不要捏造不存在的關聯。

3. **實質幫助 (Helpfulness)**：
   - 整合的目標是提升讀者的理解深度，而非增加篇幅。
   - 保持語氣專業、直接且溫暖，避免過度說教或不必要的客套話。

4. **格式要求**：
   - 保持 Markdown 格式。
   - 流暢地重寫相關段落，使文章讀起來像是一氣呵成，而非拼貼之作。

請輸出整合後的完整內容："""

        try:
            response = await self.llm.acomplete(prompt)
            extended_content = response.text
            logger.info("Research integrated into content", original_length=len(content_extract.filtered_content), extended_length=len(extended_content))
            return extended_content.strip()

        except Exception as e:
            logger.warning("Failed to integrate research", error=str(e))
            # Return original content if integration fails
            return content_extract.filtered_content

