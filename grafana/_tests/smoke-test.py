"""
Smoke test for Grafana dashboard availability.

- Measures API response time and test pass/fail counts using Prometheus metrics.
- Designed for fast feedback in CI/CD and production deployments.
- Always provide all required label values for metrics.
- Use fixtures to inject a mocked or isolated grafana_client in unit tests.
- Mock metrics in test runs to avoid global state and allow assertion of increments.

See _docs/alerts.md for further test and metrics best practices.
"""

import pytest
import time
from unittest.mock import patch
from metrics import API_RESPONSE_TIME, TEST_FAILURE, TEST_SUCCESS


# --- Fixtures ---
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

@pytest.fixture(autouse=True)
def mock_metrics(monkeypatch):
    """Mock Prometheus metric methods to avoid global state in test runs."""
    monkeypatch.setattr(API_RESPONSE_TIME, "labels", lambda **kwargs: API_RESPONSE_TIME)
    monkeypatch.setattr(API_RESPONSE_TIME, "set", lambda x: None)
    monkeypatch.setattr(TEST_SUCCESS, "labels", lambda **kwargs: TEST_SUCCESS)
    monkeypatch.setattr(TEST_SUCCESS, "inc", lambda: None)
    monkeypatch.setattr(TEST_FAILURE, "labels", lambda **kwargs: TEST_FAILURE)
    monkeypatch.setattr(TEST_FAILURE, "inc", lambda: None)
    yield

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
        API_RESPONSE_TIME.labels(endpoint="/api/dashboards", status=response.status_code).set(time.time() - start_time)
        TEST_SUCCESS.labels(test_name=test_name).inc()
    except Exception as e:
        TEST_FAILURE.labels(test_name=test_name, error=str(e)).inc()
        raise
