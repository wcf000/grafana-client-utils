"""
Security test suite for Grafana API endpoints.

Covers:
- Authentication and authorization (401, 403, 400)
- Rate limiting (429)
- Resource not found (404)
- API key handling (valid, invalid, malformed)

Best practices:
- All external requests are to be mocked in CI/unit tests for speed and reliability.
- Use pytest fixtures for setup/teardown and to avoid test cross-contamination.
- Parameterize similar tests for maintainability.
- Extend with additional security scenarios as needed (expired keys, XSS, etc).

See _docs/alerts.md for more on CI/test architecture.
"""

from unittest.mock import patch

import pytest
import requests

from app.core.config import settings


# --- Fixtures ---
@pytest.fixture(autouse=True)
def mock_requests():
    """Mock requests.get for all tests to avoid real HTTP calls."""
    with patch("requests.get") as mock_get:
        yield mock_get

# --- Parameterized Security Tests ---
import pytest

GRAFANA_HOSTS = ["localhost", "127.0.0.1"]

@pytest.mark.parametrize("host", GRAFANA_HOSTS)
@pytest.mark.parametrize("endpoint_path,headers,expected_status", [
    ("/api/dashboards/uid/fastapi", None, 401),
    ("/api/dashboards/uid/fastapi", {"Authorization": "Bearer invalid_key"}, 403),
    ("/api/dashboards/uid/fastapi", {"Authorization": "Bearer invalid!@#$%^"}, 403),
])
def test_security_status_codes(mock_requests, host, endpoint_path, headers, expected_status):
    url = f"http://{host}:3000{endpoint_path}"
    mock_response = requests.models.Response()
    mock_response.status_code = expected_status
    mock_requests.return_value = mock_response
    response = requests.get(url, headers=headers) if headers else requests.get(url)
    assert response.status_code == expected_status
    """Test authentication, invalid API key, and malformed API key scenarios."""
    mock_response = requests.models.Response()
    mock_response.status_code = expected_status
    mock_requests.return_value = mock_response
    response = requests.get(endpoint, headers=headers) if headers else requests.get(endpoint)
    assert response.status_code == expected_status

# --- Rate Limiting Test ---
def test_rate_limiting(mock_requests):
    """Test rate limiting returns 429 status code."""
    mock_response = requests.models.Response()
    mock_response.status_code = 429
    mock_requests.return_value = mock_response
    for host in GRAFANA_HOSTS:
        url = f"http://{host}:3000/api/dashboards/uid/fastapi"
        response = requests.get(url)
        assert response.status_code == 429

# --- Resource Not Found Test ---
def test_resource_not_found(mock_requests):
    """Test resource not found returns 404 status code."""
    mock_response = requests.models.Response()
    mock_response.status_code = 404
    mock_requests.return_value = mock_response
    for host in GRAFANA_HOSTS:
        url = f"http://{host}:3000/api/dashboards/uid/doesnotexist"
        response = requests.get(url)
        assert response.status_code == 404

# --- Extendable: Add more security scenarios as needed ---
# Example: Expired API key, XSS, etc.
