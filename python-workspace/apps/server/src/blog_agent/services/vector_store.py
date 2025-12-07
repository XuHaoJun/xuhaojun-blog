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
        query_embedding: List[float],
        limit: int = 5,
    ) -> List[dict]:
        """Query personal knowledge base (if available)."""
        # This will be enhanced in US3 when knowledge base integration is added
        return await self.search_similar(
            query_embedding=query_embedding,
            entity_type=None,
            limit=limit,
        )

