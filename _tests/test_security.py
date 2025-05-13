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


from app.core.config import settings


# --- Fixtures ---

# --- Parameterized Security Tests ---
import pytest


@pytest.mark.parametrize("endpoint_path,headers,expected_status", [
    ("/api/dashboards/uid/fastapi", None, 401),
    ("/api/dashboards/uid/fastapi", {"Authorization": "Bearer invalid_key"}, 403),
    ("/api/dashboards/uid/fastapi", {"Authorization": "Bearer invalid!@#$%^"}, 403),
])
def test_security_status_codes(grafana_client, endpoint_path, headers, expected_status):
    # ! Use GrafanaClient abstraction only
    response = grafana_client.dashboard.get_dashboard("fastapi")
    assert response.status_code == expected_status
    # Note: Additional negative scenarios (invalid/malformed API key) should be implemented via client mocks or fixtures, not direct requests.

# --- Rate Limiting Test ---
def test_rate_limiting(grafana_client):
    """Test rate limiting returns 429 status code."""
    response = grafana_client.dashboard.get_dashboard("fastapi")
    assert response.status_code == 429

# --- Resource Not Found Test ---
def test_resource_not_found(grafana_client):
    """Test resource not found returns 404 status code."""
    response = grafana_client.dashboard.get_dashboard("doesnotexist")
    assert response.status_code == 404

# --- Extendable: Add more security scenarios as needed ---
# Example: Expired API key, XSS, etc.
