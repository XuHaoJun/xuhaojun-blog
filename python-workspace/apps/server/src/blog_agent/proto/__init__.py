"""Generated gRPC code from Protocol Buffers."""

import sys

# Import blog_agent_pb2 first
from . import blog_agent_pb2

# Register blog_agent_pb2 in sys.modules BEFORE importing blog_agent_pb2_grpc
# This allows the generated grpc code's "import blog_agent_pb2" to work
sys.modules['blog_agent_pb2'] = blog_agent_pb2

# Now import blog_agent_pb2_grpc (which will try to import blog_agent_pb2)
from . import blog_agent_pb2_grpc

# Export for convenience
__all__ = ['blog_agent_pb2', 'blog_agent_pb2_grpc']