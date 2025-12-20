"""Generated gRPC code from Protocol Buffers."""

import sys

# Import blog_agent_pb2 first
from . import blog_agent_pb2

# Register blog_agent_pb2 in sys.modules
# This allows the generated connect code's "import blog_agent_pb2" to work
sys.modules['blog_agent_pb2'] = blog_agent_pb2

# Export for convenience
__all__ = ['blog_agent_pb2']