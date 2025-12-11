"""gRPC server entry point."""

import asyncio
import signal
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime
from uuid import UUID

try:
    import grpc
except ImportError:
    grpc = None  # Will be available when grpcio is installed

from blog_agent.config import config
from blog_agent.services.blog_service import BlogService
from blog_agent.services.llm import get_llm
from blog_agent.storage.models import ConversationMessage
from blog_agent.storage.repository import (
    BlogPostRepository,
    ContentBlockRepository,
    ConversationLogRepository,
    ProcessingHistoryRepository,
    PromptSuggestionRepository,
)
from blog_agent.utils.prompt_meta_builder import build_prompt_meta
from blog_agent.utils.errors import BlogAgentError
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


from blog_agent.proto import blog_agent_pb2, blog_agent_pb2_grpc


class BlogAgentServiceImpl:
    """gRPC service implementation for Blog Agent."""

    def __init__(self):
        """Initialize service."""
        self.blog_service = BlogService()
        self.conversation_repo = ConversationLogRepository()
        self.blog_repo = BlogPostRepository()
        self.history_repo = ProcessingHistoryRepository()
        self.content_block_repo = ContentBlockRepository()  # T085a: For GetBlogPostWithPrompts
        self.prompt_suggestion_repo = PromptSuggestionRepository()  # T085a: For GetBlogPostWithPrompts

    async def ProcessConversation(self, request, context):
        """Process conversation log and generate blog post."""
        try:
            # Extract request data
            file_path = request.file_path
            file_content = request.file_content
            file_format = self._map_file_format(request.file_format)
            metadata = dict(request.metadata) if hasattr(request, "metadata") else {}
            force = getattr(request, "force", False)  # FR-034: Support force flag

            # Process conversation
            processing, blog_post = await self.blog_service.process_conversation(
                file_path=file_path,
                file_content=file_content,
                file_format=file_format,
                metadata=metadata,
                force=force,
            )

            # Build response
            response = blog_agent_pb2.ProcessConversationResponse(
                processing_id=str(processing.id),
                status=self._map_processing_status(processing.status),
                blog_post=self._blog_post_to_proto(blog_post) if blog_post else None,
            )
            return response

        except BlogAgentError as e:
            logger.error("Processing error", error=str(e), details=e.to_dict())
            # TODO: Return error response with full technical details (FR-024)
            raise
        except Exception as e:
            logger.error("Unexpected error", error=str(e), exc_info=True)
            raise

    def _map_file_format(self, proto_format):
        """Map proto FileFormat to string."""
        format_map = {
            0: "markdown",  # FILE_FORMAT_UNSPECIFIED -> default to markdown
            1: "markdown",  # FILE_FORMAT_MARKDOWN
            2: "json",      # FILE_FORMAT_JSON
            3: "csv",       # FILE_FORMAT_CSV
            4: "text",      # FILE_FORMAT_TEXT
        }
        return format_map.get(proto_format, "markdown")

    def _map_processing_status(self, status: str):
        """Map string status to proto ProcessingStatus enum."""
        status_map = {
            "pending": 1,      # PROCESSING_STATUS_PENDING
            "processing": 2,  # PROCESSING_STATUS_PROCESSING
            "completed": 3,   # PROCESSING_STATUS_COMPLETED
            "failed": 4,      # PROCESSING_STATUS_FAILED
        }
        return status_map.get(status.lower(), 0)  # PROCESSING_STATUS_UNSPECIFIED

    def _conversation_log_to_proto(self, conversation_log):
        """Convert ConversationLog model to proto message."""
        import json
        
        # Convert metadata values to strings (protobuf requires map<string, string>)
        metadata_dict = {}
        if conversation_log.metadata:
            for key, value in conversation_log.metadata.items():
                if value is None:
                    metadata_dict[str(key)] = ""
                elif isinstance(value, (str, int, float, bool)):
                    metadata_dict[str(key)] = str(value)
                else:
                    # For complex types (list, dict, etc.), serialize to JSON string
                    metadata_dict[str(key)] = json.dumps(value, ensure_ascii=False)
        
        return blog_agent_pb2.ConversationLog(
            id=str(conversation_log.id) if conversation_log.id else "",
            file_path=conversation_log.file_path or "",
            file_format=self._map_file_format_to_proto(conversation_log.file_format),
            raw_content=conversation_log.raw_content or "",
            parsed_content_json=json.dumps(conversation_log.parsed_content) if conversation_log.parsed_content else "",
            metadata=metadata_dict,
            language=conversation_log.language or "",
            message_count=conversation_log.message_count or 0,
            created_at=conversation_log.created_at.isoformat() if conversation_log.created_at else "",
            updated_at=conversation_log.updated_at.isoformat() if conversation_log.updated_at else "",
        )

    def _blog_post_to_proto(self, blog_post):
        """Convert BlogPost model to proto message."""
        import json
        
        # Convert metadata values to strings (protobuf requires map<string, string>)
        metadata_dict = {}
        if blog_post.metadata:
            for key, value in blog_post.metadata.items():
                if value is None:
                    metadata_dict[str(key)] = ""
                elif isinstance(value, (str, int, float, bool)):
                    metadata_dict[str(key)] = str(value)
                else:
                    # For complex types (list, dict, etc.), serialize to JSON string
                    metadata_dict[str(key)] = json.dumps(value, ensure_ascii=False)
        
        # Ensure tags is a list
        tags_list = blog_post.tags if isinstance(blog_post.tags, list) else list(blog_post.tags) if blog_post.tags else []
        
        return blog_agent_pb2.BlogPost(
            id=str(blog_post.id) if blog_post.id else "",
            conversation_log_id=str(blog_post.conversation_log_id),
            title=blog_post.title or "",
            summary=blog_post.summary or "",
            tags=tags_list,
            content=blog_post.content or "",
            metadata=metadata_dict,
            status=self._map_blog_post_status_to_proto(blog_post.status),
            created_at=blog_post.created_at.isoformat() if blog_post.created_at else "",
            updated_at=blog_post.updated_at.isoformat() if blog_post.updated_at else "",
        )

    def _processing_history_to_proto(self, processing_history):
        """Convert ProcessingHistory model to proto message."""
        import json
        return blog_agent_pb2.ProcessingHistory(
            id=str(processing_history.id) if processing_history.id else "",
            conversation_log_id=str(processing_history.conversation_log_id),
            blog_post_id=str(processing_history.blog_post_id) if processing_history.blog_post_id else "",
            status=self._map_processing_status_to_proto(processing_history.status),
            error_message=processing_history.error_message or "",
            processing_steps_json=json.dumps(processing_history.processing_steps) if processing_history.processing_steps else "",
            started_at=processing_history.started_at.isoformat() if processing_history.started_at else "",
            completed_at=processing_history.completed_at.isoformat() if processing_history.completed_at else "",
            created_at=processing_history.created_at.isoformat() if processing_history.created_at else "",
        )

    # T082: GetConversationLog handler
    async def GetConversationLog(self, request, context):
        """Get a specific conversation log by ID."""
        try:
            conversation_log_id = UUID(request.conversation_log_id)
            conversation_log = await self.conversation_repo.get_by_id(conversation_log_id)

            if not conversation_log:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Conversation log not found: {request.conversation_log_id}")
                return None

            response = blog_agent_pb2.GetConversationLogResponse(
                conversation_log=self._conversation_log_to_proto(conversation_log)
            )
            return response

        except ValueError as e:
            logger.error("Invalid conversation log ID", error=str(e))
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid conversation log ID: {str(e)}")
            return None
        except Exception as e:
            logger.error("GetConversationLog error", error=str(e), exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return None

    # T083: ListConversationLogs handler
    async def ListConversationLogs(self, request, context):
        """List conversation logs with pagination."""
        try:
            page_size = request.page_size if request.page_size > 0 else 100
            page_token = request.page_token if request.page_token else "0"
            
            # Parse page token (simple offset-based pagination)
            try:
                offset = int(page_token)
            except ValueError:
                offset = 0

            # Apply language filter if provided
            conversation_logs = await self.conversation_repo.list(limit=page_size, offset=offset)
            
            if request.language_filter:
                conversation_logs = [
                    log for log in conversation_logs
                    if log.language == request.language_filter
                ]

            # Generate next page token
            next_page_token = str(offset + len(conversation_logs)) if len(conversation_logs) == page_size else ""

            response = blog_agent_pb2.ListConversationLogsResponse(
                conversation_logs=[
                    self._conversation_log_to_proto(log) for log in conversation_logs
                ],
                next_page_token=next_page_token,
                total_count=len(conversation_logs),  # Note: This is approximate without full count
            )
            return response

        except Exception as e:
            logger.error("ListConversationLogs error", error=str(e), exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return None

    # T084: GetBlogPost handler
    async def GetBlogPost(self, request, context):
        """Get a specific blog post by ID."""
        try:
            blog_post_id = UUID(request.blog_post_id)
            blog_post = await self.blog_repo.get_by_id(blog_post_id)

            if not blog_post:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Blog post not found: {request.blog_post_id}")
                return None

            response = blog_agent_pb2.GetBlogPostResponse(
                blog_post=self._blog_post_to_proto(blog_post)
            )
            return response

        except ValueError as e:
            logger.error("Invalid blog post ID", error=str(e))
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid blog post ID: {str(e)}")
            return None
        except Exception as e:
            logger.error("GetBlogPost error", error=str(e), exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return None

    # T085a: GetBlogPostWithPrompts handler (UI/UX P0)
    async def GetBlogPostWithPrompts(self, request, context):
        """
        Get blog post with conversation messages and prompt suggestions for UI/UX support.
        
        Returns BlogPost + ConversationMessages + PromptSuggestions for Side-by-Side display.
        ContentBlocks are set to empty array for backward compatibility.
        """
        try:
            blog_post_id = UUID(request.blog_post_id)
            blog_post = await self.blog_repo.get_by_id(blog_post_id)

            if not blog_post:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Blog post not found: {request.blog_post_id}")
                return None

            # Get conversation log
            conversation_log = await self.conversation_repo.get_by_id(blog_post.conversation_log_id)
            if not conversation_log:
                logger.warning(
                    "Conversation log not found",
                    conversation_log_id=str(blog_post.conversation_log_id),
                )
                # Return empty conversation messages if log not found
                conversation_messages = []
            else:
                # Extract conversation messages from parsed_content
                conversation_messages = self._extract_conversation_messages(conversation_log)
            
            # Get all prompt suggestions for this conversation log
            prompt_suggestions = await self.prompt_suggestion_repo.get_all_by_conversation_log_id(
                blog_post.conversation_log_id
            )
            
            # Convert ConversationMessage to proto
            conversation_message_protos = []
            for msg in conversation_messages:
                timestamp_str = None
                if msg.timestamp:
                    timestamp_str = msg.timestamp.isoformat()
                
                conversation_message_protos.append(
                    blog_agent_pb2.ConversationMessage(
                        role=msg.role,
                        content=msg.content,
                        timestamp=timestamp_str or "",
                    )
                )
            
            # Convert PromptSuggestion to proto
            prompt_suggestion_protos = []
            for ps in prompt_suggestions:
                prompt_suggestion_protos.append(
                    blog_agent_pb2.PromptSuggestion(
                        id=str(ps.id) if ps.id else "",
                        original_prompt=ps.original_prompt,
                        analysis=ps.analysis,
                        better_candidates=[
                            blog_agent_pb2.PromptCandidate(
                                type=candidate.type,
                                prompt=candidate.prompt,
                                reasoning=candidate.reasoning,
                            )
                            for candidate in ps.better_candidates
                        ],
                        expected_effect=ps.expected_effect or "",
                    )
                )

            # Build response with empty content_blocks for backward compatibility
            response = blog_agent_pb2.GetBlogPostWithPromptsResponse(
                blog_post=self._blog_post_to_proto(blog_post),
                content_blocks=[],  # Empty for backward compatibility
                conversation_messages=conversation_message_protos,
                prompt_suggestions=prompt_suggestion_protos,
            )
            return response

        except ValueError as e:
            logger.error("Invalid blog post ID", error=str(e))
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid blog post ID: {str(e)}")
            return None
        except Exception as e:
            logger.error("GetBlogPostWithPrompts error", error=str(e), exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return None

    # T085: ListBlogPosts handler
    async def ListBlogPosts(self, request, context):
        """List blog posts with pagination and status filter."""
        try:
            page_size = request.page_size if request.page_size > 0 else 100
            page_token = request.page_token if request.page_token else "0"
            
            # Parse page token (simple offset-based pagination)
            try:
                offset = int(page_token)
            except ValueError:
                offset = 0

            blog_posts = await self.blog_repo.list(limit=page_size, offset=offset)

            # Apply status filter if provided
            if request.status_filter:
                status_str = self._map_blog_post_status_from_proto(request.status_filter)
                blog_posts = [
                    post for post in blog_posts
                    if post.status == status_str
                ]

            # Generate next page token
            next_page_token = str(offset + len(blog_posts)) if len(blog_posts) == page_size else ""

            response = blog_agent_pb2.ListBlogPostsResponse(
                blog_posts=[
                    self._blog_post_to_proto(post) for post in blog_posts
                ],
                next_page_token=next_page_token,
                total_count=len(blog_posts),  # Note: This is approximate without full count
            )
            return response

        except Exception as e:
            logger.error("ListBlogPosts error", error=str(e), exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return None

    # T086: GetProcessingHistory handler
    async def GetProcessingHistory(self, request, context):
        """Get processing history by ID."""
        try:
            processing_id = UUID(request.processing_id)
            processing_history = await self.history_repo.get_by_id(processing_id)

            if not processing_history:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Processing history not found: {request.processing_id}")
                return None

            response = blog_agent_pb2.GetProcessingHistoryResponse(
                processing_history=self._processing_history_to_proto(processing_history)
            )
            return response

        except ValueError as e:
            logger.error("Invalid processing ID", error=str(e))
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid processing ID: {str(e)}")
            return None
        except Exception as e:
            logger.error("GetProcessingHistory error", error=str(e), exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return None

    def _extract_conversation_messages(self, conversation_log):
        """
        從 conversation_log 的 parsed_content 中提取對話訊息。
        
        Args:
            conversation_log: ConversationLog 物件
            
        Returns:
            ConversationMessage 列表
        """
        from datetime import datetime
        
        messages = []
        parsed_content = conversation_log.parsed_content
        
        try:
            # parsed_content 應該包含 messages 陣列
            if isinstance(parsed_content, dict) and "messages" in parsed_content:
                messages_list = parsed_content["messages"]
                if not isinstance(messages_list, list):
                    logger.warning(
                        "parsed_content.messages is not a list",
                        conversation_log_id=str(conversation_log.id),
                    )
                    return messages
                
                for msg_data in messages_list:
                    try:
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
                    except Exception as e:
                        logger.warning(
                            "Failed to parse message",
                            error=str(e),
                            conversation_log_id=str(conversation_log.id),
                        )
                        # Continue processing other messages
                        continue
            else:
                logger.warning(
                    "parsed_content does not contain messages array",
                    conversation_log_id=str(conversation_log.id),
                )
        except Exception as e:
            logger.error(
                "Failed to extract conversation messages",
                error=str(e),
                conversation_log_id=str(conversation_log.id),
                exc_info=True,
            )
        
        return messages

    # Helper methods for conversion (temporary dict-based until proto generation)
    def _conversation_log_to_dict(self, conversation_log):
        """Convert ConversationLog model to dictionary (temporary)."""
        import json
        return {
            "id": str(conversation_log.id),
            "file_path": conversation_log.file_path,
            "file_format": self._map_file_format_to_proto(conversation_log.file_format),
            "raw_content": conversation_log.raw_content,
            "parsed_content_json": json.dumps(conversation_log.parsed_content),
            "metadata": conversation_log.metadata or {},
            "language": conversation_log.language or "",
            "message_count": conversation_log.message_count or 0,
            "created_at": conversation_log.created_at.isoformat() if conversation_log.created_at else "",
            "updated_at": conversation_log.updated_at.isoformat() if conversation_log.updated_at else "",
        }

    def _blog_post_to_dict(self, blog_post):
        """Convert BlogPost model to dictionary (temporary)."""
        import json
        return {
            "id": str(blog_post.id),
            "conversation_log_id": str(blog_post.conversation_log_id),
            "title": blog_post.title,
            "summary": blog_post.summary,
            "tags": blog_post.tags,
            "content": blog_post.content,
            "metadata": blog_post.metadata or {},
            "status": self._map_blog_post_status_to_proto(blog_post.status),
            "created_at": blog_post.created_at.isoformat() if blog_post.created_at else "",
            "updated_at": blog_post.updated_at.isoformat() if blog_post.updated_at else "",
        }

    def _processing_history_to_dict(self, processing_history):
        """Convert ProcessingHistory model to dictionary (temporary)."""
        import json
        return {
            "id": str(processing_history.id),
            "conversation_log_id": str(processing_history.conversation_log_id),
            "blog_post_id": str(processing_history.blog_post_id) if processing_history.blog_post_id else "",
            "status": self._map_processing_status_to_proto(processing_history.status),
            "error_message": processing_history.error_message or "",
            "processing_steps_json": json.dumps(processing_history.processing_steps) if processing_history.processing_steps else "",
            "started_at": processing_history.started_at.isoformat() if processing_history.started_at else "",
            "completed_at": processing_history.completed_at.isoformat() if processing_history.completed_at else "",
            "created_at": processing_history.created_at.isoformat() if processing_history.created_at else "",
        }

    def _map_file_format_to_proto(self, format_str):
        """Map string format to proto FileFormat enum."""
        format_map = {
            "markdown": 1,  # FILE_FORMAT_MARKDOWN
            "json": 2,      # FILE_FORMAT_JSON
            "csv": 3,       # FILE_FORMAT_CSV
            "text": 4,      # FILE_FORMAT_TEXT
        }
        return format_map.get(format_str.lower(), 0)  # FILE_FORMAT_UNSPECIFIED

    def _map_processing_status_to_proto(self, status_str):
        """Map string status to proto ProcessingStatus enum."""
        status_map = {
            "pending": 1,      # PROCESSING_STATUS_PENDING
            "processing": 2,  # PROCESSING_STATUS_PROCESSING
            "completed": 3,   # PROCESSING_STATUS_COMPLETED
            "failed": 4,      # PROCESSING_STATUS_FAILED
        }
        return status_map.get(status_str.lower(), 0)  # PROCESSING_STATUS_UNSPECIFIED

    def _map_processing_status_from_proto(self, proto_status):
        """Map proto ProcessingStatus enum to string."""
        status_map = {
            1: "pending",
            2: "processing",
            3: "completed",
            4: "failed",
        }
        return status_map.get(proto_status, "pending")

    def _map_blog_post_status_to_proto(self, status_str):
        """Map string status to proto BlogPostStatus enum."""
        status_map = {
            "draft": 1,       # BLOG_POST_STATUS_DRAFT
            "published": 2,   # BLOG_POST_STATUS_PUBLISHED
            "archived": 3,    # BLOG_POST_STATUS_ARCHIVED
        }
        return status_map.get(status_str.lower(), 0)  # BLOG_POST_STATUS_UNSPECIFIED

    def _map_blog_post_status_from_proto(self, proto_status):
        """Map proto BlogPostStatus enum to string."""
        status_map = {
            1: "draft",
            2: "published",
            3: "archived",
        }
        return status_map.get(proto_status, "draft")


async def serve():
    """Start gRPC server."""
    import grpc
    from grpc import aio

    # Check LLM structured_predict support
    try:
        llm = get_llm()
        has_structured_predict = hasattr(llm, 'structured_predict')
        llm_type = type(llm).__name__
        llm_provider = config.LLM_PROVIDER
        llm_model = config.LLM_MODEL
        
        logger.info(
            "LLM structured_predict support check",
            provider=llm_provider,
            model=llm_model,
            llm_type=llm_type,
            has_structured_predict=has_structured_predict,
        )
        
        if not has_structured_predict:
            logger.warning(
                "LLM does not support structured_predict - workflows will use fallback methods",
                provider=llm_provider,
                model=llm_model,
            )
    except Exception as e:
        logger.warning(
            "Failed to check LLM structured_predict support",
            error=str(e),
            exc_info=True,
        )

    # Create gRPC server
    server = aio.server()

    # Add service implementation
    service_impl = BlogAgentServiceImpl()
    blog_agent_pb2_grpc.add_BlogAgentServiceServicer_to_server(
        service_impl, server
    )

    # Listen on port
    listen_addr = f"{config.GRPC_HOST}:{config.GRPC_PORT}"
    server.add_insecure_port(listen_addr)

    logger.info("Starting gRPC server", address=listen_addr)
    await server.start()

    logger.info("gRPC server started", port=config.GRPC_PORT)

    # Set up signal handlers for graceful shutdown
    shutdown_event = asyncio.Event()

    def signal_handler():
        """Handle shutdown signals."""
        logger.info("Received shutdown signal, initiating graceful shutdown")
        shutdown_event.set()

    # Register signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Signal handlers are only available on Unix
            logger.warning("Signal handlers not available on this platform")
            break

    try:
        # Wait for shutdown signal
        await shutdown_event.wait()
    except Exception as e:
        logger.error("Error waiting for shutdown signal", error=str(e), exc_info=True)
    finally:
        # Gracefully stop the server
        logger.info("Stopping gRPC server")
        try:
            await server.stop(grace=5)  # Give 5 seconds for graceful shutdown
            logger.info("gRPC server stopped")
        except Exception as e:
            logger.error("Error stopping server", error=str(e), exc_info=True)


if __name__ == "__main__":
    asyncio.run(serve())
