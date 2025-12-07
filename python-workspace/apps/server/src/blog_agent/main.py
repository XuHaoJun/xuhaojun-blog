"""gRPC server entry point."""

import asyncio
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


# TODO: Uncomment after proto generation (T021)
# from blog_agent.proto import blog_agent_pb2, blog_agent_pb2_grpc


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
            # TODO: Uncomment after proto generation
            # response = blog_agent_pb2.ProcessConversationResponse(
            #     processing_id=str(processing.id),
            #     status=self._map_processing_status(processing.status),
            #     blog_post=self._blog_post_to_proto(blog_post),
            # )
            # return response

            # Temporary placeholder
            return {"processing_id": str(processing.id), "status": processing.status}

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

    def _blog_post_to_proto(self, blog_post):
        """Convert BlogPost model to proto message."""
        # TODO: Implement after proto generation
        pass

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

            # TODO: Uncomment after proto generation
            # response = blog_agent_pb2.GetConversationLogResponse(
            #     conversation_log=self._conversation_log_to_proto(conversation_log)
            # )
            # return response

            # Temporary placeholder
            return {"conversation_log": self._conversation_log_to_dict(conversation_log)}

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

            # TODO: Uncomment after proto generation
            # response = blog_agent_pb2.ListConversationLogsResponse(
            #     conversation_logs=[
            #         self._conversation_log_to_proto(log) for log in conversation_logs
            #     ],
            #     next_page_token=next_page_token,
            #     total_count=len(conversation_logs),  # Note: This is approximate without full count
            # )
            # return response

            # Temporary placeholder
            return {
                "conversation_logs": [self._conversation_log_to_dict(log) for log in conversation_logs],
                "next_page_token": next_page_token,
                "total_count": len(conversation_logs),
            }

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

            # TODO: Uncomment after proto generation
            # response = blog_agent_pb2.GetBlogPostResponse(
            #     blog_post=self._blog_post_to_proto(blog_post)
            # )
            # return response

            # Temporary placeholder
            return {"blog_post": self._blog_post_to_dict(blog_post)}

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
        Get blog post with structured content blocks and prompt meta for UI/UX support.
        
        Returns BlogPost + ContentBlocks with PromptMeta for Side-by-Side display.
        """
        try:
            blog_post_id = UUID(request.blog_post_id)
            blog_post = await self.blog_repo.get_by_id(blog_post_id)

            if not blog_post:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Blog post not found: {request.blog_post_id}")
                return None

            # Get content blocks for this blog post
            content_blocks = await self.content_block_repo.get_by_blog_post_id(blog_post_id)
            
            # Build ContentBlock proto messages with PromptMeta
            content_block_protos = []
            for block in content_blocks:
                prompt_meta = None
                
                # If block has associated prompt_suggestion, build PromptMeta
                if block.prompt_suggestion_id:
                    prompt_suggestion = await self.prompt_suggestion_repo.get_by_id(block.prompt_suggestion_id)
                    if prompt_suggestion:
                        prompt_meta = build_prompt_meta(prompt_suggestion)
                
                # TODO: Uncomment after proto generation
                # content_block_proto = blog_agent_pb2.ContentBlock(
                #     id=str(block.id) if block.id else "",
                #     blog_post_id=str(block.blog_post_id),
                #     block_order=block.block_order,
                #     text=block.text,
                #     prompt_meta=blog_agent_pb2.PromptMeta(**prompt_meta) if prompt_meta else None,
                # )
                # content_block_protos.append(content_block_proto)
                
                # Temporary placeholder
                content_block_protos.append({
                    "id": str(block.id) if block.id else "",
                    "blog_post_id": str(block.blog_post_id),
                    "block_order": block.block_order,
                    "text": block.text,
                    "prompt_meta": prompt_meta,
                })

            # TODO: Uncomment after proto generation
            # response = blog_agent_pb2.GetBlogPostWithPromptsResponse(
            #     blog_post=self._blog_post_to_proto(blog_post),
            #     content_blocks=content_block_protos,
            # )
            # return response

            # Temporary placeholder
            return {
                "blog_post": self._blog_post_to_dict(blog_post),
                "content_blocks": content_block_protos,
            }

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

            # TODO: Uncomment after proto generation
            # response = blog_agent_pb2.ListBlogPostsResponse(
            #     blog_posts=[
            #         self._blog_post_to_proto(post) for post in blog_posts
            #     ],
            #     next_page_token=next_page_token,
            #     total_count=len(blog_posts),  # Note: This is approximate without full count
            # )
            # return response

            # Temporary placeholder
            return {
                "blog_posts": [self._blog_post_to_dict(post) for post in blog_posts],
                "next_page_token": next_page_token,
                "total_count": len(blog_posts),
            }

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

            # TODO: Uncomment after proto generation
            # response = blog_agent_pb2.GetProcessingHistoryResponse(
            #     processing_history=self._processing_history_to_proto(processing_history)
            # )
            # return response

            # Temporary placeholder
            return {"processing_history": self._processing_history_to_dict(processing_history)}

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
    try:
        import grpc
        from grpc import aio

        # Create gRPC server
        server = aio.server()

        # Add service implementation
        service_impl = BlogAgentServiceImpl()
        # TODO: Uncomment after proto generation (T021)
        # blog_agent_pb2_grpc.add_BlogAgentServiceServicer_to_server(
        #     service_impl, server
        # )

        # Listen on port
        listen_addr = f"{config.GRPC_HOST}:{config.GRPC_PORT}"
        server.add_insecure_port(listen_addr)

        logger.info("Starting gRPC server", address=listen_addr)
        await server.start()

        logger.info("gRPC server started", port=config.GRPC_PORT)

        # Wait for termination
        await server.wait_for_termination()

    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server")
    except Exception as e:
        logger.error("gRPC server error", error=str(e), exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(serve())
