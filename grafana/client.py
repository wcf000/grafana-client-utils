# app/core/grafana/client.py
import logging
from typing import Optional

import requests
from circuitbreaker import circuit
from grafana_client import GrafanaApi
from prometheus_client import Counter, Histogram
from tenacity import RetryCallState, retry, stop_after_attempt, wait_exponential

from app.core.grafana.config import GrafanaConfig
from app.core.grafana.exceptions import (
    ErrorDetail,  # Add this import
    GrafanaAuthError,
    GrafanaConflictError,
    GrafanaConnectionError,
    GrafanaError,
    GrafanaNotFoundError,
    GrafanaRateLimitError,
    GrafanaValidationError,
)

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_LATENCY = Histogram(
    "grafana_client_request_latency_seconds",
    "Grafana API request latency",
    ["method", "endpoint"],
)
CIRCUIT_STATE = Counter(
    "grafana_client_circuit_state_changes_total",
    "Circuit breaker state changes",
    ["state"],
)


class GrafanaClient:
    def __init__(self, config: Optional[GrafanaConfig] = None):
        """Initialize a production-ready Grafana client"""
        self.config = config or GrafanaConfig()
        self._session = None  # For connection pooling
        self._circuit_state = "closed"

    @property
    def session(self) -> requests.Session:
        """Reusable connection session with pooling"""
        if self._session is None:
            self._session = self._create_session()
        return self._session

    @circuit(
        failure_threshold=5,
        recovery_timeout=60,
        expected_exception=(
            GrafanaConnectionError,
            GrafanaRateLimitError,
     
        )
    )
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        before_sleep=lambda retry_state: retry_state.args[0]._log_retry_attempt(
            retry_state
        ),
    )
    def get_client(self) -> GrafanaApi:
        """Get a production-ready Grafana client with proper error handling"""
        with REQUEST_LATENCY.labels("connect", "grafana").time():
            try:
                client = GrafanaApi.from_url(
                    url=self.config.SERVICE_URL,
                    credential=self.config.API_KEY,
                    timeout=(self.config.CONNECT_TIMEOUT, self.config.READ_TIMEOUT),
                    **self.config.SSL_CONFIG,
                )
                client.session = self.session
                return client
            except requests.exceptions.ConnectionError as e:
                raise GrafanaConnectionError(
                    message="Failed to connect to Grafana",
                    url=self.config.SERVICE_URL,
                    context={"error": str(e)},
                )
            except requests.exceptions.HTTPError as http_error:
                status_code = http_error.response.status_code
                error_context = {"error": str(http_error)}
                
                if status_code == 401:
                    error = GrafanaAuthError(
                        message="Invalid Grafana credentials",
                        status_code=401,
                        context=error_context
                    )
                elif status_code == 404:
                    error = GrafanaNotFoundError(
                        message="Grafana resource not found",
                        resource_type="endpoint",
                        resource_id=self.config.SERVICE_URL,
                        context=error_context
                    )
                elif status_code == 409:
                    error = GrafanaConflictError(
                        message="Grafana resource conflict",
                        resource_type="endpoint",
                        conflict_reason=str(http_error),
                        context=error_context
                    )
                elif status_code == 422:
                    error = GrafanaValidationError(
                        message="Invalid Grafana request",
                        validation_errors=http_error.response.json().get("errors", {}),
                        context=error_context
                    )
                elif status_code == 429:
                    error = GrafanaRateLimitError(
                        message="Grafana rate limit exceeded",
                        limit=http_error.response.headers.get("X-RateLimit-Limit", 0),
                        remaining=http_error.response.headers.get("X-RateLimit-Remaining", 0),
                        reset_time=http_error.response.headers.get("X-RateLimit-Reset", ""),
                        context=error_context
                    )
                else:
                    error = GrafanaError(
                        ErrorDetail(
                            code="grafana_http_error",
                            message=f"Grafana HTTP error: {str(http_error)}",
                            context={
                                "status_code": status_code,
                                "url": self.config.SERVICE_URL
                            }
                        )
                    )
                
                error.log_error()
                raise error
            except Exception as e:
                error = GrafanaError(
                    ErrorDetail(
                        code="grafana_client_error",
                        message=f"Unexpected Grafana error: {str(e)}",
                        context={"url": self.config.SERVICE_URL, "error": str(e)},
                    )
                )
                error.log_error()
                raise error

    async def get_async_client(self):
        """Stub async client for testing (mocked in tests)"""
        pass

    def _create_session(self) -> requests.Session:
        """Configure a production-ready requests session"""
        session = requests.Session()

        # Configure TLS verification
        session.verify = self.config.SSL_CONFIG.get("verify", True)

        # Connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=self.config.POOL_CONNECTIONS,
            pool_maxsize=self.config.POOL_MAXSIZE,
            max_retries=self.config.MAX_RETRIES,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _log_retry_attempt(self, retry_state: RetryCallState) -> None:
        """Log retry attempts with context"""
        logger.warning(
            f"Retrying Grafana connection (attempt {retry_state.attempt_number}): "
            f"{str(retry_state.outcome.exception())}"
        )

    def __enter__(self) -> GrafanaApi:
        """Enter the runtime context"""
        return self.get_client()

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit the runtime context and clean up resources"""
        if self._session:
            self._session.close()
        return False  # Propagate exceptions
