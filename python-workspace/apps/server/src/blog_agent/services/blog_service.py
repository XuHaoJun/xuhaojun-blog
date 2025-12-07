"""Blog processing service."""

import traceback
from uuid import UUID, uuid4

from blog_agent.parsers import ParserFactory
from blog_agent.parsers.role_inference import RoleInference
from blog_agent.storage.models import (
    BlogPost,
    ConversationLog,
    Message,
    ProcessingHistory,
)
from blog_agent.storage.repository import (
    BlogPostRepository,
    ConversationLogRepository,
    ProcessingHistoryRepository,
)
from blog_agent.utils.errors import ProcessingError
from blog_agent.utils.hash_utils import calculate_sha256_hash
from blog_agent.utils.logging import get_logger
from blog_agent.workflows.blog_workflow import BlogWorkflow

logger = get_logger(__name__)


class BlogService:
    """Service for processing conversations into blog posts."""

    def __init__(self):
        """Initialize blog service."""
        self.conversation_repo = ConversationLogRepository()
        self.blog_repo = BlogPostRepository()
        self.history_repo = ProcessingHistoryRepository()
        self.workflow = BlogWorkflow()

    async def process_conversation(
        self,
        file_path: str,
        file_content: bytes,
        file_format: str,
        metadata: dict = None,
        force: bool = False,
    ) -> tuple[ProcessingHistory, BlogPost]:
        """
        Process conversation log and generate blog post.
        
        Args:
            file_path: Path to the conversation log file
            file_content: File content as bytes
            file_format: File format (markdown, json, csv, text)
            metadata: Optional metadata dictionary
            force: If True, force processing even if content hasn't changed (FR-034)
        
        Returns:
            Tuple of (ProcessingHistory, BlogPost)
        
        Raises:
            ProcessingError: If processing fails or file unchanged (unless force=True)
        """
        processing_id = uuid4()
        conversation_log_id = None
        blog_post_id = None

        try:
            # Calculate content hash (FR-031)
            content_str = file_content.decode("utf-8")
            content_hash = calculate_sha256_hash(content_str)
            
            # Check if file with same path and hash already exists (FR-032, FR-033)
            existing_log = await self.conversation_repo.get_by_file_path_and_hash(
                file_path, content_hash
            )
            
            if existing_log and not force:
                # File content hasn't changed, skip processing (FR-032)
                logger.info(
                    "File content unchanged, skipping processing",
                    file_path=file_path,
                    content_hash=content_hash,
                    existing_log_id=str(existing_log.id),
                )
                
                # Find existing blog post for this conversation log
                # Query database directly for efficiency
                from blog_agent.storage.db import get_db_connection
                async with get_db_connection() as conn:
                    row = await conn.fetchrow(
                        """
                        SELECT id, conversation_log_id, title, summary, tags, content,
                               metadata, status, created_at, updated_at
                        FROM blog_posts
                        WHERE conversation_log_id = $1
                        ORDER BY created_at DESC
                        LIMIT 1
                        """,
                        existing_log.id,
                    )
                    
                    if row:
                        import json
                        existing_blog_post = BlogPost(
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
                    else:
                        existing_blog_post = None
                
                # Create a processing history record indicating skipped
                processing = ProcessingHistory(
                    id=processing_id,
                    conversation_log_id=existing_log.id,
                    blog_post_id=existing_blog_post.id if existing_blog_post else None,
                    status="completed",
                    processing_steps={"skipped": True, "reason": "content_unchanged"},
                )
                processing = await self.history_repo.create(processing)
                
                if existing_blog_post:
                    return processing, existing_blog_post
                else:
                    raise ProcessingError(
                        step="process_conversation",
                        message="File content unchanged and no existing blog post found",
                        details={
                            "file_path": file_path,
                            "content_hash": content_hash,
                            "existing_log_id": str(existing_log.id),
                        },
                    )
            
            # Check if file path exists but hash is different (FR-033)
            existing_log_by_path = await self.conversation_repo.get_by_file_path(file_path)
            if existing_log_by_path and existing_log_by_path.content_hash != content_hash:
                logger.info(
                    "File content changed, will regenerate",
                    file_path=file_path,
                    old_hash=existing_log_by_path.content_hash,
                    new_hash=content_hash,
                )
                # Continue with processing to regenerate blog post
            
            # Create processing history
            processing = ProcessingHistory(
                id=processing_id,
                conversation_log_id=UUID(int=0),  # Temporary, will update
                status="processing",
            )
            processing = await self.history_repo.create(processing)

            # Parse conversation log
            parser = ParserFactory.create_parser(file_format)
            conversation_log = parser.parse(content_str, file_path)
            
            # Set content hash on conversation log
            conversation_log.content_hash = content_hash

            # Apply role inference if needed (FR-028)
            if any(not msg.role or msg.role not in ["user", "assistant", "system"] for msg in conversation_log.parsed_content.get("messages", [])):
                messages, uncertainties = RoleInference.infer_roles_with_uncertainty(
                    [Message(**msg) for msg in conversation_log.parsed_content["messages"]]
                )
                conversation_log.parsed_content["messages"] = [msg.model_dump() for msg in messages]
                if any(uncertainties):
                    logger.warning("Some message roles inferred with uncertainty", uncertainties=uncertainties)

            # Save conversation log
            conversation_log = await self.conversation_repo.create(conversation_log)
            conversation_log_id = conversation_log.id

            # Update processing history
            processing.conversation_log_id = conversation_log_id
            processing = await self.history_repo.update(processing)

            # Run workflow
            messages = [
                Message(**msg) for msg in conversation_log.parsed_content["messages"]
            ]

            # Use workflow to process
            from blog_agent.workflows.blog_workflow import BlogWorkflowStartEvent
            from blog_agent.workflows.extractor import ContentExtractor, ExtractStartEvent
            from blog_agent.workflows.editor import BlogEditor

            start_event = BlogWorkflowStartEvent(
                messages=messages,
                conversation_log_id=str(conversation_log_id),
            )

            # Run workflow steps
            extractor = ContentExtractor()
            editor = BlogEditor()

            # Extract metadata from conversation log (FR-015: preserve timestamps, participants)
            conversation_log_metadata = self._extract_conversation_metadata(conversation_log)
            
            # Extract
            extract_start = ExtractStartEvent(
                messages=messages,
                conversation_log_id=str(conversation_log_id),
                conversation_log_metadata=conversation_log_metadata,
            )
            extract_event = await extractor.extract(extract_start)

            # Save content extract (optional, for tracking)
            # content_extract = extract_event.content_extract
            # content_extract.conversation_log_id = conversation_log_id
            # await ContentExtractRepository().create(content_extract)

            # Edit
            edit_event = await editor.edit(extract_event)

            # Save blog post
            blog_post = edit_event.blog_post
            blog_post.conversation_log_id = conversation_log_id
            blog_post = await self.blog_repo.create(blog_post)
            blog_post_id = blog_post.id

            # Update processing history
            processing.blog_post_id = blog_post_id
            processing.status = "completed"
            processing = await self.history_repo.update(processing)

            return processing, blog_post

        except Exception as e:
            logger.error(
                "Processing failed",
                error=str(e),
                stack_trace=traceback.format_exc(),
                exc_info=True,
            )

            # Update processing history with error (FR-024)
            error_message = f"{str(e)}\n\nStack Trace:\n{traceback.format_exc()}"
            processing.status = "failed"
            processing.error_message = error_message
            if conversation_log_id:
                processing.conversation_log_id = conversation_log_id
            await self.history_repo.update(processing)

            raise ProcessingError(
                step="process_conversation",
                message=str(e),
                details={"processing_id": str(processing_id), "stack_trace": traceback.format_exc()},
            ) from e

    def _extract_conversation_metadata(self, conversation_log: ConversationLog) -> dict:
        """
        Extract metadata from conversation log (timestamps, participants, etc.) (FR-015).
        
        Args:
            conversation_log: The conversation log to extract metadata from
            
        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {}
        
        # Extract timestamps from messages
        messages = conversation_log.parsed_content.get("messages", [])
        timestamps = []
        for msg_data in messages:
            if isinstance(msg_data, dict) and "timestamp" in msg_data:
                timestamp = msg_data["timestamp"]
                if timestamp:
                    timestamps.append(timestamp)
        
        if timestamps:
            metadata["timestamps"] = {
                "first": min(timestamps) if timestamps else None,
                "last": max(timestamps) if timestamps else None,
                "count": len(timestamps),
            }
        
        # Extract participants (unique roles)
        participants = set()
        for msg_data in messages:
            if isinstance(msg_data, dict) and "role" in msg_data:
                role = msg_data["role"]
                if role:
                    participants.add(role)
        
        if participants:
            metadata["participants"] = list(participants)
        
        # Include existing metadata from conversation log
        if conversation_log.metadata:
            metadata.update(conversation_log.metadata)
        
        # Add language if available
        if conversation_log.language:
            metadata["language"] = conversation_log.language
        
        # Add message count
        if conversation_log.message_count:
            metadata["message_count"] = conversation_log.message_count
        
        return metadata

