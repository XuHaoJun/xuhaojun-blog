"""Repository pattern for data persistence."""

import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Generic, List, Optional, TypeVar
from uuid import UUID, uuid4

import asyncpg

from blog_agent.storage.db import get_db_connection
from blog_agent.storage.models import (
    BlogPost,
    ContentBlock,
    ContentExtract,
    ConversationLog,
    ConversationMessage,
    ProcessingHistory,
    PromptCandidate,
    PromptSuggestion,
    ReviewFindings,
    TavilySearchCache,
)
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Base repository interface."""

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def list(self, limit: int = 100, offset: int = 0) -> List[T]:
        """List entities."""
        pass


class ConversationLogRepository(BaseRepository[ConversationLog]):
    """Repository for conversation logs."""

    @staticmethod
    def _json_serialize_datetime(obj):
        """Recursively convert datetime objects to ISO format strings for JSON serialization."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: ConversationLogRepository._json_serialize_datetime(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [ConversationLogRepository._json_serialize_datetime(item) for item in obj]
        else:
            return obj

    async def create(self, entity: ConversationLog) -> ConversationLog:
        """Create a new conversation log."""
        async with get_db_connection() as conn:
            entity_id = entity.id or uuid4()
            now = datetime.utcnow()

            # Serialize parsed_content with datetime handling
            serialized_parsed_content = self._json_serialize_datetime(entity.parsed_content)
            serialized_metadata = self._json_serialize_datetime(entity.metadata) if entity.metadata else None

            await conn.execute(
                """
                INSERT INTO conversation_logs (
                    id, file_path, file_format, raw_content, parsed_content,
                    content_hash, metadata, language, message_count, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """,
                entity_id,
                entity.file_path,
                entity.file_format,
                entity.raw_content,
                json.dumps(serialized_parsed_content),
                entity.content_hash,
                json.dumps(serialized_metadata) if serialized_metadata else None,
                entity.language,
                entity.message_count,
                now,
                now,
            )

            entity.id = entity_id
            entity.created_at = now
            entity.updated_at = now

            return entity

    async def get_by_id(self, entity_id: UUID) -> Optional[ConversationLog]:
        """Get conversation log by ID."""
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, file_path, file_format, raw_content, parsed_content,
                       content_hash, metadata, language, message_count, created_at, updated_at
                FROM conversation_logs
                WHERE id = $1
                """,
                entity_id,
            )

            if not row:
                return None

            return ConversationLog(
                id=row["id"],
                file_path=row["file_path"],
                file_format=row["file_format"],
                raw_content=row["raw_content"],
                parsed_content=json.loads(row["parsed_content"]),
                content_hash=row["content_hash"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                language=row["language"],
                message_count=row["message_count"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def list(self, limit: int = 100, offset: int = 0) -> List[ConversationLog]:
        """List conversation logs."""
        async with get_db_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, file_path, file_format, raw_content, parsed_content,
                       content_hash, metadata, language, message_count, created_at, updated_at
                FROM conversation_logs
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )

            return [
                ConversationLog(
                    id=row["id"],
                    file_path=row["file_path"],
                    file_format=row["file_format"],
                    raw_content=row["raw_content"],
                    parsed_content=json.loads(row["parsed_content"]),
                    content_hash=row["content_hash"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                    language=row["language"],
                    message_count=row["message_count"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    async def get_by_file_path(self, file_path: str) -> Optional[ConversationLog]:
        """
        Get conversation log by file path (most recent if multiple exist).
        
        Args:
            file_path: Path to the conversation log file
        
        Returns:
            Most recent ConversationLog with matching file_path, or None if not found
        """
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, file_path, file_format, raw_content, parsed_content,
                       content_hash, metadata, language, message_count, created_at, updated_at
                FROM conversation_logs
                WHERE file_path = $1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                file_path,
            )

            if not row:
                return None

            return ConversationLog(
                id=row["id"],
                file_path=row["file_path"],
                file_format=row["file_format"],
                raw_content=row["raw_content"],
                parsed_content=json.loads(row["parsed_content"]),
                content_hash=row["content_hash"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                language=row["language"],
                message_count=row["message_count"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def get_by_file_path_and_hash(
        self, file_path: str, content_hash: str
    ) -> Optional[ConversationLog]:
        """
        Get conversation log by file path and content hash (FR-031, FR-032, FR-033).
        
        This method is used to check if a file with the same content has already been processed.
        
        Args:
            file_path: Path to the conversation log file
            content_hash: SHA-256 hash of the file content
        
        Returns:
            ConversationLog with matching file_path and content_hash, or None if not found
        """
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, file_path, file_format, raw_content, parsed_content,
                       content_hash, metadata, language, message_count, created_at, updated_at
                FROM conversation_logs
                WHERE file_path = $1 AND content_hash = $2
                ORDER BY created_at DESC
                LIMIT 1
                """,
                file_path,
                content_hash,
            )

            if not row:
                return None

            return ConversationLog(
                id=row["id"],
                file_path=row["file_path"],
                file_format=row["file_format"],
                raw_content=row["raw_content"],
                parsed_content=json.loads(row["parsed_content"]),
                content_hash=row["content_hash"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                language=row["language"],
                message_count=row["message_count"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def extract_conversation_messages(self, conversation_log: ConversationLog) -> List[ConversationMessage]:
        """
        從 conversation_log 的 parsed_content 中提取對話訊息。

        Args:
            conversation_log: ConversationLog 物件

        Returns:
            ConversationMessage 列表
        """
        messages = []
        parsed_content = conversation_log.parsed_content

        # parsed_content 應該包含 messages 陣列
        if isinstance(parsed_content, dict) and "messages" in parsed_content:
            messages_list = parsed_content["messages"]
            if not isinstance(messages_list, list):
                return messages

            for msg_data in messages_list:
                try:
                    # Validate that msg_data is a dictionary
                    if not isinstance(msg_data, dict):
                        continue

                    # 處理時間戳記
                    timestamp = None
                    if "timestamp" in msg_data and msg_data["timestamp"]:
                        if isinstance(msg_data["timestamp"], str):
                            try:
                                timestamp = datetime.fromisoformat(msg_data["timestamp"].replace("Z", "+00:00"))
                            except (ValueError, AttributeError):
                                timestamp = None
                        elif isinstance(msg_data["timestamp"], datetime):
                            timestamp = msg_data["timestamp"]

                    message = ConversationMessage(
                        role=msg_data.get("role", "user"),
                        content=msg_data.get("content", ""),
                        timestamp=timestamp,
                    )
                    messages.append(message)
                except Exception:
                    # Skip malformed messages but continue processing others
                    continue

        return messages


class BlogPostRepository(BaseRepository[BlogPost]):
    """Repository for blog posts."""

    async def create(self, entity: BlogPost) -> BlogPost:
        """Create a new blog post."""
        async with get_db_connection() as conn:
            entity_id = entity.id or uuid4()
            now = datetime.utcnow()

            await conn.execute(
                """
                INSERT INTO blog_posts (
                    id, conversation_log_id, title, summary, tags, content,
                    metadata, status, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                entity_id,
                entity.conversation_log_id,
                entity.title,
                entity.summary,
                entity.tags,
                entity.content,
                json.dumps(entity.metadata) if entity.metadata else None,
                entity.status,
                now,
                now,
            )

            entity.id = entity_id
            entity.created_at = now
            entity.updated_at = now

            return entity

    async def get_by_id(self, entity_id: UUID) -> Optional[BlogPost]:
        """Get blog post by ID."""
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, conversation_log_id, title, summary, tags, content,
                       metadata, status, created_at, updated_at
                FROM blog_posts
                WHERE id = $1
                """,
                entity_id,
            )

            if not row:
                return None

            return BlogPost(
                id=row["id"],
                conversation_log_id=row["conversation_log_id"],
                title=row["title"],
                summary=row["summary"],
                tags=list(row["tags"]) if row["tags"] else [],
                content=row["content"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def list(self, limit: int = 100, offset: int = 0) -> List[BlogPost]:
        """List blog posts."""
        async with get_db_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, conversation_log_id, title, summary, tags, content,
                       metadata, status, created_at, updated_at
                FROM blog_posts
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )

            return [
                BlogPost(
                    id=row["id"],
                    conversation_log_id=row["conversation_log_id"],
                    title=row["title"],
                    summary=row["summary"],
                    tags=list(row["tags"]) if row["tags"] else [],
                    content=row["content"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                    status=row["status"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]


class ProcessingHistoryRepository(BaseRepository[ProcessingHistory]):
    """Repository for processing history."""

    async def create(self, entity: ProcessingHistory) -> ProcessingHistory:
        """Create a new processing history record."""
        async with get_db_connection() as conn:
            entity_id = entity.id or uuid4()
            now = datetime.utcnow()

            await conn.execute(
                """
                INSERT INTO processing_history (
                    id, conversation_log_id, blog_post_id, status, error_message,
                    processing_steps, started_at, completed_at, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                entity_id,
                entity.conversation_log_id,
                entity.blog_post_id,
                entity.status,
                entity.error_message,
                json.dumps(entity.processing_steps) if entity.processing_steps else None,
                entity.started_at or now,
                entity.completed_at,
                now,
            )

            entity.id = entity_id
            entity.started_at = entity.started_at or now
            entity.created_at = now

            return entity

    async def get_by_id(self, entity_id: UUID) -> Optional[ProcessingHistory]:
        """Get processing history by ID."""
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, conversation_log_id, blog_post_id, status, error_message,
                       processing_steps, started_at, completed_at, created_at
                FROM processing_history
                WHERE id = $1
                """,
                entity_id,
            )

            if not row:
                return None

            return ProcessingHistory(
                id=row["id"],
                conversation_log_id=row["conversation_log_id"],
                blog_post_id=row["blog_post_id"],
                status=row["status"],
                error_message=row["error_message"],
                processing_steps=json.loads(row["processing_steps"])
                if row["processing_steps"]
                else None,
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                created_at=row["created_at"],
            )

    async def list(self, limit: int = 100, offset: int = 0) -> List[ProcessingHistory]:
        """List processing history records."""
        async with get_db_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, conversation_log_id, blog_post_id, status, error_message,
                       processing_steps, started_at, completed_at, created_at
                FROM processing_history
                ORDER BY started_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )

            return [
                ProcessingHistory(
                    id=row["id"],
                    conversation_log_id=row["conversation_log_id"],
                    blog_post_id=row["blog_post_id"],
                    status=row["status"],
                    error_message=row["error_message"],
                    processing_steps=json.loads(row["processing_steps"])
                    if row["processing_steps"]
                    else None,
                    started_at=row["started_at"],
                    completed_at=row["completed_at"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    async def update(self, entity: ProcessingHistory) -> ProcessingHistory:
        """Update processing history record."""
        async with get_db_connection() as conn:
            now = datetime.utcnow()

            await conn.execute(
                """
                UPDATE processing_history
                SET blog_post_id = $1, status = $2, error_message = $3,
                    processing_steps = $4, completed_at = $5
                WHERE id = $6
                """,
                entity.blog_post_id,
                entity.status,
                entity.error_message,
                json.dumps(entity.processing_steps) if entity.processing_steps else None,
                entity.completed_at or now,
                entity.id,
            )

            entity.completed_at = entity.completed_at or now

            return entity


class ContentExtractRepository(BaseRepository[ContentExtract]):
    """Repository for content extracts."""

    async def create(self, entity: ContentExtract) -> ContentExtract:
        """Create a new content extract."""
        raise NotImplementedError

    async def get_by_id(self, entity_id: UUID) -> Optional[ContentExtract]:
        """Get content extract by ID."""
        raise NotImplementedError

    async def list(self, limit: int = 100, offset: int = 0) -> List[ContentExtract]:
        """List content extracts."""
        raise NotImplementedError


class ReviewFindingsRepository(BaseRepository[ReviewFindings]):
    """Repository for review findings."""

    async def create(self, entity: ReviewFindings) -> ReviewFindings:
        """Create a new review finding."""
        async with get_db_connection() as conn:
            entity_id = entity.id or uuid4()
            now = datetime.utcnow()

            await conn.execute(
                """
                INSERT INTO review_findings (
                    id, content_extract_id, issues, improvement_suggestions,
                    fact_checking_needs, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                entity_id,
                entity.content_extract_id,
                json.dumps(entity.issues),
                entity.improvement_suggestions,
                entity.fact_checking_needs,
                now,
            )

            entity.id = entity_id
            entity.created_at = now

            return entity

    async def get_by_id(self, entity_id: UUID) -> Optional[ReviewFindings]:
        """Get review finding by ID."""
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, content_extract_id, issues, improvement_suggestions,
                       fact_checking_needs, created_at
                FROM review_findings
                WHERE id = $1
                """,
                entity_id,
            )

            if not row:
                return None

            return ReviewFindings(
                id=row["id"],
                content_extract_id=row["content_extract_id"],
                issues=json.loads(row["issues"]),
                improvement_suggestions=list(row["improvement_suggestions"])
                if row["improvement_suggestions"]
                else [],
                fact_checking_needs=list(row["fact_checking_needs"])
                if row["fact_checking_needs"]
                else [],
                created_at=row["created_at"],
            )

    async def list(self, limit: int = 100, offset: int = 0) -> List[ReviewFindings]:
        """List review findings."""
        async with get_db_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, content_extract_id, issues, improvement_suggestions,
                       fact_checking_needs, created_at
                FROM review_findings
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )

            return [
                ReviewFindings(
                    id=row["id"],
                    content_extract_id=row["content_extract_id"],
                    issues=json.loads(row["issues"]),
                    improvement_suggestions=list(row["improvement_suggestions"])
                    if row["improvement_suggestions"]
                    else [],
                    fact_checking_needs=list(row["fact_checking_needs"])
                    if row["fact_checking_needs"]
                    else [],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    async def get_by_content_extract_id(
        self, content_extract_id: UUID
    ) -> Optional[ReviewFindings]:
        """Get review finding by content extract ID."""
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, content_extract_id, issues, improvement_suggestions,
                       fact_checking_needs, created_at
                FROM review_findings
                WHERE content_extract_id = $1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                content_extract_id,
            )

            if not row:
                return None

            return ReviewFindings(
                id=row["id"],
                content_extract_id=row["content_extract_id"],
                issues=json.loads(row["issues"]),
                improvement_suggestions=list(row["improvement_suggestions"])
                if row["improvement_suggestions"]
                else [],
                fact_checking_needs=list(row["fact_checking_needs"])
                if row["fact_checking_needs"]
                else [],
                created_at=row["created_at"],
            )


class PromptSuggestionRepository(BaseRepository[PromptSuggestion]):
    """Repository for prompt suggestions."""

    async def create(self, entity: PromptSuggestion) -> PromptSuggestion:
        """Create a new prompt suggestion."""
        async with get_db_connection() as conn:
            entity_id = entity.id or uuid4()
            now = datetime.utcnow()

            # Convert PromptCandidate list to dict list for JSONB
            # asyncpg will automatically convert Python dict/list to JSONB
            candidates_data = [
                candidate.model_dump() for candidate in entity.better_candidates
            ]

            await conn.execute(
                """
                INSERT INTO prompt_suggestions (
                    id, conversation_log_id, original_prompt, analysis,
                    better_candidates, reasoning, expected_effect, created_at
                ) VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8)
                """,
                entity_id,
                entity.conversation_log_id,
                entity.original_prompt,
                entity.analysis,
                json.dumps(candidates_data),  # Convert to JSON string for JSONB
                entity.reasoning,
                entity.expected_effect,
                now,
            )

            entity.id = entity_id
            entity.created_at = now

            return entity

    async def get_by_id(self, entity_id: UUID) -> Optional[PromptSuggestion]:
        """Get prompt suggestion by ID."""
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, conversation_log_id, original_prompt, analysis,
                       better_candidates, reasoning, expected_effect, created_at
                FROM prompt_suggestions
                WHERE id = $1
                """,
                entity_id,
            )

            if not row:
                return None

            # Convert JSONB to PromptCandidate list
            candidates_data = (
                json.loads(row["better_candidates"])
                if isinstance(row["better_candidates"], str)
                else row["better_candidates"]
            )
            candidates = [
                PromptCandidate(**candidate) for candidate in candidates_data
            ]

            return PromptSuggestion(
                id=row["id"],
                conversation_log_id=row["conversation_log_id"],
                original_prompt=row["original_prompt"],
                analysis=row["analysis"],
                better_candidates=candidates,
                reasoning=row["reasoning"],
                expected_effect=row.get("expected_effect"),
                created_at=row["created_at"],
            )

    async def list(self, limit: int = 100, offset: int = 0) -> List[PromptSuggestion]:
        """List prompt suggestions."""
        async with get_db_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, conversation_log_id, original_prompt, analysis,
                       better_candidates, reasoning, expected_effect, created_at
                FROM prompt_suggestions
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )

            result = []
            for row in rows:
                # Convert JSONB to PromptCandidate list
                candidates_data = (
                    json.loads(row["better_candidates"])
                    if isinstance(row["better_candidates"], str)
                    else row["better_candidates"]
                )
                candidates = [
                    PromptCandidate(**candidate) for candidate in candidates_data
                ]

                result.append(
                    PromptSuggestion(
                        id=row["id"],
                        conversation_log_id=row["conversation_log_id"],
                        original_prompt=row["original_prompt"],
                        analysis=row["analysis"],
                        better_candidates=candidates,
                        reasoning=row["reasoning"],
                        expected_effect=row.get("expected_effect"),
                        created_at=row["created_at"],
                    )
                )
            return result

    async def get_by_conversation_log_id(
        self, conversation_log_id: UUID
    ) -> Optional[PromptSuggestion]:
        """Get prompt suggestion by conversation log ID."""
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, conversation_log_id, original_prompt, analysis,
                       better_candidates, reasoning, expected_effect, created_at
                FROM prompt_suggestions
                WHERE conversation_log_id = $1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                conversation_log_id,
            )

            if not row:
                return None

            # Convert JSONB to PromptCandidate list
            candidates_data = (
                json.loads(row["better_candidates"])
                if isinstance(row["better_candidates"], str)
                else row["better_candidates"]
            )
            candidates = [
                PromptCandidate(**candidate) for candidate in candidates_data
            ]

            return PromptSuggestion(
                id=row["id"],
                conversation_log_id=row["conversation_log_id"],
                original_prompt=row["original_prompt"],
                analysis=row["analysis"],
                better_candidates=candidates,
                reasoning=row["reasoning"],
                expected_effect=row.get("expected_effect"),
                created_at=row["created_at"],
            )

    async def get_all_by_conversation_log_id(
        self, conversation_log_id: UUID
    ) -> List[PromptSuggestion]:
        """Get all prompt suggestions by conversation log ID."""
        async with get_db_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, conversation_log_id, original_prompt, analysis,
                       better_candidates, reasoning, expected_effect, created_at
                FROM prompt_suggestions
                WHERE conversation_log_id = $1
                ORDER BY created_at DESC
                """,
                conversation_log_id,
            )

            result = []
            for row in rows:
                # Convert JSONB to PromptCandidate list
                candidates_data = (
                    json.loads(row["better_candidates"])
                    if isinstance(row["better_candidates"], str)
                    else row["better_candidates"]
                )
                candidates = [
                    PromptCandidate(**candidate) for candidate in candidates_data
                ]

                result.append(
                    PromptSuggestion(
                        id=row["id"],
                        conversation_log_id=row["conversation_log_id"],
                        original_prompt=row["original_prompt"],
                        analysis=row["analysis"],
                        better_candidates=candidates,
                        reasoning=row["reasoning"],
                        expected_effect=row.get("expected_effect"),
                        created_at=row["created_at"],
                    )
                )
            return result


class ContentBlockRepository(BaseRepository[ContentBlock]):
    """Repository for content blocks."""

    async def create(self, entity: ContentBlock) -> ContentBlock:
        """Create a new content block."""
        async with get_db_connection() as conn:
            entity_id = entity.id or uuid4()
            now = datetime.utcnow()

            await conn.execute(
                """
                INSERT INTO content_blocks (
                    id, blog_post_id, block_order, text, prompt_suggestion_id, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                entity_id,
                entity.blog_post_id,
                entity.block_order,
                entity.text,
                entity.prompt_suggestion_id,
                now,
            )

            entity.id = entity_id
            entity.created_at = now

            return entity

    async def get_by_id(self, entity_id: UUID) -> Optional[ContentBlock]:
        """Get content block by ID."""
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, blog_post_id, block_order, text, prompt_suggestion_id, created_at
                FROM content_blocks
                WHERE id = $1
                """,
                entity_id,
            )

            if not row:
                return None

            return ContentBlock(
                id=row["id"],
                blog_post_id=row["blog_post_id"],
                block_order=row["block_order"],
                text=row["text"],
                prompt_suggestion_id=row["prompt_suggestion_id"],
                created_at=row["created_at"],
            )

    async def list(self, limit: int = 100, offset: int = 0) -> List[ContentBlock]:
        """List content blocks."""
        async with get_db_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, blog_post_id, block_order, text, prompt_suggestion_id, created_at
                FROM content_blocks
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )

            return [
                ContentBlock(
                    id=row["id"],
                    blog_post_id=row["blog_post_id"],
                    block_order=row["block_order"],
                    text=row["text"],
                    prompt_suggestion_id=row["prompt_suggestion_id"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    async def get_by_blog_post_id(
        self, blog_post_id: UUID
    ) -> List[ContentBlock]:
        """Get all content blocks for a blog post, ordered by block_order."""
        async with get_db_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, blog_post_id, block_order, text, prompt_suggestion_id, created_at
                FROM content_blocks
                WHERE blog_post_id = $1
                ORDER BY block_order ASC
                """,
                blog_post_id,
            )

            return [
                ContentBlock(
                    id=row["id"],
                    blog_post_id=row["blog_post_id"],
                    block_order=row["block_order"],
                    text=row["text"],
                    prompt_suggestion_id=row["prompt_suggestion_id"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    async def get_by_prompt_suggestion_id(
        self, prompt_suggestion_id: UUID
    ) -> List[ContentBlock]:
        """Get all content blocks associated with a prompt suggestion."""
        async with get_db_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, blog_post_id, block_order, text, prompt_suggestion_id, created_at
                FROM content_blocks
                WHERE prompt_suggestion_id = $1
                ORDER BY block_order ASC
                """,
                prompt_suggestion_id,
            )

            return [
                ContentBlock(
                    id=row["id"],
                    blog_post_id=row["blog_post_id"],
                    block_order=row["block_order"],
                    text=row["text"],
                    prompt_suggestion_id=row["prompt_suggestion_id"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]


class TavilySearchCacheRepository(BaseRepository[TavilySearchCache]):
    """Repository for Tavily search cache."""

    async def create(self, entity: TavilySearchCache) -> TavilySearchCache:
        """Create a new cache entry."""
        async with get_db_connection() as conn:
            entity_id = entity.id or uuid4()
            now = datetime.utcnow()

            await conn.execute(
                """
                INSERT INTO tavily_search_cache (
                    id, query, search_depth, max_results, include_domains,
                    exclude_domains, results, expires_at, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                entity_id,
                entity.query,
                entity.search_depth,
                entity.max_results,
                entity.include_domains,
                entity.exclude_domains,
                json.dumps(entity.results),
                entity.expires_at,
                now,
                now,
            )

            entity.id = entity_id
            entity.created_at = now
            entity.updated_at = now

            return entity

    async def get_by_id(self, entity_id: UUID) -> Optional[TavilySearchCache]:
        """Get cache entry by ID."""
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, query, search_depth, max_results, include_domains,
                       exclude_domains, results, expires_at, created_at, updated_at
                FROM tavily_search_cache
                WHERE id = $1
                """,
                entity_id,
            )

            if not row:
                return None

            return TavilySearchCache(
                id=row["id"],
                query=row["query"],
                search_depth=row["search_depth"],
                max_results=row["max_results"],
                include_domains=list(row["include_domains"]) if row["include_domains"] else [],
                exclude_domains=list(row["exclude_domains"]) if row["exclude_domains"] else [],
                results=json.loads(row["results"]),
                expires_at=row["expires_at"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def list(self, limit: int = 100, offset: int = 0) -> List[TavilySearchCache]:
        """List cache entries."""
        async with get_db_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, query, search_depth, max_results, include_domains,
                       exclude_domains, results, expires_at, created_at, updated_at
                FROM tavily_search_cache
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )

            return [
                TavilySearchCache(
                    id=row["id"],
                    query=row["query"],
                    search_depth=row["search_depth"],
                    max_results=row["max_results"],
                    include_domains=list(row["include_domains"]) if row["include_domains"] else [],
                    exclude_domains=list(row["exclude_domains"]) if row["exclude_domains"] else [],
                    results=json.loads(row["results"]),
                    expires_at=row["expires_at"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    async def get_cached_search(
        self,
        query: str,
        search_depth: str,
        max_results: int,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> Optional[TavilySearchCache]:
        """
        Get non-expired cached search results.
        """
        async with get_db_connection() as conn:
            # Handle list/None comparison in SQL
            # Note: Postgres unique index/constraint treats NULL as distinct from empty array.
            # We'll normalize to empty arrays for the query if they are None.
            inc_domains = include_domains or []
            exc_domains = exclude_domains or []

            row = await conn.fetchrow(
                """
                SELECT id, query, search_depth, max_results, include_domains,
                       exclude_domains, results, expires_at, created_at, updated_at
                FROM tavily_search_cache
                WHERE query = $1 
                  AND search_depth = $2 
                  AND max_results = $3 
                  AND COALESCE(include_domains, '{}') = $4
                  AND COALESCE(exclude_domains, '{}') = $5
                  AND expires_at > now()
                ORDER BY created_at DESC
                LIMIT 1
                """,
                query,
                search_depth,
                max_results,
                inc_domains,
                exc_domains,
            )

            if not row:
                return None

            return TavilySearchCache(
                id=row["id"],
                query=row["query"],
                search_depth=row["search_depth"],
                max_results=row["max_results"],
                include_domains=list(row["include_domains"]) if row["include_domains"] else [],
                exclude_domains=list(row["exclude_domains"]) if row["exclude_domains"] else [],
                results=json.loads(row["results"]),
                expires_at=row["expires_at"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def create_or_update(self, entity: TavilySearchCache) -> TavilySearchCache:
        """
        Create or update a cache entry (upsert based on search parameters).
        """
        async with get_db_connection() as conn:
            entity_id = entity.id or uuid4()
            now = datetime.utcnow()
            
            inc_domains = entity.include_domains or []
            exc_domains = entity.exclude_domains or []

            await conn.execute(
                """
                INSERT INTO tavily_search_cache (
                    id, query, search_depth, max_results, include_domains,
                    exclude_domains, results, expires_at, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (query, search_depth, max_results, include_domains, exclude_domains)
                DO UPDATE SET
                    results = EXCLUDED.results,
                    expires_at = EXCLUDED.expires_at,
                    updated_at = EXCLUDED.updated_at
                """,
                entity_id,
                entity.query,
                entity.search_depth,
                entity.max_results,
                inc_domains,
                exc_domains,
                json.dumps(entity.results),
                entity.expires_at,
                now,
                now,
            )

            entity.id = entity_id
            entity.created_at = now
            entity.updated_at = now

            return entity

