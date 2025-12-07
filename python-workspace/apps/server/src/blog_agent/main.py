"""gRPC server entry point."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from blog_agent.config import config
from blog_agent.services.blog_service import BlogService
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

    async def ProcessConversation(self, request, context):
        """Process conversation log and generate blog post."""
        try:
            # Extract request data
            file_path = request.file_path
            file_content = request.file_content
            file_format = self._map_file_format(request.file_format)
            metadata = dict(request.metadata) if hasattr(request, "metadata") else {}

            # Process conversation
            processing, blog_post = await self.blog_service.process_conversation(
                file_path=file_path,
                file_content=file_content,
                file_format=file_format,
                metadata=metadata,
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
        # TODO: Implement after proto generation
        format_map = {
            # 0: "markdown",  # FILE_FORMAT_UNSPECIFIED
            # 1: "markdown",  # FILE_FORMAT_MARKDOWN
            # 2: "json",      # FILE_FORMAT_JSON
            # 3: "csv",       # FILE_FORMAT_CSV
            # 4: "text",      # FILE_FORMAT_TEXT
        }
        return format_map.get(proto_format, "markdown")

    def _map_processing_status(self, status: str):
        """Map string status to proto ProcessingStatus."""
        # TODO: Implement after proto generation
        pass

    def _blog_post_to_proto(self, blog_post):
        """Convert BlogPost model to proto message."""
        # TODO: Implement after proto generation
        pass


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
