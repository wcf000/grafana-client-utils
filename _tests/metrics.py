"""
metrics.py
Centralized Prometheus metric definitions for all Grafana-related tests.
Ensures no duplicated metrics in CollectorRegistry during pytest runs.
"""
from prometheus_client import Counter, Gauge, CollectorRegistry, REGISTRY

def get_metrics(registry=None):
    if registry is None:
        registry = REGISTRY
    if not hasattr(get_metrics, "_metrics"):
        get_metrics._metrics = {}
    if registry not in get_metrics._metrics:
        API_RESPONSE_TIME = Gauge(
            "grafana_api_response_seconds",
            "API response time in seconds",
            ["endpoint", "status"],
            registry=registry,
        )
        TEST_SUCCESS = Counter(
            "test_success_total",
            "Total successful test executions",
            ["test_name"],
            registry=registry,
        )
        TEST_FAILURE = Counter(
            "test_failure_total",
            "Total failed test executions",
            ["test_name", "error"],
            registry=registry,
        )
        get_metrics._metrics[registry] = (API_RESPONSE_TIME, TEST_SUCCESS, TEST_FAILURE)
    return get_metrics._metrics[registry]


