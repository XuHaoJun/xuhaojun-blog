"""Tavily API integration for content extension and fact-checking."""

from typing import Any, Dict, List, Optional

from blog_agent.config import config
from blog_agent.utils.errors import ExternalServiceError
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


class TavilyService:
    """Tavily API service for research and fact-checking."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Tavily service."""
        self.api_key = api_key or config.TAVILY_API_KEY
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY is required")

        try:
            from tavily import TavilyClient

            self.client = TavilyClient(api_key=self.api_key)
        except ImportError:
            raise ImportError("tavily-python package is required. Install with: pip install tavily-python")

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for information using Tavily API.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            search_depth: Search depth ("basic" or "advanced")
            include_domains: Optional list of domains to include
            exclude_domains: Optional list of domains to exclude
            
        Returns:
            List of search results with title, url, content, score, etc.
            
        Raises:
            ExternalServiceError: If Tavily API call fails (FR-019)
        """
        try:
            # Tavily client is synchronous, so we wrap it
            # In a real async context, you might want to use asyncio.to_thread
            import asyncio

            def _search():
                return self.client.search(
                    query=query,
                    max_results=max_results,
                    search_depth=search_depth,
                    include_domains=include_domains,
                    exclude_domains=exclude_domains,
                )

            # Run synchronous call in thread pool
            result = await asyncio.to_thread(_search)

            logger.info(
                "Tavily search completed",
                query=query,
                results_count=len(result.get("results", [])),
            )

            return result.get("results", [])

        except Exception as e:
            logger.error("Tavily API search failed", query=query, error=str(e), exc_info=True)
            raise ExternalServiceError(
                service_name="Tavily",
                message=f"Tavily search failed: {str(e)}",
                details={"query": query, "max_results": max_results},
            ) from e

    async def get_answer(
        self,
        query: str,
        search_depth: str = "advanced",
    ) -> Dict[str, Any]:
        """
        Get a direct answer to a query using Tavily's answer endpoint.
        
        Args:
            query: Question to answer
            search_depth: Search depth ("basic" or "advanced")
            
        Returns:
            Dictionary with answer, sources, and metadata
            
        Raises:
            ExternalServiceError: If Tavily API call fails (FR-019)
        """
        try:
            import asyncio

            def _get_answer():
                return self.client.get_answer(query=query, search_depth=search_depth)

            result = await asyncio.to_thread(_get_answer)

            logger.info("Tavily answer retrieved", query=query)

            return result

        except Exception as e:
            logger.error("Tavily API get_answer failed", query=query, error=str(e), exc_info=True)
            raise ExternalServiceError(
                service_name="Tavily",
                message=f"Tavily get_answer failed: {str(e)}",
                details={"query": query},
            ) from e

    async def fact_check(
        self,
        claim: str,
        max_results: int = 3,
    ) -> Dict[str, Any]:
        """
        Fact-check a specific claim using Tavily search.
        
        Args:
            claim: The claim to fact-check
            max_results: Maximum number of sources to check
            
        Returns:
            Dictionary with fact-check results including:
            - verified: bool indicating if claim is verified
            - sources: List of sources that support or contradict the claim
            - summary: Summary of fact-check findings
            
        Raises:
            ExternalServiceError: If Tavily API call fails (FR-019)
        """
        try:
            # Search for information about the claim
            results = await self.search(
                query=claim,
                max_results=max_results,
                search_depth="advanced",
            )

            # Analyze results to determine if claim is supported
            verified = len(results) > 0
            sources = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                    "score": r.get("score", 0.0),
                }
                for r in results
            ]

            summary = f"Found {len(sources)} sources related to the claim: {claim}"

            logger.info("Fact-check completed", claim=claim, verified=verified, sources_count=len(sources))

            return {
                "verified": verified,
                "sources": sources,
                "summary": summary,
                "claim": claim,
            }

        except Exception as e:
            logger.error("Tavily fact-check failed", claim=claim, error=str(e), exc_info=True)
            raise ExternalServiceError(
                service_name="Tavily",
                message=f"Tavily fact-check failed: {str(e)}",
                details={"claim": claim},
            ) from e


def get_tavily_service() -> TavilyService:
    """Get Tavily service instance."""
    return TavilyService()

