from typing import Any, Optional


class AppException(Exception):
    """Base application exception for Vishleshan AI."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details,
        )


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication required or invalid credentials", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="UNAUTHENTICATED",
            status_code=401,
            details=details,
        )


class AuthorizationError(AppException):
    def __init__(self, message: str = "Permission denied for this resource", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
            status_code=403,
            details=details,
        )


class ValidationError(AppException):
    def __init__(self, message: str = "Invalid input parameters", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class ConflictError(AppException):
    def __init__(self, message: str = "Resource conflict detected", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details,
        )


class DatabaseError(AppException):
    def __init__(self, message: str = "Database operation failed", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500,
            details=details,
        )
