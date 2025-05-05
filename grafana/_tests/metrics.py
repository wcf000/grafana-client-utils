import logging
import os
from typing import Optional, Union
from unittest.mock import patch

import pytest
from prometheus_client import Counter, Gauge, start_http_server

from app.core.grafana.alert_manager import AlertRule

from app.core.grafana.models import DashboardMeta, GrafanaDashboard

logger = logging.getLogger("grafana.metrics")

# Metrics definitions
API_RESPONSE_TIME = Gauge(
    "grafana_api_response_seconds",
    "API response time in seconds",
    ["operation", "status", "dashboard_uid", "dashboard_title", "alert_uid", "alert_title", "severity", "error"],
)
TEST_SUCCESS = Counter(
    "test_success_total", "Total successful test executions", ["operation", "status", "dashboard_uid", "dashboard_title", "alert_uid", "alert_title", "severity"]
)
TEST_FAILURE = Counter(
    "test_failure_total", "Total failed test executions", ["operation", "status", "dashboard_uid", "dashboard_title", "alert_uid", "alert_title", "severity", "error"]
)

# --- Optimized Metrics Utilities for Grafana ---
def record_grafana_metric(
    operation: str,
    model: Union[GrafanaDashboard, DashboardMeta, AlertRule],
    status: str,
    duration: float,
    error: Optional[str] = None,
) -> None:
    """
    Record Prometheus metrics for a Grafana operation using typed models for labels.

    Args:
        operation: The operation performed (e.g., 'dashboard_get', 'alert_create').
        model: The relevant Grafana model instance (dashboard, alert, etc.).
        status: The status/result (e.g., 'success', 'error', HTTP status).
        duration: Time taken for the operation in seconds.
        error: Optional error message for failures.
    """
    labels = {
        "operation": operation,
        "status": status,
    }
    # Extract model-specific labels
    if isinstance(model, GrafanaDashboard):
        labels.update({
            "dashboard_uid": getattr(model, "uid", "unknown"),
            "dashboard_title": getattr(model, "title", "unknown"),
        })
    elif isinstance(model, DashboardMeta):
        labels.update({
            "dashboard_uid": getattr(model, "uid", "unknown"),
            "dashboard_title": getattr(model, "title", "unknown"),
        })
    elif isinstance(model, AlertRule):
        labels.update({
            "alert_uid": getattr(model, "uid", "unknown"),
            "alert_title": getattr(model, "title", "unknown"),
            "severity": getattr(model, "severity", "unknown"),
        })
    if error:
        labels["error"] = error
        TEST_FAILURE.labels(**labels).inc()
    else:
        TEST_SUCCESS.labels(**labels).inc()
    API_RESPONSE_TIME.labels(**labels).set(duration)
    logger.info(f"Recorded metric for {operation} | status={status} | duration={duration:.3f}s | labels={labels}")


def handle_grafana_exception(operation: str, model: object, exc: Exception) -> None:
    """
    Standardized error handling: log exception and increment failure metric.
    """
    error_msg = str(exc)
    logger.error(f"Grafana operation '{operation}' failed: {error_msg}")
    record_grafana_metric(
        operation=operation,
        model=model,
        status="error",
        duration=0.0,
        error=error_msg,
    )

# --- Pytest Fixtures for Metric Reset ---
@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset Prometheus metrics between tests to avoid cross-test contamination."""
    API_RESPONSE_TIME._metrics.clear()
    TEST_SUCCESS._metrics.clear()
    TEST_FAILURE._metrics.clear()
    yield
    API_RESPONSE_TIME._metrics.clear()
    TEST_SUCCESS._metrics.clear()
    TEST_FAILURE._metrics.clear()

# --- Mock start_http_server for unit tests ---
@pytest.fixture(autouse=True)
def mock_start_http_server():
    with patch("prometheus_client.start_http_server") as mock_server:
        yield mock_server

def start_metrics_server():
    """Start Prometheus metrics server"""
    start_http_server(int(os.getenv("METRICS_PORT", 8000)))
