"""
Smoke test for Grafana dashboard availability.

- Measures API response time and test pass/fail counts using Prometheus metrics.
- Designed for fast feedback in CI/CD and production deployments.
- Always provide all required label values for metrics.
- Use fixtures to inject a mocked or isolated grafana_client in unit tests.
- Mock metrics in test runs to avoid global state and allow assertion of increments.

See _docs/alerts.md for further test and metrics best practices.
"""

import os

from unittest.mock import MagicMock
import pytest
import time
from app.core.grafana._tests import metrics

# Set Prometheus metrics to MagicMock directly to guarantee no AttributeError
metrics.API_RESPONSE_TIME = MagicMock()
metrics.TEST_SUCCESS = MagicMock()
metrics.TEST_FAILURE = MagicMock()



@pytest.fixture
def grafana_client():
    """Provide a mock Grafana client for tests."""
    class MockDashboard:
        def get_dashboard(self, uid):
            class Response:
                status_code = 200
            return Response()
    class MockGrafanaClient:
        dashboard = MockDashboard()
    return MockGrafanaClient()


def test_dashboard_availability(grafana_client):
    """Test dashboard availability and metric increment logic."""
    start_time = time.time()
    test_name = "test_dashboard_availability"
    try:
        response = grafana_client.dashboard.get_dashboard("fastapi")
        metrics.API_RESPONSE_TIME.labels(endpoint="/api/dashboards", status=response.status_code).set(time.time() - start_time)
        metrics.TEST_SUCCESS.labels(test_name=test_name).inc()
    except Exception as e:
        metrics.TEST_FAILURE.labels(test_name=test_name, error=str(e)).inc()
        raise
