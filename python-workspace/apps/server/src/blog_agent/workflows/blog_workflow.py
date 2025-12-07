"""Blog workflow orchestrator using LlamaIndex Workflows."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from llama_index.core.workflow import StopEvent, Workflow, step

from blog_agent.storage.models import Message
from blog_agent.workflows.editor import BlogEditor, EditEvent
from blog_agent.workflows.extractor import ContentExtractor, ExtractEvent, ExtractStartEvent
from blog_agent.workflows.extender import ContentExtender, ExtendEvent
from blog_agent.workflows.reviewer import ContentReviewer, ReviewEvent
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


class BlogWorkflowStartEvent:
    """Start event for blog workflow."""

    def __init__(self, messages: List[Message], conversation_log_id: str, conversation_log_metadata: Optional[Dict[str, Any]] = None):
        self.messages = messages
        self.conversation_log_id = conversation_log_id
        self.conversation_log_metadata = conversation_log_metadata or {}


class BlogWorkflowStopEvent(StopEvent):
    """Stop event containing final blog post."""

    blog_post_id: str
    conversation_log_id: str


class BlogWorkflow(Workflow):
    """Main blog generation workflow (extractor → extender → reviewer → editor)."""

    def __init__(self, timeout: int = 300, verbose: bool = True):
        """Initialize blog workflow."""
        super().__init__(timeout=timeout, verbose=verbose)
        self.extractor = ContentExtractor()
        self.extender = ContentExtender()
        self.reviewer = ContentReviewer()
        self.editor = BlogEditor()

    async def extract_step(self, ev: BlogWorkflowStartEvent) -> ExtractEvent:
        """Content extraction step."""
        logger.info("Starting content extraction", conversation_log_id=ev.conversation_log_id)
        extract_start = ExtractStartEvent(
            messages=ev.messages,
            conversation_log_id=ev.conversation_log_id,
            conversation_log_metadata=ev.conversation_log_metadata,
        )
        return await self.extractor.extract(extract_start)

    @step
    async def extend_step(self, ev: ExtractEvent) -> ExtendEvent:
        """Content extension step (T070)."""
        logger.info("Starting content extension", conversation_log_id=ev.conversation_log_id)
        return await self.extender.extend(ev)

    @step
    async def review_step(self, ev: ExtendEvent) -> ReviewEvent:
        """Content review step."""
        logger.info("Starting content review", conversation_log_id=ev.conversation_log_id)
        # Convert ExtendEvent to ExtractEvent for reviewer (reviewer expects ExtractEvent structure)
        # The reviewer will use the extended content from ExtendEvent
        from blog_agent.workflows.extractor import ExtractEvent as ExtractorExtractEvent
        
        extract_ev = ExtractorExtractEvent(
            content_extract=ev.content_extract,
            conversation_log_id=ev.conversation_log_id,
            conversation_log_metadata=ev.conversation_log_metadata,
        )
        return await self.reviewer.review(extract_ev)

    @step
    async def edit_step(self, ev: ReviewEvent) -> EditEvent:
        """Blog editing step."""
        logger.info("Starting blog editing", conversation_log_id=ev.conversation_log_id)
        return await self.editor.edit(ev)

    @step
    async def finalize_step(self, ev: EditEvent) -> BlogWorkflowStopEvent:
        """Finalize workflow."""
        logger.info(
            "Workflow completed",
            conversation_log_id=ev.conversation_log_id,
            blog_post_id=ev.blog_post.id,
        )
        return BlogWorkflowStopEvent(
            blog_post_id=str(ev.blog_post.id) if ev.blog_post.id else "",
            conversation_log_id=ev.conversation_log_id,
        )

    async def run_workflow(
        self, messages: List[Message], conversation_log_id: str, conversation_log_metadata: Optional[Dict[str, Any]] = None
    ) -> BlogWorkflowStopEvent:
        """Run the complete workflow."""
        start_event = BlogWorkflowStartEvent(
            messages=messages,
            conversation_log_id=conversation_log_id,
            conversation_log_metadata=conversation_log_metadata or {},
        )

        result = await self.run(start_event)
        return result

