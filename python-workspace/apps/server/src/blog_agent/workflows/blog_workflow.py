"""Blog workflow orchestrator using LlamaIndex Workflows."""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from llama_index.core.workflow import Context, Event, StartEvent, StopEvent, Workflow, step

from blog_agent.storage.models import BlogPost, Message, PromptSuggestion
from blog_agent.workflows.editor import BlogEditor, EditEvent
from blog_agent.workflows.extractor import ContentExtractor, ExtractEvent, ExtractStartEvent
from blog_agent.workflows.extender import ContentExtender, ExtendEvent
from blog_agent.workflows.prompt_analyzer import PromptAnalyzer, PromptAnalysisEvent
from blog_agent.workflows.reviewer import ContentReviewer, ReviewEvent
from blog_agent.workflows.memory_manager import ConversationMemoryManager
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


class BlogWorkflowStartEvent(StartEvent):
    """Start event for blog workflow."""

    messages: List[Message]
    conversation_log_id: str
    conversation_log_metadata: Optional[Dict[str, Any]] = None


class BlogWorkflowStopEvent(StopEvent):
    """Stop event containing final results."""

    blog_post: BlogPost
    prompt_suggestions: List[PromptSuggestion]
    conversation_log_id: str


class BlogWorkflow(Workflow):
    """Main blog generation workflow (extractor → extender → reviewer → editor)."""

    def __init__(self, timeout: int = 1200, verbose: bool = True):
        """Initialize blog workflow."""
        super().__init__(timeout=timeout, verbose=verbose)
        self.extractor = ContentExtractor()
        self.extender = ContentExtender()
        self.reviewer = ContentReviewer()
        self.editor = BlogEditor()
        self.prompt_analyzer = PromptAnalyzer()  # T079: Add prompt analyzer for parallel execution

    @step
    async def extract_step(self, ev: BlogWorkflowStartEvent) -> ExtractEvent:
        """Content extraction step."""
        logger.info("Starting content extraction", conversation_log_id=ev.conversation_log_id)
        
        # Create memory manager from messages
        memory = await ConversationMemoryManager.from_messages(ev.messages)
        extract_start = ExtractStartEvent(
            messages=ev.messages,
            conversation_log_id=ev.conversation_log_id,
            conversation_log_metadata=ev.conversation_log_metadata or {},
            memory=memory,
        )
        return await self.extractor.extract(extract_start)

    @step
    async def prompt_analysis_step(self, ev: BlogWorkflowStartEvent) -> PromptAnalysisEvent:
        """
        T079: Prompt analysis step (runs in parallel with main workflow).
        
        This step analyzes user prompts and generates improvement suggestions.
        It runs in parallel with the main content processing pipeline.
        """
        logger.info("Starting prompt analysis", conversation_log_id=ev.conversation_log_id)
        
        # Create memory manager from messages (shared with extract_step)
        memory = await ConversationMemoryManager.from_messages(ev.messages)
        extract_start = ExtractStartEvent(
            messages=ev.messages,
            conversation_log_id=ev.conversation_log_id,
            conversation_log_metadata=ev.conversation_log_metadata or {},
            memory=memory,
        )
        return await self.prompt_analyzer.analyze(extract_start)

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
            memory=ev.memory,  # Pass memory through
        )
        return await self.reviewer.review(extract_ev)

    @step
    async def edit_step(self, ctx: Context, ev: Union[ReviewEvent, PromptAnalysisEvent]) -> Optional[EditEvent]:
        """
        Blog editing step (joins main flow with prompt analysis).
        
        This step waits for both the main content processing flow (ReviewEvent)
        and the parallel prompt analysis flow (PromptAnalysisEvent) to complete
        before generating the final blog post.
        """
        logger.info(f"Received event in edit_step: {type(ev).__name__}", conversation_log_id=ev.conversation_log_id)
        
        # Collect both events before proceeding to edit
        if results := ctx.collect_events(ev, [ReviewEvent, PromptAnalysisEvent]):
            review_ev, prompt_ev = results
            logger.info("Main flow and prompt analysis joined", conversation_log_id=review_ev.conversation_log_id)
            
            # Merge prompt suggestions into ReviewEvent for the editor
            review_ev.prompt_suggestions = prompt_ev.prompt_suggestions
            
            # Execute editor
            return await self.editor.edit(review_ev)
            
        return None

    @step
    async def finalize_step(self, ev: EditEvent) -> BlogWorkflowStopEvent:
        """Finalize workflow."""
        logger.info(
            "Workflow completed",
            conversation_log_id=ev.conversation_log_id,
        )
        return BlogWorkflowStopEvent(
            blog_post=ev.blog_post,
            prompt_suggestions=ev.prompt_suggestions,
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

        # T079: Pass the start event as a keyword argument to avoid confusion with context
        result = await self.run(start_event=start_event)
        return result

