"""
Custom exceptions for Grafana operations with production-ready features
"""

import logging
from dataclasses import dataclass
from typing import Any
from pydantic import BaseModel, Field


class TimeoutThresholds(BaseModel):
    """Production-ready timeout thresholds for Grafana operations.

    Attributes:
        read_timeout: Timeout for read operations in seconds (default: 10)
        write_timeout: Timeout for write operations in seconds (default: 30)
        connect_timeout: Timeout for connection establishment in seconds (default: 5)
        retry_attempts: Number of retry attempts (default: 3)
        retry_delay: Initial retry delay in seconds (default: 1)
        max_retry_delay: Maximum retry delay in seconds (default: 10)
    """

    read_timeout: float = Field(
        10.0, gt=0, le=300, description="Read timeout in seconds"
    )
    write_timeout: float = Field(
        30.0, gt=0, le=300, description="Write timeout in seconds"
    )
    connect_timeout: float = Field(
        5.0, gt=0, le=60, description="Connection timeout in seconds"
    )
    retry_attempts: int = Field(3, ge=0, le=5, description="Max retry attempts")
    retry_delay: float = Field(
        1.0, gt=0, le=5, description="Initial retry delay in seconds"
    )
    max_retry_delay: float = Field(
        10.0, gt=0, le=30, description="Max retry delay in seconds"
    )


@dataclass
class ErrorDetail:
    """Structured error details for production logging"""

    code: str
    message: str
    context: dict[str, Any] | None


class GrafanaError(Exception):
    """Base Grafana exception with production features"""

    def __init__(self, detail: ErrorDetail):
        self.detail = detail
        self.logger = logging.getLogger("grafana")
        super().__init__(f"{detail.code}: {detail.message}")

    def log_error(self):
        """Standardized error logging"""
        self.logger.error(
            "Grafana error occurred",
            extra={
                "code": self.detail.code,
                "error_message": self.detail.message,
                "context": self.detail.context or {},
            },
        )


class GrafanaConnectionError(GrafanaError):
    """Connection/network related errors"""

    DEFAULT_CODE = "grafana_connection_error"

    def __init__(self, message: str, url: str, context: dict[str, Any] | None):
        detail = ErrorDetail(
            code=self.DEFAULT_CODE,
            message=message,
            context={"url": url, **(context or {})},
        )
        super().__init__(detail)


class GrafanaAuthError(GrafanaError):
    """Authentication/authorization errors"""

    DEFAULT_CODE = "grafana_auth_error"

    def __init__(
        self, message: str, status_code: int, context: dict[str, Any] | None
    ):
        detail = ErrorDetail(
            code=self.DEFAULT_CODE,
            message=message,
            context={"status_code": status_code, **(context or {})},
        )
        super().__init__(detail)


class GrafanaNotFoundError(GrafanaError):
    """Resource not found"""

    DEFAULT_CODE = "grafana_not_found"

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        context: dict[str, Any] | None,
    ):
        detail = ErrorDetail(
            code=self.DEFAULT_CODE,
            message=f"{resource_type} with ID {resource_id} not found",
            context={
                "resource_type": resource_type,
                "resource_id": resource_id,
                **(context or {}),
            },
        )
        super().__init__(detail)


class GrafanaConflictError(GrafanaError):
    """Resource conflict (e.g. duplicate)"""

    DEFAULT_CODE = "grafana_conflict"

    def __init__(
        self,
        resource_type: str,
        conflict_reason: str,
        context: dict[str, Any] | None,
    ):
        detail = ErrorDetail(
            code=self.DEFAULT_CODE,
            message=f"Conflict creating {resource_type}: {conflict_reason}",
            context={
                "resource_type": resource_type,
                "conflict_reason": conflict_reason,
                **(context or {}),
            },
        )
        super().__init__(detail)


class GrafanaValidationError(GrafanaError):
    """Invalid data/configuration"""

    DEFAULT_CODE = "grafana_validation_error"

    def __init__(
        self,
        message: str,
        validation_errors: dict[str, Any],
        context: dict[str, Any] | None,
    ):
        detail = ErrorDetail(
            code=self.DEFAULT_CODE,
            message=message,
            context={"validation_errors": validation_errors, **(context or {})},
        )
        super().__init__(detail)


class GrafanaRateLimitError(GrafanaError):
    """Rate limit exceeded"""

    DEFAULT_CODE = "grafana_rate_limit"

    def __init__(
        self,
        message: str,
        limit: int,
        remaining: int,
        reset_time: str,
        context: dict[str, Any] | None,
    ):
        detail = ErrorDetail(
            code=self.DEFAULT_CODE,
            message=message,
            context={
                "rate_limit": limit,
                "remaining": remaining,
                "reset_time": reset_time,
                **(context or {}),
            },
        )
        super().__init__(detail)


class GrafanaTimeoutError(Exception):
    """Exception raised when Grafana operation times out.

    Attributes:
        operation: The operation that timed out
        timeout: The timeout value that was exceeded
        threshold: The configured threshold for this operation
    """

    def __init__(self, operation: str, timeout: float, threshold: TimeoutThresholds):
        self.operation = operation
        self.timeout = timeout
        self.threshold = threshold
        message = (
            f"Grafana {operation} operation timed out after {timeout} seconds. "
            f"Configured thresholds: {threshold}"
        )
        super().__init__(message)
