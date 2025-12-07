"""Error handling infrastructure."""

import traceback
from typing import Any, Dict, Optional


class BlogAgentError(Exception):
    """Base exception for blog agent system."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.stack_trace = traceback.format_exc()

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary with full technical details."""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "stack_trace": self.stack_trace,
            "type": self.__class__.__name__,
        }


class ExternalServiceError(BlogAgentError):
    """Error when external service fails."""

    def __init__(
        self,
        service_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"External service '{service_name}' failed: {message}",
            error_code=f"EXTERNAL_SERVICE_{service_name.upper()}_FAILED",
            details=details or {},
        )
        self.service_name = service_name


class ProcessingError(BlogAgentError):
    """Error during content processing."""

    def __init__(
        self,
        step: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"Processing failed at step '{step}': {message}",
            error_code=f"PROCESSING_{step.upper()}_FAILED",
            details=details or {},
        )
        self.step = step


class ValidationError(BlogAgentError):
    """Error when validation fails."""

    def __init__(
        self,
        field: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"Validation failed for field '{field}': {message}",
            error_code="VALIDATION_FAILED",
            details=details or {},
        )
        self.field = field

