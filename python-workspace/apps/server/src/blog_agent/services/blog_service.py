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
        self, file_path: str, file_content: bytes, file_format: str, metadata: dict = None
    ) -> tuple[ProcessingHistory, BlogPost]:
        """Process conversation log and generate blog post."""
        processing_id = uuid4()
        conversation_log_id = None
        blog_post_id = None

        try:
            # Create processing history
            processing = ProcessingHistory(
                id=processing_id,
                conversation_log_id=UUID(int=0),  # Temporary, will update
                status="processing",
            )
            processing = await self.history_repo.create(processing)

            # Parse conversation log
            content_str = file_content.decode("utf-8")
            parser = ParserFactory.create_parser(file_format)
            conversation_log = parser.parse(content_str, file_path)

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

            # Extract
            extract_start = ExtractStartEvent(
                messages=messages,
                conversation_log_id=str(conversation_log_id),
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

