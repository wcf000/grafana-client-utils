"""
Production metrics utilities for Grafana instrumentation.
- Provides Prometheus Gauge and Counter metrics for API response times and test results.
- Unified helpers for recording metrics on dashboards, alerts, and other Grafana operations.
- Uses type-safe label extraction from core models for DRY, maintainable code.
- Integrates with CI/CD, production monitoring, and test environments.

Best practices:
- Always provide all required label values when using metrics.
- Use helpers to record success/failure and timing for each operation.
- Use fixtures to reset metrics between tests to avoid cross-test contamination.
- Mock start_http_server in unit tests.
- Use unique metric names to avoid conflicts.

See _docs/alerts.md for more details.
"""

import logging
from typing import Union

from prometheus_client import Counter, Gauge

from app.core.grafana.alert_manager import AlertRule
from app.core.grafana.models.index import DashboardMeta, GrafanaDashboard
from app.core.prometheus.metrics import (
    PULSAR_CACHE_DELETES,
    PULSAR_CACHE_HITS,
    PULSAR_CACHE_MISSES,
    PULSAR_CACHE_SETS,
    CELERY_TASK_COUNT,
    CELERY_TASK_LATENCY,
    VALKEY_CACHE_HITS,
)

logger = logging.getLogger("grafana.metrics")

# --- Metric Definitions ---
API_RESPONSE_TIME = Gauge(
    "grafana_api_response_seconds",
    "API response time in seconds",
    [
        "operation",
        "status",
        "dashboard_uid",
        "dashboard_title",
        "alert_uid",
        "alert_title",
        "severity",
        "error",
    ],
)
TEST_SUCCESS = Counter(
    "test_success_total",
    "Total successful test executions",
    [
        "operation",
        "status",
        "dashboard_uid",
        "dashboard_title",
        "alert_uid",
        "alert_title",
        "severity",
    ],
)
TEST_FAILURE = Counter(
    "test_failure_total",
    "Total failed test executions",
    [
        "operation",
        "status",
        "dashboard_uid",
        "dashboard_title",
        "alert_uid",
        "alert_title",
        "severity",
        "error",
    ],
)


# --- Unified Metric Recording Helper ---
def record_grafana_metric(
    operation: str,
    model: GrafanaDashboard | DashboardMeta | AlertRule,
    status: str,
    duration: float,
    error: str | None,
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
        "dashboard_uid": getattr(model, "uid", ""),
        "dashboard_title": getattr(model, "title", ""),
        "alert_uid": getattr(model, "uid", "") if isinstance(model, AlertRule) else "",
        "alert_title": getattr(model, "title", "")
        if isinstance(model, AlertRule)
        else "",
        "severity": getattr(model, "severity", "")
        if hasattr(model, "severity")
        else "",
        "error": error or "",
    }
    # Remove empty labels for metrics that don't use them
    clean_labels = {k: v for k, v in labels.items() if v != ""}
    if error:
        TEST_FAILURE.labels(**clean_labels).inc()
    else:
        TEST_SUCCESS.labels(
            **{k: v for k, v in clean_labels.items() if k != "error"}
        ).inc()
    API_RESPONSE_TIME.labels(**clean_labels).set(duration)
    logger.info(
        f"Recorded metric for {operation} | status={status} | duration={duration:.3f}s | labels={clean_labels}"
    )


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


# Pulsar cache metric helpers
def record_pulsar_cache_hit():
    """Increment Pulsar cache hit metric"""
    PULSAR_CACHE_HITS.inc()


def record_pulsar_cache_miss():
    """Increment Pulsar cache miss metric"""
    PULSAR_CACHE_MISSES.inc()


def record_pulsar_cache_set():
    """Increment Pulsar cache set metric"""
    PULSAR_CACHE_SETS.inc()


def record_pulsar_cache_delete():
    """Increment Pulsar cache delete metric"""
    PULSAR_CACHE_DELETES.inc()


# Celery metric helpers
def record_celery_task_success(task_name: str) -> None:
    """Increment Celery task success counter"""
    CELERY_TASK_COUNT.labels(task_name=task_name, status="success").inc()


def record_celery_task_failure(task_name: str) -> None:
    """Increment Celery task failure counter"""
    CELERY_TASK_COUNT.labels(task_name=task_name, status="failure").inc()


def record_celery_task_latency(task_name: str, duration: float) -> None:
    """Observe Celery task execution duration"""
    CELERY_TASK_LATENCY.labels(task_name=task_name).observe(duration)


# Valkey cache metric helpers
def record_valkey_cache_hit() -> None:
    """Increment Valkey cache hit metric"""
    VALKEY_CACHE_HITS.inc()
