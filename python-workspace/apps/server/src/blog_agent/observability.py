"""Phoenix observability instrumentation for LlamaIndex."""

from blog_agent.config import config
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)

_initialized = False


def init_observability():
    """Initialize Phoenix observability if enabled."""
    global _initialized

    if _initialized:
        return

    if not config.PHOENIX_ENABLED:
        logger.info("Phoenix observability disabled")
        return

    try:
        from phoenix.otel import register
        from openinference.instrumentation.llama_index import LlamaIndexInstrumentor

        register_kwargs = {"project_name": config.PHOENIX_PROJECT_NAME}
        if config.PHOENIX_COLLECTOR_ENDPOINT:
            register_kwargs["endpoint"] = config.PHOENIX_COLLECTOR_ENDPOINT

        tracer_provider = register(**register_kwargs)
        LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)

        _initialized = True
        logger.info(
            "Phoenix observability initialized",
            project_name=config.PHOENIX_PROJECT_NAME,
            endpoint=config.PHOENIX_COLLECTOR_ENDPOINT or "default",
        )
    except ImportError as e:
        _initialized = True  # Mark as initialized to prevent retry attempts
        logger.warning("Phoenix packages not installed, observability disabled", error=str(e))
    except Exception as e:
        _initialized = True  # Mark as initialized to prevent retry attempts
        logger.error("Failed to initialize Phoenix observability", error=str(e), exc_info=True)
