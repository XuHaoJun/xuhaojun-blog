"""PostgreSQL + pgvector integration for vector storage and search."""

from typing import List, Optional
from uuid import UUID

import asyncpg
from blog_agent.storage.db import get_db_connection
from blog_agent.utils.errors import ExternalServiceError
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Vector store using PostgreSQL + pgvector."""

    def __init__(self, dimension: int = 1536):
        """Initialize vector store with embedding dimension."""
        self.dimension = dimension

    async def create_embedding(
        self,
        entity_type: str,
        entity_id: UUID,
        content: str,
        embedding: List[float],
        metadata: Optional[dict] = None,
    ) -> UUID:
        """Create an embedding record."""
        try:
            async with get_db_connection() as conn:
                # Convert list to pgvector format
                embedding_str = "[" + ",".join(map(str, embedding)) + "]"

                record = await conn.fetchrow(
                    """
                    INSERT INTO embeddings (entity_type, entity_id, content, embedding, metadata)
                    VALUES ($1, $2, $3, $4::vector, $5)
                    RETURNING id
                    """,
                    entity_type,
                    entity_id,
                    content,
                    embedding_str,
                    metadata or {},
                )

                return record["id"]

        except Exception as e:
            logger.error("Failed to create embedding", error=str(e), exc_info=True)
            raise ExternalServiceError(
                service_name="VectorStore",
                message=f"Failed to create embedding: {str(e)}",
            ) from e

    async def search_similar(
        self,
        query_embedding: List[float],
        entity_type: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[dict]:
        """Search for similar embeddings."""
        try:
            async with get_db_connection() as conn:
                embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

                query = """
                    SELECT id, entity_type, entity_id, content, metadata,
                           1 - (embedding <=> $1::vector) as similarity
                    FROM embeddings
                    WHERE 1 - (embedding <=> $1::vector) >= $2
                """

                params = [embedding_str, threshold]

                if entity_type:
                    query += " AND entity_type = $3"
                    params.append(entity_type)
                    limit_param = "$4"
                else:
                    limit_param = "$3"

                query += f" ORDER BY embedding <=> $1::vector LIMIT {limit_param}"

                params.append(limit)

                records = await conn.fetch(query, *params)

                return [
                    {
                        "id": str(record["id"]),
                        "entity_type": record["entity_type"],
                        "entity_id": str(record["entity_id"]),
                        "content": record["content"],
                        "metadata": record["metadata"],
                        "similarity": float(record["similarity"]),
                    }
                    for record in records
                ]

        except Exception as e:
            logger.error("Failed to search embeddings", error=str(e), exc_info=True)
            raise ExternalServiceError(
                service_name="VectorStore",
                message=f"Failed to search embeddings: {str(e)}",
            ) from e

    async def query_knowledge_base(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        limit: int = 5,
        threshold: float = 0.7,
    ) -> List[dict]:
        """
        Query personal knowledge base (if available) (T068, FR-018).
        
        Args:
            query: Text query string
            query_embedding: Optional pre-computed embedding for the query
            limit: Maximum number of results
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            List of knowledge base results, empty if KB not available or no results.
            Each result contains: id, entity_type, entity_id, content, metadata, similarity
        """
        # If no embedding provided, we can't search
        # In a full implementation, we'd generate embedding here using an embedding service
        # For now, return empty list if no embedding provided (KB is optional)
        if query_embedding is None:
            logger.debug("Knowledge base query skipped - no embedding provided", query=query)
            return []

        try:
            # Search for similar content in the knowledge base
            results = await self.search_similar(
                query_embedding=query_embedding,
                entity_type=None,  # Search across all entity types
                limit=limit,
                threshold=threshold,
            )

            logger.info(
                "Knowledge base query completed",
                query=query,
                results_count=len(results),
            )

            return results

        except Exception as e:
            logger.warning("Knowledge base query failed", query=query, error=str(e))
            # Return empty list on failure (KB is optional, FR-018)
            return []

