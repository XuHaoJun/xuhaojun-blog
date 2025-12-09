"""Content extension workflow step for research and knowledge gap filling."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from llama_index.core import PromptTemplate
from llama_index.core.workflow import Event, step

# Try to import LLM classes - they may be in separate packages
if TYPE_CHECKING:
    from llama_index.llms.ollama import Ollama
    from llama_index.llms.openai import OpenAI
else:
    try:
        from llama_index.llms.ollama import Ollama
    except ImportError:
        try:
            from llama_index_llms_ollama import Ollama
        except ImportError:
            Ollama = None

    try:
        from llama_index.llms.openai import OpenAI
    except ImportError:
        try:
            from llama_index_llms_openai import OpenAI
        except ImportError:
            OpenAI = None

from blog_agent.services.embedding import generate_embedding
from blog_agent.services.llm import get_llm
from blog_agent.services.tavily_service import get_tavily_service
from blog_agent.services.vector_store import VectorStore
from blog_agent.storage.models import ContentExtract
from blog_agent.workflows.extractor import ExtractEvent
from blog_agent.utils.errors import ExternalServiceError
from blog_agent.utils.logging import get_logger
from blog_agent.workflows.schemas import KnowledgeGapResponse

logger = get_logger(__name__)


class ExtendEvent(Event):
    """Event containing extended content."""

    content_extract: ContentExtract  # Updated with extended content
    conversation_log_id: str
    conversation_log_metadata: Optional[Dict[str, Any]] = None
    research_results: List[Dict[str, Any]] = []  # Research results from Tavily/KB
    knowledge_gaps: List[Dict[str, Any]] = []  # Identified knowledge gaps


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
        
        Returns:
            List of knowledge gaps, each with:
            - type: Type of gap (e.g., "missing_context", "unclear_concept", "missing_background")
            - description: Description of the gap
            - location: Where in the content the gap appears
            - query: Search query to find information about this gap
        """
        template_str = """請分析以下內容，找出缺少足夠上下文或細節的區域。

核心觀點：
{key_insights}

核心概念：
{core_concepts}

內容：
{content}

請找出以下類型的知識缺口：
1. 缺少必要的背景知識
2. 概念或術語未充分解釋
3. 缺少相關的技術細節
4. 缺少實際範例或應用場景
5. 缺少相關的歷史或發展脈絡"""

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

        # Build research context for LLM
        research_context = "\n\n研究補充資訊：\n"
        for result in research_results:
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

        prompt = f"""請將以下研究補充資訊自然地整合到原始內容中。

原始內容：
{content_extract.filtered_content}
{research_context}

要求：
1. 保持原始內容的結構和風格
2. 自然地將補充資訊融入相關段落
3. 不要重複已有的資訊
4. 使用 Markdown 格式
5. 在適當的地方添加引用或說明來源
6. 確保整合後的內容流暢連貫

請直接輸出整合後的完整內容，不要額外說明。"""

        try:
            response = await self.llm.acomplete(prompt)
            extended_content = response.text
            logger.info("Research integrated into content", original_length=len(content_extract.filtered_content), extended_length=len(extended_content))
            return extended_content.strip()

        except Exception as e:
            logger.warning("Failed to integrate research", error=str(e))
            # Return original content if integration fails
            return content_extract.filtered_content

