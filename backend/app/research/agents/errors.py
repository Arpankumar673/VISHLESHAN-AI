from typing import Any, Optional
from app.core.errors import AppException


class AgentException(AppException):
    """Base exception for all agent-related failures in Vishleshan AI."""

    def __init__(
        self,
        message: str = "Agent execution failed",
        code: str = "AGENT_ERROR",
        status_code: int = 500,
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=status_code, details=details)


class AgentTimeoutError(AgentException):
    """Raised when an agent or underlying tool operation exceeds its deadline."""

    def __init__(
        self,
        message: str = "Agent execution timed out",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code="AGENT_TIMEOUT", status_code=504, details=details)


class AgentSourceError(AgentException):
    """Raised when an external tool, API, or data source failure prevents agent execution."""

    def __init__(
        self,
        message: str = "External source or tool execution failed",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code="AGENT_SOURCE_ERROR", status_code=502, details=details)


class AgentValidationError(AgentException):
    """Raised when agent inputs, intermediate states, or outputs fail contract validation."""

    def __init__(
        self,
        message: str = "Agent input or contract validation failed",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code="AGENT_VALIDATION_ERROR", status_code=422, details=details)
