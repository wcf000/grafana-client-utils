# _tests/metrics.py
import os

from prometheus_client import Counter, Gauge, start_http_server

# Metrics definitions
API_RESPONSE_TIME = Gauge(
    "grafana_api_response_seconds",
    "API response time in seconds",
    ["endpoint", "status"],
)
TEST_SUCCESS = Counter(
    "test_success_total", "Total successful test executions", ["test_name"]
)
TEST_FAILURE = Counter(
    "test_failure_total", "Total failed test executions", ["test_name", "error"]
)


def start_metrics_server():
    """Start Prometheus metrics server"""
    start_http_server(int(os.getenv("METRICS_PORT", 8000)))
